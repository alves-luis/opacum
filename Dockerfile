FROM ubuntu:18.04

# Run without interactive dialogue
ENV DEBIAN_FRONTEND=noninteractive

# Install PHP
RUN apt-get update && apt-get install -y software-properties-common git zip unzip \
	&& add-apt-repository ppa:ondrej/php \
        && apt-get update \
	&& apt-get install -y php7.4 php7.4-zip php7.4-gd php7.4-bcmath php7.4-ctype php7.4-json php7.4-tokenizer php7.4-xml php7.4-xml php7.4-mbstring php7.4-intl php7.4-imagick php7.4-redis php7.4-pdo php7.4-pgsql

# Install NodeJS
RUN apt-get install -y curl && curl -sL https://deb.nodesource.com/setup_10.x | bash - \
	 && apt-get install -y nodejs

# Change to swap directory
WORKDIR /swap

# Install Composer
RUN php -r "copy('https://getcomposer.org/installer', 'composer-setup.php');" \
	&& php -r "if (hash_file('sha384', 'composer-setup.php') === 'e0012edf3e80b6978849f5eff0d4b4e4c79ff1609dd1e613307e16318854d24ae64f26d17af3ef0bf7cfb710ca74755a') { echo 'Installer verified'; } else { echo 'Installer corrupt'; unlink('composer-setup.php'); } echo PHP_EOL;" \
	&& php composer-setup.php \
	&& php -r "unlink('composer-setup.php');" 

# Install Composer packages
COPY swap/composer.json swap/composer.lock /swap/
RUN php composer.phar install --prefer-dist --no-scripts --no-autoloader && rm -rf /root/.composer

# Install Yarn
RUN curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add - \
  && echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list \
  && apt-get update && apt-get install yarn

# Install yarn dependencies
COPY swap/package.json swap/package-lock.json /swap/
RUN yarn install

# Copy repo
COPY swap /swap/

# Finish composer
RUN php composer.phar dump-autoload --no-scripts --optimize

# Generate application key
# This should run after building the container
RUN php artisan key:generate

# Build assets
RUN npm run prod

# Expose port
EXPOSE 8000

# Start local server
CMD ["php", "artisan", "serve", "--host=0.0.0.0"]
