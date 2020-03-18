FROM python:3.8.2-alpine3.11

# Install Flask and Docker libraries for Python
RUN pip3 install flask docker

# Copy the app itself to the container
COPY swarm-deployer.py /opt/swarm-deployer/

# Change working dir
WORKDIR /opt/swarm-deployer

# Set name of the Flask App
ENV FLASK_APP=swarm-deployer.py

# Expose port
EXPOSE 5000

# Run Flask app
CMD python3 swarm-deployer.py
