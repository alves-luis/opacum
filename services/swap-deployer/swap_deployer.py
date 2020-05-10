import re
from logging.config import dictConfig

import docker
from flask import Flask, abort, request
from jinja2 import Template

import os

"""
Parameters
"""
REGISTRY_USERNAME = "admin"
REGISTRY_PASSWORD = open("/run/secrets/registry_password").read()
REGISTRY_URL = "servemeaswap.com:4000"
DEFAULT_DOCKER_NETWORK = "sms-net"
POSTGRES_USER = "swapper"
POSTGRES_DATABASE = "swapper"
POSTGRES_PASSWORD = "secret"

"""
Logging configuration
"""
dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] [%(levelname)s]: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})

application = Flask(__name__)


"""
Validates that the request has all the necessary parameters
"""
def validate_deploy_request():
    if not request.json:
        abort(400, 'Not JSON encoded body')

    request_dict = {}

    mandatory_fields = [ "key", "mail_domain", "admin", "courses" ]

    for field in mandatory_fields:
        if not field in request.json:
            application.logger.info(f"Request with path {request.full_path} was missing {field} field")
            abort(400, f'Missing {field} in body')
    
    if request.json['key'] != open("/run/secrets/mabeei_key").read():
        application.logger.warning(f"Someone tried to use this API using this invalid key: {request.json['key']}")
        abort(401, 'Invalid authentication key!')

    request_dict['mail_domain'] = request.json['mail_domain']

    admin_fields = [ "email", "password" ]
    request_dict['admin'] = {}

    for admin_field in admin_fields:
        if not admin_field in request.json['admin']:
            application.logger.info(f"Request with path {request.full_path} was missing {admin_field} field in Admin")
            abort(400, f'Missing {admin_field} in Admin')
        else:
            request_dict['admin'][admin_field] = request.json['admin'][admin_field]

    course_fields = [ "code", "name", "semester", "year" ]

    request_dict['courses'] = []
    
    for course in request.json['courses']:
        for course_field in course_fields:
            if not course_field in course.keys():
                application.logger.info(f"Request with path {request.full_path} was missing {course_field} field in Course")
                abort(400, f'Missing {course_field} in course')
        request_dict['courses'].append(course)

    return request_dict

@application.route('/deploy/<subdomain>/', methods=['POST'])
def deploy(subdomain):
    deployment_dict = validate_deploy_request()
    docker_client = docker.from_env()

    network = create_network(docker_client, subdomain)
    postgres_service = setup_postgres_service(docker_client, subdomain)
    swap_service = setup_swap_service(docker_client, subdomain, deployment_dict)
    setup_reverse_proxy(docker_client, subdomain)
    return "Ok"

"""
Setup reverse-proxy configuration
"""
def setup_reverse_proxy(client, subdomain):
    nginx_template = Template(open('nginx_template.j2', 'r').read()).render(subdomain=subdomain)
    file = open(f"./sites/{subdomain}.conf", 'w')
    print(nginx_template, file=file)
    file.close()
    image = client.images.build(dockerfile="reverse_upgrade.Dockerfile",
        path=".",
        buildargs={ "domain": subdomain },
        tag=f"{REGISTRY_URL}/reverse:latest")
    client.login(username=REGISTRY_USERNAME, password=REGISTRY_PASSWORD, registry=REGISTRY_URL)
    client.images.push(f"{REGISTRY_URL}/reverse:latest")
    services = client.services.list(filters={'name': 'reverse-proxy'})
    rp_id = services.pop().id
    rp_service = client.services.get(rp_id)
    #rp_service.update(image=f"{REGISTRY_URL}/reverse:latest")
    rp_service.force_update()

"""
Create a new network, given a subdomain
"""
def create_network(client, subdomain):
    network_name = net_name(subdomain)
    try:
        net = client.networks.create(network_name, driver="overlay")
    except docker.errors.APIError as e:
        if e.response.status_code == 409:
            application.logger.info(f"Request with path {request.full_path} tried to create a network that already exists ({network_name}")
            abort(409, f"Subdomain is already in use")
        elif e.response.status_code == 500:
            application.logger.error(f"Error 500 when creating network {subdomain}: {e.response.message}")
            abort(503, f"Something went wrong when deploying your Swap")
    return net

