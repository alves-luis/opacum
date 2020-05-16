FROM servemeaswap.com:4000/reverse:latest

ARG domain
RUN rm /etc/nginx/conf.d/${domain}.conf
