# Security Dashboard - Production Deployment Guide

This guide covers deploying the Security Dashboard with Gunicorn and Docker for production use.

## 🚀 Quick Start

### Option 1: Local Development with Gunicorn

1. **Install dependencies and run:**
   ```bash
   ./start_gunicorn.sh
   ```

### Option 2: Docker (Recommended for Production)

1. **Build and run with Docker:**
   ```bash
   docker build -t security-dashboard .
   docker run -p 5000:5000 --env-file .env security-dashboard
   ```

2. **Or use Docker Compose (includes MySQL):**
   ```bash
   docker-compose up -d
   ```

## 📋 Prerequisites

- Python 3.11+
- MySQL 8.0+ (or use Docker Compose)
- Docker & Docker Compose (for containerized deployment)

## ⚙️ Configuration

### Environment Variables

Create a `.env` file or use environment variables:

```bash
# Database
DB_HOST=localhost
DB_USER=dashboard
DB_PASSWORD=your-secure-password
DB_NAME=security_dashboard

# Flask
FLASK_SECRET_KEY=your-32-char-secret-key
FLASK_ENV=production
PORT=5000

# Security
CORS_ORIGINS=yourdomain.com,localhost
```

### Gunicorn Configuration

The app uses `gunicorn.conf.py` with production-ready settings:
- Multi-worker support (CPU cores × 2 + 1)
- Request limits and timeouts
- Proper logging
- Security settings

## 🐳 Docker Deployment

### Single Container
```bash
# Build the image
docker build -t security-dashboard .

# Run the container
docker run -d \
  --name security-dashboard \
  -p 5000:5000 \
  --env-file .env \
  security-dashboard
```

### With Docker Compose (Full Stack)
```bash
# Start all services (app + MySQL)
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

## 🔧 Local Development

### Manual Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run with Gunicorn
gunicorn --config gunicorn.conf.py flaskkk:app
```

### Using the Startup Script
```bash
# Make executable and run
chmod +x start_gunicorn.sh
./start_gunicorn.sh
```

## 📊 Monitoring & Health Checks

### Health Check Endpoint
```bash
curl http://localhost:5000/api/ping
```

### Application Logs
```bash
# Docker
docker logs security-dashboard

# Docker Compose
docker-compose logs app

# Local
tail -f app.log
```

## 🔒 Security Features

- Non-root user in Docker container
- Environment variable configuration
- Rate limiting built-in
- CORS protection
- Input validation
- SQL injection protection

## 🚀 Production Deployment Commands

### Build Docker Image
```bash
cd "/home/kali/latest/Claude's made dashboard"
docker build -t security-dashboard:latest .
```

### Run Production Container
```bash
docker run -d \
  --name security-dashboard-prod \
  --restart unless-stopped \
  -p 5000:5000 \
  -e FLASK_ENV=production \
  -e DB_HOST=your-db-host \
  -e DB_USER=dashboard \
  -e DB_PASSWORD=your-secure-password \
  -e FLASK_SECRET_KEY=your-very-secure-secret-key \
  security-dashboard:latest
```

### Full Stack with Docker Compose
```bash
# Production deployment
docker-compose -f docker-compose.yml up -d

# Check status
docker-compose ps

# Scale workers (if needed)
docker-compose up -d --scale app=3
```

## 🎯 API Endpoints

- `GET /api/ping` - Health check
- `POST /api/alerts` - Submit security alerts
- `GET /api/alerts` - Retrieve alerts
- `POST /api/gps` - Submit GPS data
- `GET /api/gps` - Retrieve GPS data
- `GET /api/stats` - Get statistics

## 🔧 Troubleshooting

### Common Issues

1. **Database Connection Failed**
   ```bash
   # Check MySQL service
   docker-compose logs db
   
   # Verify environment variables
   docker exec security-dashboard env | grep DB_
   ```

2. **Port Already in Use**
   ```bash
   # Find process using port 5000
   lsof -i :5000
   
   # Use different port
   export PORT=5001
   ```

3. **Permission Issues**
   ```bash
   # Fix file permissions
   chmod +x start_gunicorn.sh
   
   # Fix directory permissions for Docker
   sudo chown -R $USER:$USER .
   ```

## 📈 Performance Tuning

### Gunicorn Workers
Edit `gunicorn.conf.py`:
```python
# Adjust workers based on your server
workers = 4  # For 2-core server
worker_class = "gevent"  # For async workloads
```

### Docker Resources
```bash
# Limit container resources
docker run --memory="512m" --cpus="1.0" security-dashboard
```

## 🔄 Updates and Maintenance

### Update Application
```bash
# Rebuild and redeploy
docker-compose build app
docker-compose up -d app

# Or with downtime
docker-compose down
docker-compose up -d
```

### Database Backup
```bash
# Backup database
docker exec security_dashboard_db mysqldump -u dashboard -p security_dashboard > backup.sql

# Restore
docker exec -i security_dashboard_db mysql -u dashboard -p security_dashboard < backup.sql
```
