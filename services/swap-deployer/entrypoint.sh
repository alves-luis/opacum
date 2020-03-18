#!/bin/bash
#wait-for-it.sh $1-db:5432
cd /var/www/html/
php artisan key:generate
#php artisan migrate
apachectl -DFOREGROUND
#php artisan $1-db:seed
