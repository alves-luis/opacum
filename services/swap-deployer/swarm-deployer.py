from flask import Flask, abort, request
import docker

app = Flask(__name__)

"""
Options for deployment (that go in the HTTP POST body)
* means it's mandatory
- mail_domain *
- admin *
    - email *
    - password *
- classes (csv file) *
- modules to be enabled (list)
"""
@app.route('/deploy/<subdomain>/', methods=['POST'])
def deploy(subdomain):
    if not request.json:
        abort(400, 'Not JSON encoded body')

    if not 'mail_domain' in request.json:
        abort(400, 'Missing mail_domain field in body')

    if not 'admin' in request.json and not 'email' in request.json['admin']:
        abort(400, 'Missing email field in admin fields in body')

    if not 'admin' in request.json and not 'password' in request.json['password']:
        abort(400, 'Missing password field in admin fields in body')
    #docker_client = docker.from_env()
    mail_domain = request.json['mail_domain']
    admin_mail = request.json['admin']['email']
    print(mail_domain)

    """
    net = create_network(docker_client, subdomain)
    postgres_service = setup_postgres_service(docker_client, subdomain)
    swap_service = setup_swap_service(docker_client, subdomain)

    services = docker_client.services.list()
    string_result = ""
    for service in services:
        string_result += service.name
    return string_result
    """
    return admin_mail

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
    service = client.services.create("swap:01", command=None,
        name=swap_name,
        networks=[network_name, "sms-net"])
    return service


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
