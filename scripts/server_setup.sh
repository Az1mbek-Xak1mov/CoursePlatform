#!/bin/bash
# Server setup script for IlmSpace
# Run this on your production server as root

set -e

# Configuration - UPDATE THESE VALUES
SERVER_IP="${1:-your_server_ip}"
DOMAIN="${2:-$SERVER_IP}"
PROJECT_PATH="/var/www/ilmspace"
GIT_REPO="https://github.com/Az1mbek-Xak1mov/CoursePlatform.git"
USER="www-data"

echo "🚀 Starting IlmSpace server setup..."

# Update system
echo "📦 Updating system packages..."
apt update && apt upgrade -y

# Install required packages
echo "📦 Installing required packages..."
apt install -y python3.12 python3.12-venv python3-pip nginx git curl postgresql postgresql-contrib

# Install uv
echo "📦 Installing uv package manager..."
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

# Create project directory
echo "📁 Creating project directory..."
mkdir -p $PROJECT_PATH
cd $PROJECT_PATH

# Clone repository (or pull if exists)
if [ -d ".git" ]; then
    echo "📥 Pulling latest code..."
    git pull origin master
else
    echo "📥 Cloning repository..."
    git clone $GIT_REPO .
fi

# Set ownership
chown -R $USER:$USER $PROJECT_PATH

# Create virtual environment and install dependencies
echo "🐍 Setting up Python environment..."
cd $PROJECT_PATH
uv sync --frozen

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️ Creating .env file..."
    SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')
    cat > .env << EOF
DEBUG=False
SECRET_KEY=$SECRET_KEY
ALLOWED_HOSTS=$DOMAIN,$SERVER_IP,localhost
DATABASE_URL=sqlite:///db.sqlite3
EOF
fi

# Create logs directory
mkdir -p logs
touch logs/django.log
chown -R $USER:$USER logs

# Collect static files
echo "📦 Collecting static files..."
uv run python manage.py collectstatic --noinput

# Run migrations
echo "🔄 Running migrations..."
uv run python manage.py migrate --noinput

# Create systemd service
echo "⚙️ Creating systemd service..."
cat > /etc/systemd/system/ilmspace.service << EOF
[Unit]
Description=IlmSpace Django Application
After=network.target

[Service]
User=$USER
Group=$USER
WorkingDirectory=$PROJECT_PATH
Environment="PATH=$PROJECT_PATH/.venv/bin:/usr/local/bin:/usr/bin"
ExecStart=$PROJECT_PATH/.venv/bin/gunicorn CoursePlatform.wsgi:application --bind 127.0.0.1:8000 --workers 3 --timeout 120
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Create nginx configuration
echo "⚙️ Creating nginx configuration..."
cat > /etc/nginx/sites-available/ilmspace << EOF
server {
    listen 80;
    server_name $DOMAIN $SERVER_IP;

    client_max_body_size 100M;

    location /static/ {
        alias $PROJECT_PATH/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias $PROJECT_PATH/media/;
        expires 7d;
        add_header Cache-Control "public";
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
        proxy_connect_timeout 300s;
        proxy_read_timeout 300s;
    }
}
EOF

# Enable nginx site
ln -sf /etc/nginx/sites-available/ilmspace /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
nginx -t

# Reload systemd and start services
echo "🔄 Starting services..."
systemctl daemon-reload
systemctl enable ilmspace
systemctl start ilmspace
systemctl restart nginx

echo ""
echo "✅ Server setup completed!"
echo ""
echo "🌐 Your application is now running at: http://$DOMAIN"
echo ""
echo "📋 Useful commands:"
echo "   - Check status:  sudo systemctl status ilmspace"
echo "   - View logs:     sudo journalctl -u ilmspace -f"
echo "   - Restart app:   sudo systemctl restart ilmspace"
echo ""
echo "🔐 Don't forget to:"
echo "   1. Add GitHub secrets (SERVER_IP, SERVER_USER, SSH_PRIVATE_KEY)"
echo "   2. Generate SSH key and add to server's authorized_keys"
echo "   3. Create superuser: cd $PROJECT_PATH && uv run python manage.py createsuperuser"
