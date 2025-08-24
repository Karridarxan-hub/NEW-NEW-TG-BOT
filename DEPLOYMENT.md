# FACEIT CS2 Bot - Deployment & Maintenance Guide

This comprehensive guide covers production deployment, monitoring, and maintenance for the FACEIT CS2 Telegram bot.

## Table of Contents

1. [Production Deployment](#production-deployment)
2. [Environment Configuration](#environment-configuration)
3. [Docker Deployment](#docker-deployment)
4. [Database Setup](#database-setup)
5. [Monitoring & Logging](#monitoring--logging)
6. [Backup & Recovery](#backup--recovery)
7. [Security Considerations](#security-considerations)
8. [Maintenance Tasks](#maintenance-tasks)
9. [Troubleshooting](#troubleshooting)
10. [Scaling Considerations](#scaling-considerations)

---

## Production Deployment

### Prerequisites

- **Operating System**: Ubuntu 20.04+ or CentOS 8+ (recommended)
- **Docker**: 20.10+ with Docker Compose v2
- **Memory**: Minimum 2GB RAM (4GB+ recommended)
- **Storage**: 20GB+ available disk space
- **Network**: Open ports 80, 443, 8080 (configurable)

### Step-by-Step Production Setup

#### 1. Server Preparation

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

#### 2. Project Deployment

```bash
# Clone the repository
git clone <your-repo-url> /opt/faceit-cs2-bot
cd /opt/faceit-cs2-bot

# Set proper permissions
sudo chown -R $USER:$USER /opt/faceit-cs2-bot

# Create required directories
mkdir -p logs data nginx/ssl

# Copy environment configuration
cp .env.example .env
```

#### 3. SSL Certificate Setup

```bash
# Using Let's Encrypt (recommended)
sudo apt install certbot python3-certbot-nginx -y

# Generate SSL certificate
sudo certbot certonly --standalone -d your-domain.com

# Copy certificates to nginx directory
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/
sudo chown -R $USER:$USER nginx/ssl/
```

#### 4. Production Deployment

```bash
# Run deployment script
chmod +x scripts/deploy.sh
./scripts/deploy.sh prod

# Or manual deployment
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

---

## Environment Configuration

### Required Environment Variables

Create a `.env` file with the following configurations:

```bash
# Bot Configuration
BOT_TOKEN=your_telegram_bot_token_here
FACEIT_API_KEY=your_faceit_api_key_here

# Webhook Configuration (optional for production)
WEBHOOK_URL=https://your-domain.com/webhook/telegram

# Debug and Logging
DEBUG=false
LOG_LEVEL=INFO

# Database Configuration
DATABASE_URL=postgresql://faceit_user:your_secure_password@postgres:5432/faceit_bot
POSTGRES_DB=faceit_bot
POSTGRES_USER=faceit_user
POSTGRES_PASSWORD=your_secure_password

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# Security
SECRET_KEY=your_random_secret_key_here

# Notification Webhooks (optional)
WEBHOOK_DEPLOY_URL=https://hooks.slack.com/services/your/slack/webhook
BACKUP_WEBHOOK_URL=https://hooks.slack.com/services/your/slack/webhook

# Backup Configuration
BACKUP_DIR=/opt/backups/faceit-cs2-bot
```

### Environment Variable Security

```bash
# Set secure permissions on .env file
chmod 600 .env

# Validate environment variables
source .env
if [[ -z "$BOT_TOKEN" || -z "$FACEIT_API_KEY" ]]; then
    echo "Critical environment variables missing!"
    exit 1
fi
```

---

## Docker Deployment

### Production Docker Compose Stack

The bot uses multi-stage Docker builds and separate configurations for development and production:

#### Key Components:
- **faceit-bot**: Main application container (Python 3.11)
- **postgres**: PostgreSQL 15 database
- **redis**: Redis 7 for caching
- **nginx**: Reverse proxy with SSL termination

#### Resource Limits (Production):
```yaml
faceit-bot:
  deploy:
    resources:
      limits:
        cpus: '2.0'
        memory: 1G
      reservations:
        cpus: '1.0'
        memory: 512M
```

### Docker Commands

```bash
# Build and start production stack
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# View running containers
docker-compose ps

# View logs
docker-compose logs -f faceit-bot

# Restart specific service
docker-compose restart faceit-bot

# Update and redeploy
git pull
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# Stop all services
docker-compose down

# Clean up unused resources
docker system prune -f
```

### Health Checks

All services include built-in health checks:

```bash
# Check container health status
docker-compose ps

# Manual health check
curl -f http://localhost:8080/health

# Detailed health check script
./scripts/health-check.sh --detailed
```

---

## Database Setup

### PostgreSQL Configuration

#### Initialization
The database is automatically initialized using `migrations/init.sql` which creates:

- **users**: Bot users table
- **user_settings**: User preferences
- **match_history**: Match statistics
- **comparison_lists**: Player comparison data
- **user_sessions**: Session tracking
- **faceit_cache**: API response caching
- **tracked_matches**: Match notifications

#### Database Management

```bash
# Connect to database
docker-compose exec postgres psql -U faceit_user -d faceit_bot

# Backup database
docker-compose exec postgres pg_dump -U faceit_user faceit_bot > backup.sql

# Restore database
docker-compose exec -T postgres psql -U faceit_user -d faceit_bot < backup.sql

# Monitor database size
docker-compose exec postgres psql -U faceit_user -d faceit_bot -c "
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public' 
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"
```

### Redis Configuration

Redis is used for:
- API response caching (TTL: 5-60 minutes)
- Session storage
- Rate limiting

```bash
# Connect to Redis
docker-compose exec redis redis-cli

# Monitor Redis usage
docker-compose exec redis redis-cli info memory

# Clear cache (if needed)
docker-compose exec redis redis-cli flushdb
```

---

## Monitoring & Logging

### Log Management

#### Log Locations:
```bash
# Application logs
./logs/bot.log
./logs/error.log

# Container logs
docker-compose logs faceit-bot
docker-compose logs postgres
docker-compose logs redis
docker-compose logs nginx

# System logs
/var/log/faceit-cs2-bot-deploy.log
```

#### Log Rotation Configuration:
```bash
# Create logrotate configuration
sudo tee /etc/logrotate.d/faceit-cs2-bot << EOF
/opt/faceit-cs2-bot/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    notifempty
    copytruncate
    sharedscripts
    postrotate
        docker-compose -f /opt/faceit-cs2-bot/docker-compose.yml restart faceit-bot
    endscript
}
EOF
```

### Health Monitoring

#### Automated Health Checks:
```bash
# Add to crontab for regular monitoring
*/5 * * * * /opt/faceit-cs2-bot/scripts/health-check.sh --json >> /var/log/health-check.log

# Set up alerts for failures
*/5 * * * * /opt/faceit-cs2-bot/scripts/health-check.sh || echo "Bot health check failed" | mail -s "FACEIT Bot Alert" admin@example.com
```

#### Metrics Collection:
If using Prometheus (optional):
```bash
# Enable monitoring profile
docker-compose --profile monitoring -f docker-compose.yml -f docker-compose.prod.yml up -d

# Access metrics
curl http://localhost:9100/metrics
```

### Application Metrics

The bot exposes the following metrics endpoints:
- `GET /health` - Health check status
- `GET /metrics` - Prometheus metrics (if enabled)
- `GET /api/stats` - Bot usage statistics

---

## Backup & Recovery

### Automated Backup Strategy

#### Backup Script Usage:
```bash
# Standard backup (config + source code)
./scripts/backup.sh

# Full backup (includes logs and data)
./scripts/backup.sh --full

# Configuration only
./scripts/backup.sh --config-only

# Set retention period
./scripts/backup.sh --retention-days 7
```

#### Scheduled Backups:
```bash
# Add to crontab
0 2 * * * /opt/faceit-cs2-bot/scripts/backup.sh --full
0 6,18 * * * /opt/faceit-cs2-bot/scripts/backup.sh
```

### Backup Components

1. **Application Code**: Python files, configuration
2. **Database**: PostgreSQL dumps
3. **Data**: User data, logs (optional)
4. **Configuration**: Docker Compose files, Nginx config
5. **Docker Volumes**: Redis data, PostgreSQL data

### Recovery Procedures

#### Application Recovery:
```bash
# Stop services
docker-compose down

# Restore from backup
cd /opt/backups/faceit-cs2-bot
tar -xzf faceit-cs2-bot_full_20240101_020000.tar.gz
cp -r backup_20240101_020000/* /opt/faceit-cs2-bot/

# Restart services
./scripts/deploy.sh prod
```

#### Database Recovery:
```bash
# Stop bot (to prevent data conflicts)
docker-compose stop faceit-bot

# Restore database
docker-compose exec -T postgres psql -U faceit_user -d faceit_bot < backup.sql

# Restart services
docker-compose up -d
```

---

## Security Considerations

### API Keys & Secrets

1. **Environment Variables**: Store all secrets in `.env` files
2. **File Permissions**: Set `.env` to 600 (owner read/write only)
3. **Secret Rotation**: Regularly rotate API keys and passwords
4. **Version Control**: Never commit secrets to Git

### Network Security

#### Firewall Configuration:
```bash
# UFW firewall rules
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

#### Nginx Security Headers:
The nginx configuration includes:
- HSTS (HTTP Strict Transport Security)
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- Content Security Policy
- Rate limiting for API endpoints

### Container Security

1. **Non-root User**: Containers run as non-privileged user (uid 1000)
2. **Resource Limits**: CPU and memory limits prevent resource exhaustion
3. **Network Isolation**: Services communicate through dedicated Docker network
4. **Health Checks**: Built-in health monitoring for early issue detection

### Data Protection

1. **Database Encryption**: Use encrypted PostgreSQL connections in production
2. **Backup Encryption**: Encrypt backup files before remote storage
3. **Log Sanitization**: Sensitive data is masked in logs

---

## Maintenance Tasks

### Daily Tasks

```bash
# Check service health
./scripts/health-check.sh --detailed

# Review logs for errors
docker-compose logs --tail=100 faceit-bot | grep ERROR

# Monitor disk usage
df -h
du -sh logs/
```

### Weekly Tasks

```bash
# Update Docker images (if needed)
docker-compose pull
docker-compose up -d

# Clean up old Docker resources
docker system prune -f
docker volume prune -f

# Review backup status
ls -la /opt/backups/faceit-cs2-bot/
```

### Monthly Tasks

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Review and rotate logs
sudo logrotate -f /etc/logrotate.d/faceit-cs2-bot

# Database maintenance
docker-compose exec postgres psql -U faceit_user -d faceit_bot -c "VACUUM ANALYZE;"

# Security updates
# Review and update API keys if needed
# Check for application updates
```

### SSL Certificate Renewal

```bash
# Certbot automatic renewal (add to crontab)
0 12 * * * certbot renew --quiet && docker-compose restart nginx

# Manual renewal
sudo certbot renew
sudo cp /etc/letsencrypt/live/your-domain.com/*.pem nginx/ssl/
docker-compose restart nginx
```

---

## Troubleshooting

### Common Issues

#### 1. Bot Not Responding

```bash
# Check container status
docker-compose ps

# Check logs
docker-compose logs faceit-bot

# Restart bot
docker-compose restart faceit-bot

# Verify Telegram webhook
curl -X GET "https://api.telegram.org/bot$BOT_TOKEN/getWebhookInfo"
```

#### 2. Database Connection Issues

```bash
# Check PostgreSQL status
docker-compose exec postgres pg_isready -U faceit_user

# Test connection
docker-compose exec postgres psql -U faceit_user -d faceit_bot -c "SELECT 1;"

# Check database logs
docker-compose logs postgres
```

#### 3. FACEIT API Issues

```bash
# Test API connectivity
curl -H "Authorization: Bearer $FACEIT_API_KEY" \
     "https://open.faceit.com/data/v4/players?nickname=test"

# Check rate limiting
docker-compose exec redis redis-cli keys "*rate_limit*"
```

#### 4. High Memory Usage

```bash
# Check resource usage
docker stats

# Review application logs for memory leaks
docker-compose logs faceit-bot | grep -i memory

# Restart if necessary
docker-compose restart faceit-bot
```

### Log Analysis

```bash
# Error patterns
docker-compose logs faceit-bot | grep -E "(ERROR|CRITICAL|Exception)"

# API rate limiting
docker-compose logs faceit-bot | grep -i "rate"

# Database performance
docker-compose logs postgres | grep -i "slow"

# Connection issues
docker-compose logs nginx | grep -E "(50[0-9]|40[0-9])"
```

### Performance Monitoring

```bash
# Container resource usage
docker stats --no-stream

# Database performance
docker-compose exec postgres psql -U faceit_user -d faceit_bot -c "
SELECT query, calls, mean_time, max_time 
FROM pg_stat_statements 
ORDER BY mean_time DESC LIMIT 10;"

# Redis memory usage
docker-compose exec redis redis-cli info memory | grep used_memory
```

---

## Scaling Considerations

### Horizontal Scaling

#### Load Balancer Setup:
For high availability, deploy multiple bot instances behind a load balancer:

```yaml
# docker-compose.scale.yml
services:
  faceit-bot:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
```

#### Session Affinity:
Use Redis for session storage to support multiple bot instances:
```bash
# Scale bot service
docker-compose -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.scale.yml up -d --scale faceit-bot=3
```

### Vertical Scaling

#### Resource Optimization:
```yaml
# Increased resources for high traffic
faceit-bot:
  deploy:
    resources:
      limits:
        cpus: '4.0'
        memory: 2G
      reservations:
        cpus: '2.0'
        memory: 1G
```

### Database Scaling

#### Read Replicas:
```yaml
# Add read-only database replica
postgres-read:
  image: postgres:15-alpine
  environment:
    POSTGRES_USER: replica_user
    POSTGRES_PASSWORD: replica_password
  command: >
    postgres
    -c hot_standby=on
    -c wal_level=replica
```

#### Connection Pooling:
Consider using PgBouncer for connection pooling:
```yaml
pgbouncer:
  image: pgbouncer/pgbouncer:latest
  environment:
    DATABASES_HOST: postgres
    DATABASES_PORT: 5432
    POOL_MODE: transaction
    MAX_CLIENT_CONN: 100
```

### Monitoring at Scale

#### Centralized Logging:
```yaml
# ELK Stack for log aggregation
elasticsearch:
  image: elasticsearch:8.8.0
  environment:
    - discovery.type=single-node
    
logstash:
  image: logstash:8.8.0
  volumes:
    - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    
kibana:
  image: kibana:8.8.0
  ports:
    - "5601:5601"
```

#### Metrics Collection:
```yaml
# Prometheus + Grafana
prometheus:
  image: prom/prometheus
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml
    
grafana:
  image: grafana/grafana
  ports:
    - "3000:3000"
```

### Traffic Management

#### Rate Limiting:
Nginx configuration handles rate limiting, but for high traffic:
```nginx
# Enhanced rate limiting
limit_req_zone $binary_remote_addr zone=api:10m rate=100r/s;
limit_req_zone $binary_remote_addr zone=webhook:10m rate=10r/s;

location /api/ {
    limit_req zone=api burst=50 nodelay;
    # ... rest of configuration
}
```

#### Caching Strategy:
```yaml
# Redis cluster for caching at scale
redis-cluster:
  image: redis:7-alpine
  command: redis-server --cluster-enabled yes --cluster-config-file nodes.conf
  deploy:
    replicas: 6
```

---

## Production Checklist

Before going live, ensure:

### Security
- [ ] All API keys are properly secured
- [ ] SSL certificates are configured and valid
- [ ] Firewall rules are in place
- [ ] Database passwords are strong and unique
- [ ] Log files don't contain sensitive information

### Performance
- [ ] Resource limits are configured
- [ ] Health checks are working
- [ ] Database is optimized (indexes, vacuum)
- [ ] Redis caching is enabled
- [ ] Log rotation is configured

### Monitoring
- [ ] Health check script is scheduled
- [ ] Log monitoring is set up
- [ ] Backup automation is configured
- [ ] Alert notifications are working
- [ ] Metrics collection is enabled

### Documentation
- [ ] Environment variables are documented
- [ ] Deployment procedures are tested
- [ ] Recovery procedures are validated
- [ ] Team access is configured
- [ ] Monitoring dashboards are accessible

---

## Support and Maintenance Contacts

### Emergency Procedures
1. **Service Down**: Run `./scripts/health-check.sh --detailed`
2. **High Load**: Monitor with `docker stats` and scale if needed
3. **Data Loss**: Restore from latest backup using procedures above
4. **Security Incident**: Immediately rotate all API keys and passwords

### Regular Maintenance Windows
- **Weekly**: Sunday 02:00-04:00 UTC (automated backups)
- **Monthly**: First Sunday 01:00-05:00 UTC (system updates)

This deployment guide provides comprehensive coverage for production deployment and maintenance of the FACEIT CS2 bot. Always test procedures in a staging environment before applying to production.