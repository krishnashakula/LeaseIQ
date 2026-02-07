# Production Deployment Guide

## 🚀 Production Checklist

### 1. Environment Setup
- [ ] Copy `.env.example` to `.env`
- [ ] Generate secure `SECRET_KEY` using `python -c "import secrets; print(secrets.token_hex(32))"`
- [ ] Set `FLASK_ENV=production`
- [ ] Configure `CORS_ORIGINS` with actual domain(s)
- [ ] Review and adjust `MAX_CONTENT_LENGTH` based on needs
- [ ] Set appropriate `LOG_LEVEL` (INFO or WARNING for production)

### 2. Dependencies
```bash
# Install production dependencies
pip install -r requirements.txt

# Optional: Install Tesseract for OCR support
# sudo apt-get install tesseract-ocr  # Linux
# brew install tesseract  # macOS
```

### 3. Security Configuration
- [ ] Use HTTPS/TLS in production
- [ ] Configure firewall to restrict access
- [ ] Set up rate limiting (consider using nginx or API gateway)
- [ ] Enable security headers (already configured)
- [ ] Restrict CORS origins to specific domains
- [ ] Use strong SECRET_KEY (never commit to git)
- [ ] Keep dependencies updated regularly

### 4. File System
```bash
# Create required directories
mkdir -p uploads outputs logs

# Set proper permissions (Linux/macOS)
chmod 755 uploads outputs
chmod 644 logs
```

### 5. Running in Production

#### Option A: Waitress (Recommended)
```bash
# Install waitress (included in requirements.txt)
python app.py
```

#### Option B: Gunicorn (Linux/macOS only)
```bash
# Install gunicorn
pip install gunicorn

# Run with 4 workers
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

#### Option C: Using Systemd (Linux)
Create `/etc/systemd/system/pdf-api.service`:
```ini
[Unit]
Description=PDF Extraction API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/backend
Environment="PATH=/path/to/venv/bin"
EnvironmentFile=/path/to/backend/.env
ExecStart=/path/to/venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable pdf-api
sudo systemctl start pdf-api
sudo systemctl status pdf-api
```

### 6. Reverse Proxy (Nginx)
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    client_max_body_size 50M;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts for large file uploads
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
```

### 7. Monitoring & Maintenance

#### Log Monitoring
```bash
# View real-time logs
tail -f app.log

# Check for errors
grep "ERROR" app.log

# Monitor disk usage
du -sh uploads/ outputs/
```

#### Cleanup Old Files
Create a cleanup script:
```bash
#!/bin/bash
# cleanup.sh - Run daily via cron

# Remove uploads older than 1 day
find /path/to/uploads -type f -mtime +1 -delete

# Remove outputs older than 7 days
find /path/to/outputs -type f -mtime +7 -delete

# Rotate logs if needed (or use logrotate)
```

Add to crontab:
```bash
crontab -e
# Add: 0 2 * * * /path/to/cleanup.sh
```

### 8. Performance Optimization
- [ ] Use Redis for caching (optional)
- [ ] Implement connection pooling
- [ ] Use CDN for static assets
- [ ] Enable gzip compression in nginx
- [ ] Monitor memory usage and adjust workers
- [ ] Set up horizontal scaling if needed

### 9. Backup Strategy
```bash
# Backup script
#!/bin/bash
BACKUP_DIR="/backups/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# Backup outputs
tar -czf $BACKUP_DIR/outputs.tar.gz outputs/

# Keep last 30 days
find /backups -type d -mtime +30 -exec rm -rf {} +
```

### 10. Health Monitoring
```bash
# Check health endpoint
curl https://your-domain.com/health

# Expected response:
{
  "status": "healthy",
  "service": "PDF Extractor API",
  "version": "1.0.0",
  "checks": {
    "pymupdf": true,
    "business_intelligence": true,
    "upload_folder": true,
    "output_folder": true
  }
}
```

## 🔒 Security Best Practices

1. **Never expose .env file**
2. **Use environment variables for secrets**
3. **Keep all dependencies updated**
4. **Enable firewall rules**
5. **Use HTTPS only**
6. **Implement rate limiting**
7. **Sanitize all user inputs**
8. **Regular security audits**
9. **Monitor logs for suspicious activity**
10. **Backup regularly**

## 📊 Monitoring Metrics

Monitor these key metrics:
- API response times
- Error rates
- File processing success/failure rates
- Disk usage (uploads/outputs folders)
- Memory usage
- CPU usage
- Request rate

## 🆘 Troubleshooting

### Application won't start
```bash
# Check logs
cat app.log

# Verify environment
python -c "from config import get_config; print(get_config())"

# Test imports
python -c "import fitz; print('PyMuPDF OK')"
```

### High memory usage
- Reduce number of workers
- Implement file size limits
- Clean up old files more frequently
- Monitor PDF processing memory spikes

### Slow processing
- Check CPU usage
- Verify disk I/O
- Review log for bottlenecks
- Consider adding more workers

## 📈 Scaling

### Horizontal Scaling
- Use load balancer (nginx, HAProxy)
- Deploy multiple instances
- Share uploads/outputs via NFS or S3
- Use Redis for distributed caching

### Vertical Scaling
- Increase server resources
- Optimize PDF processing
- Add more worker processes
- Use faster storage (SSD)

## 🔄 Updates & Maintenance

```bash
# Update dependencies (test in staging first!)
pip list --outdated
pip install -U package-name

# Restart service
sudo systemctl restart pdf-api

# Verify health
curl http://localhost:5000/health
```

## 📝 Version History

- v1.0.0 (2026-02-06): Initial production release
  - PDF extraction with PyMuPDF
  - Business intelligence analysis
  - Production-ready configuration
  - Security hardening
  - Comprehensive logging
