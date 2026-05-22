#!/bin/sh
set -e

# Inject CORS_ORIGIN into nginx config at container startup (no rebuild needed)
# Only ${CORS_ORIGIN} is substituted — nginx's own $variables are left untouched
envsubst '${CORS_ORIGIN}' < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf

exec nginx -g 'daemon off;'
