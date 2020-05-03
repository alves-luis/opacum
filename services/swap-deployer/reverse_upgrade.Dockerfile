FROM alvesluis98/swap-deployer:reverse

ARG domain
COPY sites/${domain}.conf /etc/nginx/conf.d/
