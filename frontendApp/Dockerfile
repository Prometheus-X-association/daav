# Build stage
FROM node:22-alpine AS build

WORKDIR /app

RUN apk add --no-cache python3 make g++

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build -- --configuration=docker

# Production stage
FROM nginx:alpine AS prod

COPY nginx.conf /etc/nginx/nginx.conf
COPY --from=build /app/www/browser /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

# Development stage
FROM node:22-alpine AS dev

WORKDIR /app

RUN apk add --no-cache python3 make g++

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 4200

CMD ["npm", "start"]
