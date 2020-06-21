#!/bin/bash
wait-for-it.sh $1:5432
cd /var/www/html/
php artisan key:generate
php artisan migrate --force
php artisan db:seed --force
apache2ctl -D FOREGROUND
