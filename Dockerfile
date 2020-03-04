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

# Install npm dependencies
COPY swap/package.json swap/package-lock.json /swap/
RUN npm install

# Copy repo
COPY swap /swap/

# Finish composer
RUN php composer.phar dump-autoload --no-scripts --optimize

# Build assets
RUN npm run prod

# Define entrypoint
COPY entrypoint.sh /usr/local/bin/
COPY wait-for-it.sh /usr/local/bin/
ENTRYPOINT ["entrypoint.sh"]

# Expose port
EXPOSE 8000

