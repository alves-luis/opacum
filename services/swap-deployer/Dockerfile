FROM python:3.8.2-alpine3.11

# Install Flask, Docker, Gunicorn and Jinja2 libraries for Python
RUN pip3 install flask docker gunicorn jinja2

# Copy the swap base files to the container
COPY swap /opt/swap-deployer/swap

# Copy the app itself and templates to the container
COPY swap_deployer.py nginx_template.j2 CoursesTableSeeder_template.j2 env.j2 reverse_upgrade.Dockerfile /opt/swap-deployer/

# Change working dir
WORKDIR /opt/swap-deployer

# Create directory for config files
RUN mkdir /opt/swap-deployer/sites

# Expose port
EXPOSE 5000

# Run Flask app
CMD gunicorn --chdir /opt/swap-deployer swap_deployer -w 2 --threads 2 -b 0.0.0.0:5000
