FROM servemeaswap.com:4000/reverse:latest

ARG domain
COPY sites/${domain}.conf /etc/nginx/conf.d/
