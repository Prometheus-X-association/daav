#!/bin/sh
set -e

# Backend URL proxied on /api/ (without trailing slash)
export API_URL="${API_URL:-http://backend:8000}"

# Inject CORS_ORIGIN and API_URL into nginx config at container startup (no rebuild needed)
# Only these variables are substituted — nginx's own $variables are left untouched
envsubst '${CORS_ORIGIN} ${API_URL}' < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf

exec nginx -g 'daemon off;'
