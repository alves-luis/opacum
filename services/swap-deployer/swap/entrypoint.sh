#!/bin/bash
wait-for-it.sh $1:5432
cd /var/www/html/
php artisan key:generate
php artisan migrate
php artisan db:seed
apache2ctl -D FOREGROUND
