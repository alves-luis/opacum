#!/bin/bash
wait-for-it.sh db:5432
cd /swap
php artisan key:generate
php artisan migrate
php artisan db:seed
php artisan serve --host=0.0.0.0
