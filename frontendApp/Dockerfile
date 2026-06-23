# Build stage
FROM node:22-alpine AS build

WORKDIR /app

RUN apk add --no-cache python3 make g++ git

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build -- --configuration=docker

# Production stage
FROM nginx:alpine AS prod

# envsubst is included in nginx:alpine via gettext package
RUN apk add --no-cache gettext

COPY nginx.conf /etc/nginx/nginx.conf.template
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh
COPY --from=build /app/www/ /usr/share/nginx/html

EXPOSE 80
ENTRYPOINT ["/docker-entrypoint.sh"]

# Development stage
FROM node:22-alpine AS dev

WORKDIR /app

RUN apk add --no-cache python3 make g++

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 4200

CMD ["npm", "start"]
