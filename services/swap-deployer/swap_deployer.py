from flask import Flask, abort, request
from jinja2 import Template
import docker
import re

"""
Parameters
"""
REGISTRY_USERNAME = "alvesluis98"
REGISTRY_PASSWORD = ""
REGISTRY_URL = "alvesluis98/swap-deployer"
DEFAULT_DOCKER_NETWORK = "sms-net"

application = Flask(__name__)

def validate_deploy_request():
    if not request.json:
        abort(400, 'Not JSON encoded body')
    
    mandatory_fields = { 
        "mail_domain": [],
        "admin": [ "email", "password" ],
        "courses": [],
    }

    course_fields = [ "code", "name", "semester", "year" ]

    request_dict = {}

    for field, sub_fields in mandatory_fields.items():
        field_value = []
        if not field in request.json:
            abort(400, f'Missing {field} in body')
        for sub_field in sub_fields:
            if not sub_field in request.json[field]:
                abort(400, f'Missing {sub_field} in {field} fields in body')
            else:
                value = { sub_field: request.json[field][sub_field]}
                field_value.append(value)
        if not field_value:
            request_dict[field] = request.json[field]
        else:
            request_dict[field] = field_value
    
    for course in request.json['courses']:
        for course_field in course_fields:
            if not course_field in course.keys():
                abort(400, f'Missing {course_field} in course')

    return request_dict

@application.route('/deploy/<subdomain>/', methods=['POST'])
def deploy(subdomain):
    deployment_dict = validate_deploy_request()
    docker_client = docker.from_env()

    net = create_network(docker_client, subdomain)
    postgres_service = setup_postgres_service(docker_client, subdomain)
    swap_service = setup_swap_service(docker_client, subdomain, deployment_dict)
    setup_reverse_proxy(docker_client, subdomain)
    return "Ok"

"""
Setup reverse-proxy configuration
"""
def setup_reverse_proxy(client, subdomain):
    nginx_template = Template(open('nginx_template.j2', 'r').read()).render(subdomain=subdomain)
    file = open(f"/opt/swap-deployer/sites/{subdomain}.conf", 'w')
    print(nginx_template, file=file)
    services = client.services.list(filters={'name': 'reverse-proxy'})
    rp_id = services.pop().id
    rp_service = client.services.get(rp_id)
    rp_service.force_update()

"""
Create a new network, given a subdomain
"""
def create_network(client, subdomain):
    network_name = net_name(subdomain)
    net = client.networks.create(network_name, driver="overlay")
    return net

"""
Setup database configuration
"""
def setup_postgres_service(client, subdomain):
    postgres_name = db_name(subdomain)
    network_name = net_name(subdomain)
    envs = ["POSTGRES_USER=swapper", "POSTGRES_DB=swapper", "POSTGRES_PASSWORD=secret"]
    service = client.services.create("postgres:12", command=None,
        name=postgres_name,
        networks=[network_name],
        env=envs)
    return service

"""
Setup Swap configuration
"""
def setup_swap_service(client, subdomain, config):
    swap_name = app_name(subdomain)
    network_name = net_name(subdomain)
    setup_courses(config)
    image = client.images.build(dockerfile="Dockerfile",
        path="./swap",
        tag=f"{REGISTRY_URL}:{image_name(subdomain)}",
        buildargs={ "db_host": db_name(subdomain) })
    client.login(username=REGISTRY_USERNAME, password=REGISTRY_PASSWORD)
    client.images.push(f"{REGISTRY_URL}:{image_name(subdomain)}")
    service = client.services.create(f"{REGISTRY_URL}:{image_name(subdomain)}", command=None,
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


"""
Given a course, validates its fields ["code", "name", "semester", "year"]
"""
def valid_course(course):
    valid_course_code(course["code"])

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
    return f"{subdomain}-swap"

if __name__ == '__main__':
    application.run(debug=True, host='0.0.0.0')
