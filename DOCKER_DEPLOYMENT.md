# DAAV - Docker Deployment Guide

Advanced Docker configuration and troubleshooting guide for DAAV.

> 💡 **For quick start**, see the Docker section in [README.md](README.md)

## Advanced Configuration

### Backend
The backend uses environment variables defined in docker-compose.yml.
To customize, you can:
1. Create a `.env` file in the `backendApi/` folder
2. Copy and modify `.env.example`

### Frontend
The frontend uses different environment configurations:
- **Development**: `environment.ts` → `http://127.0.0.1:8000`
- **Production**: `environment.prod.ts` → `https://daav-back.ptx.profenpoche.com`  
- **Docker**: `environment.docker.ts` → `/api` (proxied through Nginx)

**Important**: When deployed with Docker Compose, the frontend uses Nginx as a reverse proxy to communicate with the backend. This solves the issue where external users cannot access `localhost:8081` from their browsers.

#### How it works:
1. User accesses: `http://your-server:8080`
2. Angular makes API calls to: `/api/...`
3. Nginx proxies these calls to: `http://backend:8000/...`
4. Backend responds through the proxy back to the user

To customize the Nginx configuration, modify `frontendApp/nginx.conf`.

#### CORS configuration
The allowed origin is injected at container startup via the `CORS_ORIGIN` environment variable in `docker-compose.yml`. No rebuild is needed to change it:

```yaml
# docker-compose.yml — frontend service
environment:
  CORS_ORIGIN: "https://your-production-domain.com"
```

For local development with Docker the default value `http://localhost:8080` is already set.

## Persistent volumes

- **mongodb-data**: MongoDB data
- **mongodb-config**: MongoDB configuration
- **backend-uploads**: Uploaded files
- **backend-logs**: Application logs

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
docker-compose exec frontend curl http://backend:8000/health
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

# Check if package.json dependencies are installed
docker-compose exec frontend npm list
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

# Restart backend service
docker-compose restart backend
```

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

1. **Security**: Default passwords should be changed in production
2. **Persistence**: Docker volumes persist data between restarts
3. **Network**: All services communicate via the `daav` Docker network
4. **Monitoring**: The backend includes a health check to verify its status

## 📖 Navigation

- [← Back to main project](README.md)
- [Technical overview](docs/OVERVIEW.md)
- [Plugin development guide](docs/PLUGGINS.md)
