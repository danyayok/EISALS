#!/bin/sh

CONF="/etc/nginx/conf.d/default.conf"
STARTUP="/etc/nginx/conf.d/startup.conf_source"
PROD="/etc/nginx/conf.d/default.conf_source"
CERT="/etc/letsencrypt/live/eisals.ru/fullchain.pem"

if [ ! -f "$CERT" ]; then
    echo "SSL не найден. Запуск STARTUP режима..."
    cp "$STARTUP" "$CONF"

    # Запуск в фоне
    nginx -g 'daemon off;' &

    # Ждем сертификат
    while [ ! -f "$CERT" ]; do
        sleep 5
    done

    echo "SSL получен. Переключаюсь на основной конфиг..."
    cp "$PROD" "$CONF"
    nginx -s reload
    # Оставляем процесс работать
    wait
else
    echo "SSL найден. Обычный запуск..."
    cp "$PROD" "$CONF"
    exec nginx -g 'daemon off;'
fi
