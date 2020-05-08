FROM ubuntu:18.04

# Run without interactive dialogue
ENV DEBIAN_FRONTEND=noninteractive

# Update
RUN apt-get update && apt-get install -y software-properties-common git zip unzip \
	&& add-apt-repository ppa:ondrej/php \
  && apt-get update \
	&& apt-get install -y php7.4 php7.4-zip php7.4-gd php7.4-bcmath php7.4-ctype php7.4-json php7.4-tokenizer php7.4-xml php7.4-xml php7.4-mbstring php7.4-intl php7.4-imagick php7.4-redis php7.4-pdo php7.4-pgsql

# Install Composer
COPY --from=composer:latest /usr/bin/composer /usr/bin/composer

# Install Composer dependencies
WORKDIR /var/www/html
COPY swap/composer.json swap/composer.lock /var/www/html/
RUN composer install --no-interaction --no-ansi --no-dev --no-plugins --no-scripts --no-autoloader && rm -rf /root/.composer

# Change ownership of vendor directory files
RUN usermod -u 1000 www-data && groupmod -g 1000 www-data
RUN chown -R www-data:www-data /var/www/html/

# Install NodeJS
RUN apt-get update && apt-get install -y curl
RUN curl -sL https://deb.nodesource.com/setup_10.x | bash -
RUN apt-get update && apt-get install -y nodejs

# Install npm dependencies
COPY swap/package.json swap/package-lock.json /var/www/html/
RUN npm install

# Change ownership of node_modules directory files
RUN chown -R www-data:www-data /var/www/html/node_modules/

# Install Apache web server
RUN apt-get update \
  && apt-get install -y apache2 apache2-utils \
  && apt-get clean

# Change web_root to laravel /var/www/html/public
COPY 000-default.conf /etc/apache2/sites-available/000-default.conf

# Define entrypoint
COPY entrypoint.sh /usr/local/bin/
COPY wait-for-it.sh /usr/local/bin/

# Copy repo
COPY swap /var/www/html

# Finish Composer and optimize
RUN composer dump-autoload --optimize

# Build assets
RUN npm run prod

# Change ownership of files
RUN chown -R www-data:www-data \ 
  /var/www/html/app \
  /var/www/html/bootstrap \
  /var/www/html/config \
  /var/www/html/database \
  /var/www/html/public \
  /var/www/html/resources \
  /var/www/html/routes \
  /var/www/html/storage \
  /var/www/html/tests
RUN chown www-data:www-data /var/www/html/*

# Enable Apache module rewrite
RUN a2enmod rewrite && service apache2 restart

# Expose 80 port
EXPOSE 80

# Temporarily set .env.example as .env
COPY .env /var/www/html/.env
ARG db_host
ARG db_host=feup-db
ENV DB_HOST=${db_host}
ENTRYPOINT entrypoint.sh ${DB_HOST}
