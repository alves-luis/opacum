FROM python:3.8.2-alpine3.11

# Install Flask, Docker and Gunicorn libraries for Python
RUN pip3 install flask docker gunicorn

# Copy the swap base files to the container
COPY swap /swap-deployer/swap

# Copy the app itself to the container
COPY swap_deployer.py /swap-deployer/

# Change working dir
WORKDIR /swap-deployer

# Expose port
EXPOSE 5000

# Run Flask app
CMD gunicorn --chdir /swap-deployer swap_deployer -w 2 --threads 2 -b 0.0.0.0:5000
