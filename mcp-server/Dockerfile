FROM phpswoole/swoole:php8.3-alpine

WORKDIR /app
COPY composer.json ./
RUN composer install --no-dev --no-interaction --prefer-dist --optimize-autoloader
COPY src ./src
COPY server.php ./

EXPOSE 9501
CMD ["php", "server.php"]
