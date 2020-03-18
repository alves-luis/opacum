from flask import Flask
from flask import request
import docker

app = Flask(__name__)

@app.route('/deploy/<subdomain>/', methods=['POST'])
def deploy(subdomain):
    client = docker.from_env()
    net = create_network(client, subdomain)
    postgres_service = setup_postgres_service(client, subdomain)
    swap_service = setup_swap_service(client, subdomain)

    services = client.services.list()
    string_result = ""
    for service in services:
        string_result += service.name
    return string_result

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
