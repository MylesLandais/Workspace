# Docker Hosting for Gallery

## Quick Start

### 1. Build and Start

```bash
cd gallery
chmod +x docker-manage.sh
./docker-manage.sh build
./docker-manage.sh start
```

### 2. Access Gallery

Open: http://localhost:8001

### 3. Check Status

```bash
./docker-manage.sh status
```

## Docker Management Commands

### Build Image

```bash
./docker-manage.sh build
```

### Start Server

```bash
./docker-manage.sh start
```

### Stop Server

```bash
./docker-manage.sh stop
```

### Restart Server

```bash
./docker-manage.sh restart
```

### View Logs

```bash
./docker-manage.sh logs
```

### Test Connection

```bash
./docker-manage.sh test
```

### Clean Everything

```bash
./docker-manage.sh clean
```

## Port Configuration

### Current Configuration

Port: `8001` (exposed as `8001:8001`)

### Change Port

Edit `gallery/docker-compose.yml`:

```yaml
services:
  gallery:
    ports:
      - "8080:8001"  # Change left number to desired host port
```

Then restart:
```bash
./docker-manage.sh restart
```

Access at: http://localhost:8080

## Troubleshooting

### Port Already in Use

```bash
# Check what's using the port
sudo lsof -ti:8001

# Kill process
sudo kill -9 $(sudo lsof -ti:8001)

# Or use different port in docker-compose.yml
```

### Container Not Starting

```bash
# View logs
./docker-manage.sh logs

# Check container status
docker ps -a

# Inspect container
docker inspect gallery-server
```

### Health Check Failing

```bash
# Test health endpoint manually
curl http://localhost:8001/health

# Check if container is running
docker ps | grep gallery

# Restart container
./docker-manage.sh restart
```

### Permission Issues

```bash
# Fix cache directory permissions
sudo chown -R 1000:1000 gallery-cache/

# Or use host user ID
# Edit docker-compose.yml:
user: "${UID:-1000}:${GID:-1000}"
```

### Volume Mounting Issues

```bash
# Check volume exists
docker volume ls | grep gallery

# Inspect volume
docker volume inspect gallery_gallery-cache

# Remove and recreate volume
./docker-manage.sh clean
./docker-manage.sh start
```

## Debugging

### View Container Logs

```bash
# Follow logs
docker-compose -f gallery/docker-compose.yml logs -f

# Last 100 lines
docker-compose -f gallery/docker-compose.yml logs --tail=100

# Specific container
docker logs gallery-server
```

### Shell Into Container

```bash
docker exec -it gallery-server bash
```

### Check Network

```bash
# List networks
docker network ls

# Inspect network
docker network inspect gallery_gallery-network

# Test connectivity
docker exec gallery-server ping -c 3 8.8.8.8
```

### Check Port Binding

```bash
# List all port bindings
docker port gallery-server

# Check port availability
netstat -tuln | grep 8001
# or
ss -tuln | grep 8001
```

### Inspect Container

```bash
docker inspect gallery-server | python -m json.tool
```

## Common Issues

### "Connection Refused"

**Cause**: Container not running or port not exposed

**Fix**:
```bash
./docker-manage.sh status
./docker-manage.sh logs
./docker-manage.sh restart
```

### "Connection Reset"

**Cause**: Container crashing or port conflict

**Fix**:
```bash
# Check logs
./docker-manage.sh logs

# Restart
./docker-manage.sh restart

# If persistent, rebuild
./docker-manage.sh clean
./docker-manage.sh build
./docker-manage.sh start
```

### "404 Not Found"

**Cause**: Wrong URL or service not ready

**Fix**:
```bash
# Wait for service to start
sleep 10

# Test health endpoint
curl http://localhost:8001/health

# Check logs
./docker-manage.sh logs
```

### "Health Check Failed"

**Cause**: Service not responding to health checks

**Fix**:
```bash
# Check if service is running
curl http://localhost:8001/health

# Extend health check timeout
# Edit docker-compose.yml:
healthcheck:
  interval: 60s  # Increase from 30s
  timeout: 20s   # Increase from 10s

./docker-manage.sh restart
```

## Performance

### Resource Limits

Add to `docker-compose.yml`:

```yaml
services:
  gallery:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
```

### Build Optimization

Use multi-stage build for smaller image:

```dockerfile
# Build stage
FROM python:3.11-slim as builder
WORKDIR /app
COPY gallery/requirements.txt .
RUN pip install --user -r requirements.txt

# Runtime stage
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY gallery/ /app/gallery/
ENV PATH=/root/.local/bin:$PATH
CMD ["python", "gallery/start.py"]
```

## Monitoring

### Container Stats

```bash
docker stats gallery-server
```

### Disk Usage

```bash
# Container size
docker system df -v | grep gallery

# Volume size
du -sh gallery-cache/
```

## Production Deployment

### Use Environment File

```bash
# Create .env file
cat > gallery/.env << EOF
PORT=8001
HOST=0.0.0.0
CACHE_DIR=/app/cache
EOF
```

### Use Reverse Proxy (Nginx)

```nginx
server {
    listen 80;
    server_name gallery.example.com;

    location / {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Enable SSL

```bash
# Use Let's Encrypt with certbot
certbot --nginx -d gallery.example.com
```

## Backup and Restore

### Backup Volume

```bash
docker run --rm \
    -v gallery_gallery-cache:/data \
    -v $(pwd)/backup:/backup \
    alpine tar czf /backup/gallery-backup-$(date +%Y%m%d).tar.gz /data
```

### Restore Volume

```bash
docker run --rm \
    -v gallery_gallery-cache:/data \
    -v $(pwd)/backup:/backup \
    alpine tar xzf /backup/gallery-backup-YYYYMMDD.tar.gz -C /
```

## Testing

### Test Container

```bash
# Run interactively
docker run --rm -p 8001:8001 gallery-server

# Test with curl
curl http://localhost:8001/health
```

### Load Test

```bash
# Install wrk
apt-get install wrk

# Test performance
wrk -t4 -c100 -d30s http://localhost:8001/
```

## Security

### Scan Image

```bash
docker scan gallery-server
```

### Run as Non-Root

Edit `Dockerfile`:

```dockerfile
RUN useradd -m gallery
USER gallery
```

## Support

For issues:

1. Check logs: `./docker-manage.sh logs`
2. Test health: `curl http://localhost:8001/health`
3. Check documentation: `gallery/TROUBLESHOOTING.md`
4. Inspect container: `docker inspect gallery-server`
