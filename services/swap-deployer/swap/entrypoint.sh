#!/bin/bash
#wait-for-it.sh $1-db:5432
wait-for-it.sh db:5432
cd /var/www/html/
php artisan key:generate
php artisan migrate
php artisan db:seed
#php artisan $1-db:seed
apache2ctl -D FOREGROUND
