FROM registry.servemeaswap.com:5000/reverse:latest

ARG domain
RUN rm /etc/nginx/conf.d/${domain}.conf