"""
Setup database configuration
"""
def setup_postgres_service(client, subdomain):
    postgres_name = db_name(subdomain)
    network_name = net_name(subdomain)
    volume_name = vol_name(subdomain)
    client.volumes.create(name=volume_name, driver='local')
    envs = [f"POSTGRES_USER={POSTGRES_USER}", f"POSTGRES_DB={POSTGRES_DATABASE}", f"POSTGRES_PASSWORD={POSTGRES_PASSWORD}"]
    service = client.services.create("postgres:12", command=None,
        name=postgres_name,
        networks=[network_name],
        env=envs,
        constraints=["node.labels.db == true"],
        mounts=[f"{volume_name}:/var/lib/postgresql/data:rw"])
    return service

"""
Setup Swap configuration
"""
def setup_swap_service(client, subdomain, config):
    swap_name = app_name(subdomain)
    network_name = net_name(subdomain)
    setup_courses(config)
    setup_admin_credentials(config)
    image = client.images.build(dockerfile="Dockerfile",
        path="./swap",
        tag=f"{REGISTRY_URL}/swaps:{image_name(subdomain)}",
        buildargs={ "db_host": db_name(subdomain) })
    client.login(username=REGISTRY_USERNAME, password=REGISTRY_PASSWORD, registry=REGISTRY_URL)
    client.images.push(f"{REGISTRY_URL}/swaps:{image_name(subdomain)}")
    service = client.services.create(f"{REGISTRY_URL}/swaps:{image_name(subdomain)}", command=None,
        name=swap_name,
        networks=[network_name, DEFAULT_DOCKER_NETWORK]
    )
    return service

"""
Setup courses in the Swap image to be built
"""
def setup_courses(config):
    courses = config.get('courses')
    for course in courses:
        if not valid_course(course):
            return "Invalid Course"
    
    template = Template(open('CoursesTableSeeder_template.j2', 'r').read()).render(courses=courses)
    file = open(f"./swap/swap/database/seeds/CoursesTableSeeder.php", 'w')
    print(template, file=file)
    file.close()

"""
Setup admin credentials
"""
def setup_admin_credentials(config):
    admin = config.get('admin')
    email = admin['email']
    password = admin['password']
    template = Template(open("env.j2", "r").read()).render(db_name=POSTGRES_DATABASE, db_username=POSTGRES_USER, db_password=POSTGRES_PASSWORD,
        admin_mail=email, admin_pass=password)
    file = open(f"./swap/.env", "w")
    print(template, file=file)
    return (email, password)


"""
Given a course, validates its fields ["code", "name", "semester", "year"]
"""
def valid_course(course):
    return valid_course_code(course["code"]) and valid_course_name(course['name']) and valid_course_semester(course['semester']) and valid_course_year(course['year'])

def valid_course_code(code):
    return bool(re.match(r"^[\w0-9]+$", code))

def valid_course_name(name):
    return bool(re.match(r"^[\w ]+$", name))

def valid_course_semester(semester):
    return isinstance(semester, int) and semester >= 0

def valid_course_year(year):
    return isinstance(year, int) and year >= 0

"""
Given a subdomain, returns the name that the Swap Network should have
"""
def net_name(subdomain):
    return f"{subdomain}-net"

"""
Given a subdomain, returns the name that the Swap service should have
"""
def app_name(subdomain):
    return f"{subdomain}-app"

"""
Given a subdomain, returns the name that the Swap Database should have
"""
def db_name(subdomain):
    return f"{subdomain}-db"

"""
Given a subdomain, returns the name of the image that should be stored in the image registry
"""
def image_name(subdomain):
    return f"{subdomain}"

"""
Given a subdomain, returns the name of the volume that should be attached to that DB
"""
def vol_name(subdomain):
    return f"{subdomain}-vol"

if __name__ == '__main__':
    application.run(debug=True, host='0.0.0.0')
