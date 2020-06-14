FROM registry.servemeaswap.com:5000/reverse:latest

ARG domain
COPY sites/${domain}.conf /etc/nginx/conf.d/
