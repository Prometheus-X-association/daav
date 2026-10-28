# DAAV - Docker Deployment Guide

Advanced Docker configuration and troubleshooting guide for DAAV.

> 💡 **For quick start**, see the Docker section in [README.md](README.md)

## Advanced Configuration

### Backend
The backend uses environment variables defined in docker-compose.yml.
To customize, you can:
1. Edit the `environment:` section of the `backend` service in `docker-compose.yml` (these values take precedence)
2. Or create a `.env` file in the `backendApi/` folder (copy and modify `.env.example`) for variables not set in `docker-compose.yml` (SMTP, ...) — it is loaded at runtime through the optional `env_file` entry (it is not copied into the image), so `docker-compose up -d backend` is enough to apply changes

The backend image runs on `python:3.13-slim` with Gunicorn and `WORKERS` Uvicorn workers (default 4).

**Before deploying to production**, change at least:
- Set `JWT_SECRET_KEY` and `FIELD_ENCRYPTION_KEY`: they have no default value. If they are missing, temporary keys are generated in the `backend-secrets` volume and an error is logged at every start. Copy them with `docker compose exec backend cat /app/secrets/JWT_SECRET_KEY_TMP /app/secrets/FIELD_ENCRYPTION_KEY_TMP`, set them in `backendApi/.env` or `docker-compose.yml` and save them in a secrets vault — losing `FIELD_ENCRYPTION_KEY` makes the stored dataset credentials unreadable (see [SECURITY.md](docs/SECURITY.md#application-secrets))
- MongoDB credentials (`MONGO_INITDB_ROOT_*` and `MONGODB_URL`, plus Mongo Express settings if used)
- `CORS_ORIGINS` (backend) and `CORS_ORIGIN` (frontend) to your public domain
- `FRONTEND_URL` and the `SMTP_*` variables if password reset by email is needed
- The default application admin password (`admin` / `Admin123!`): the UI requires changing it at first login, do it before exposing the application

### Frontend
The frontend uses different environment configurations:
- **Development**: `environment.ts` → `http://127.0.0.1:8000`
- **Production**: `environment.prod.ts` → `https://daav-back.ptx.profenpoche.com`  
- **Docker**: `environment.docker.ts` → `/api` (proxied through Nginx, built with `--configuration=docker`)

**Important**: When deployed with Docker Compose, the frontend uses Nginx as a reverse proxy to communicate with the backend. This solves the issue where external users cannot access `localhost:8081` from their browsers.

#### How it works:
1. User accesses: `http://your-server:8080`
2. Angular makes API calls to: `/api/...`
3. Nginx proxies these calls to: `http://backend:8000/...`
4. Backend responds through the proxy back to the user

To customize the Nginx configuration, modify `frontendApp/nginx.conf` (it is used as a template: `docker-entrypoint.sh` substitutes `${CORS_ORIGIN}` and `${API_URL}` into it at startup), then rebuild the frontend image.

The backend proxied on `/api/` is set by the `API_URL` environment variable of the `frontend` service (default `http://backend:8000`, without trailing slash); changing it only requires recreating the container.

Upload limits: Nginx accepts request bodies up to 1000 MB on `/api/` (100 MB elsewhere); the backend then enforces `MAX_FILE_SIZE` per file (default 100 MB) and rejects requests larger than 10 × `MAX_FILE_SIZE`.

#### CORS configuration
The allowed origin is injected at container startup via the `CORS_ORIGIN` environment variable in `docker-compose.yml`. No rebuild is needed to change it:

```yaml
# docker-compose.yml — frontend service
environment:
  CORS_ORIGIN: "https://your-production-domain.com"
```

For local development with Docker the default value `http://localhost:8080` is already set.

The backend has its own CORS whitelist, set by `CORS_ORIGINS` (comma-separated) on the `backend` service. When the frontend is served through the Nginx proxy, API calls are same-origin; update `CORS_ORIGINS` only if browsers call the backend directly (port 8081).

## Persistent volumes

- **mongodb-data**: MongoDB data
- **mongodb-config**: MongoDB configuration
- **backend-uploads**: Uploaded files
- **backend-logs**: Application logs
- **backend-secrets**: Temporary keys generated when `JWT_SECRET_KEY` / `FIELD_ENCRYPTION_KEY` are not set (deleted by `docker compose down -v`)

### Migrating a legacy `config.ini`

`config.ini` files are not copied into the image (they contain credentials). To migrate a legacy `backendApi/app/config.ini` into MongoDB, copy it into the running container and restart the backend; it is renamed to `config.ini.backup` once migrated:

```bash
docker compose cp backendApi/app/config.ini backend:/app/app/config.ini
docker compose restart backend
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Port Already in Use
```bash
# Check which process is using a port
netstat -tulpn | grep :8080
lsof -i :8080

# Kill the process using the port
sudo kill -9 <PID>
```

#### 2. MongoDB Connection Issues
```bash
# Check MongoDB status
docker-compose exec mongodb mongosh --eval "db.adminCommand('ping')"

# Test authentication
docker-compose exec mongodb mongosh -u admin -p admin123 --authenticationDatabase admin

# Check MongoDB logs
docker-compose logs mongodb
```

#### 3. Backend Issues
```bash
# Check backend health
curl http://localhost:8081/health

# Check backend logs for errors
docker-compose logs -f backend

# Test backend connectivity from frontend container
docker-compose exec frontend wget -qO- http://backend:8000/health
```

#### 4. Frontend Build/Access Issues
```bash
# Check if frontend is serving files correctly
curl -I http://localhost:8080

# Check nginx configuration
docker-compose exec frontend nginx -t

# Check nginx access logs
docker-compose logs frontend | grep "GET /"
```

#### 5. File Upload Issues (413 Request Entity Too Large)
```bash
# Check nginx configuration for file size limits
docker-compose exec frontend grep -r "client_max_body_size" /etc/nginx/

# Verify backend file size configuration
docker-compose logs backend | grep "MAX_FILE_SIZE"
```

#### 6. External Access Issues
If users can't access the application from outside the Docker host:

```bash
# Test API proxy from external machine
curl http://your-server-ip:8080/api/health

# Check if containers are bound to all interfaces
docker-compose ps

# Verify nginx proxy configuration
docker-compose exec frontend cat /etc/nginx/nginx.conf
```

### Build Issues

#### Clean build process
```bash
# Stop all services
docker-compose down

# Remove images
docker-compose down --rmi all

# Clean build cache
docker system prune -a

# Rebuild from scratch
docker-compose build --no-cache
docker-compose up -d
```

#### Dependency issues
```bash
# Check if requirements.txt is up to date
docker-compose exec backend pip list

# The production frontend image only contains Nginx and the built app (no npm).
# Rebuild it without cache to reinstall package.json dependencies
docker-compose build --no-cache frontend
```

### Performance Issues

#### Monitor resource usage
```bash
# Check container resource usage
docker stats

# Check logs for memory/CPU issues
docker-compose logs backend | grep -E "(memory|CPU|performance)"
```

#### Scale backend workers
```bash
# Increase workers in docker-compose.yml
WORKERS: 8  # Increase from default 4

# Recreate backend service to apply the new environment
docker-compose up -d backend
```

> Note: the security middleware rate limit (`SECURITY_RATE_LIMIT`) is kept in memory per worker.

### Data Recovery

#### Backup and restore
```bash
# Backup MongoDB data
docker-compose exec mongodb mongodump --out /data/backup --authenticationDatabase admin -u admin -p admin123

# Backup volumes
docker run --rm -v daav_mongodb-data:/data -v $(pwd):/backup alpine tar czf /backup/mongodb-backup.tar.gz /data

# Restore from backup
docker run --rm -v daav_mongodb-data:/data -v $(pwd):/backup alpine tar xzf /backup/mongodb-backup.tar.gz -C /
```

## Important Notes

1. **Security**: Default passwords and secrets should be changed in production (see [Advanced Configuration](#advanced-configuration))
2. **Persistence**: Docker volumes persist data between restarts
3. **Network**: All services communicate via the `daav` Docker network; MongoDB is not published on the host
4. **Monitoring**: The backend exposes `GET /health`, used by the container health check

## 📖 Navigation

- [← Back to main project](README.md)
- [Technical overview](docs/OVERVIEW.md)
- [Plugin development guide](docs/PLUGGINS.md)
- [Security guide](docs/SECURITY.md)
