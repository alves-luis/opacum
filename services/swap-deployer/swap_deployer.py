from flask import Flask, abort, request
from jinja2 import Template
import docker

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
    swap_service = setup_swap_service(docker_client, subdomain)
    #setup reverse proxy TODO
    setup_reverse_proxy(docker_client, subdomain)
    return "Ok"

"""
Setup reverse-proxy configuration
"""
def setup_reverse_proxy(client, subdomain):
    # Should verify the subdomain here
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
    network_name = subdomain + "-net"
    net = client.networks.create(network_name, driver="overlay")
    return net

def setup_postgres_service(client, subdomain):
    postgres_name = subdomain + "-db"
    network_name = subdomain + "-net"
    envs = ["POSTGRES_USER=swapper", "POSTGRES_DB=swapper", "POSTGRES_PASSWORD=secret"]
    service = client.services.create("postgres:12", command=None,
        name=postgres_name,
        networks=[network_name],
        env=envs)
    return service

def setup_swap_service(client, subdomain):
    swap_name = subdomain + "-app"
    network_name = subdomain + "-net"
    image = client.images.build(dockerfile="Dockerfile",
        path="./swap",
        tag=f"alvesluis98/swap-deployer:{subdomain}-swap",
        buildargs={ "db_host": f"{subdomain}-db" })
    client.login(username='alvesluis98', password='secret') # should be stored in secret
    client.images.push(f'alvesluis98/swap-deployer:{subdomain}-swap')
    service = client.services.create(f"alvesluis98/swap-deployer:{subdomain}-swap", command=None,
        name=swap_name,
        networks=[network_name, "sms-net"]
    )
    return service


if __name__ == '__main__':
    application.run(debug=True, host='0.0.0.0')
