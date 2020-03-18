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

# Install NodeJS
RUN apt-get install -y curl && curl -sL https://deb.nodesource.com/setup_10.x | bash - \
	 && apt-get install -y nodejs

# Install Composer dependencies
WORKDIR /var/www/html
COPY swap/composer.json swap/composer.lock /var/www/html/
RUN composer install --no-interaction --no-ansi --no-dev --no-plugins --no-scripts --no-autoloader && rm -rf /root/.composer

# Install npm dependencies
COPY swap/package.json swap/package-lock.json /var/www/html/
RUN npm install

# Copy repo
COPY swap /var/www/html

# Finish Composer and optimize
RUN composer dump-autoload --optimize

# Build assets
RUN npm run prod

# Install Apache web server
RUN apt-get update && apt-get install -y apache2

# Change web_root to laravel /var/www/html/public
RUN sed -i -e "s/html/html\/public/g" /etc/apache2/sites-enabled/000-default.conf

# Enable Apache module rewrite
RUN a2enmod rewrite && service apache2 restart

# Change ownership of files
RUN usermod -u 1000 www-data && groupmod -g 1000 www-data
RUN chown -R www-data:www-data /var/www/html

# Expose 80 port
EXPOSE 80

# Define entrypoint
COPY entrypoint.sh /usr/local/bin/
COPY wait-for-it.sh /usr/local/bin/
# Temporarily set .env.example as .env
COPY .env /var/www/html/.env
ENTRYPOINT [ "entrypoint.sh" ]
