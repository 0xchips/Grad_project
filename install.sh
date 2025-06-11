#!/bin/bash

# WiGuard Security Dashboard Installation Script
# This script sets up the complete WiGuard environment on a fresh system

set -e  # Exit on any error

echo "🚀 WiGuard Security Dashboard Installation"
echo "========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_error "This script should not be run as root!"
        log_info "Please run as a regular user with sudo privileges"
        exit 1
    fi
}

# Detect OS
detect_os() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$ID
        VERSION=$VERSION_ID
    else
        log_error "Cannot detect operating system"
        exit 1
    fi
    
    log_info "Detected OS: $OS $VERSION"
}

# Install system dependencies
install_system_deps() {
    log_info "Installing system dependencies..."
    
    case $OS in
        "ubuntu"|"debian"|"kali")
            sudo apt-get update
            sudo apt-get install -y \
                python3 \
                python3-pip \
                python3-venv \
                mysql-server \
                mysql-client \
                libmysqlclient-dev \
                pkg-config \
                build-essential \
                git \
                curl \
                wget \
                aircrack-ng \
                kismet \
                wireshark \
                tcpdump \
                nmap \
                suricata \
                jq \
                net-tools \
                wireless-tools
            ;;
        "fedora"|"centos"|"rhel")
            sudo dnf install -y \
                python3 \
                python3-pip \
                mysql-server \
                mysql-devel \
                pkgconfig \
                gcc \
                gcc-c++ \
                git \
                curl \
                wget \
                aircrack-ng \
                kismet \
                wireshark \
                tcpdump \
                nmap \
                suricata \
                jq \
                net-tools \
                wireless-tools
            ;;
        *)
            log_error "Unsupported operating system: $OS"
            log_info "Please install dependencies manually"
            exit 1
            ;;
    esac
    
    log_success "System dependencies installed"
}

# Setup MySQL
setup_mysql() {
    log_info "Setting up MySQL database..."
    
    # Start MySQL service
    sudo systemctl start mysql || sudo systemctl start mysqld
    sudo systemctl enable mysql || sudo systemctl enable mysqld
    
    # Check if MySQL is running
    if ! sudo systemctl is-active --quiet mysql && ! sudo systemctl is-active --quiet mysqld; then
        log_error "MySQL service failed to start"
        exit 1
    fi
    
    # Secure MySQL installation (basic setup)
    log_info "Configuring MySQL..."
    
    # Create database and user
    mysql -u root -p <<EOF || {
        log_warning "MySQL root password required. Setting up database manually..."
        echo "Please run the following commands in MySQL:"
        echo "CREATE DATABASE IF NOT EXISTS security_dashboard;"
        echo "CREATE USER IF NOT EXISTS 'dashboard'@'localhost' IDENTIFIED BY 'securepass';"
        echo "GRANT ALL PRIVILEGES ON security_dashboard.* TO 'dashboard'@'localhost';"
        echo "FLUSH PRIVILEGES;"
        read -p "Press Enter when you've completed the MySQL setup..."
    }
CREATE DATABASE IF NOT EXISTS security_dashboard;
CREATE USER IF NOT EXISTS 'dashboard'@'localhost' IDENTIFIED BY 'securepass';
GRANT ALL PRIVILEGES ON security_dashboard.* TO 'dashboard'@'localhost';
FLUSH PRIVILEGES;
EOF
    
    log_success "MySQL database configured"
}

# Setup Python environment
setup_python() {
    log_info "Setting up Python virtual environment..."
    
    # Create virtual environment
    python3 -m venv venv
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install Python dependencies
    log_info "Installing Python packages..."
    pip install -r requirements.txt
    
    log_success "Python environment configured"
}

# Configure Kismet
configure_kismet() {
    log_info "Configuring Kismet..."
    
    # Add user to kismet group
    sudo usermod -a -G kismet $USER || log_warning "Kismet group not found, creating..."
    
    # Create kismet group if it doesn't exist
    sudo groupadd -f kismet
    sudo usermod -a -G kismet $USER
    
    # Setup Kismet configuration
    sudo mkdir -p /etc/kismet/
    
    # Copy Kismet configuration if it doesn't exist
    if [[ ! -f /etc/kismet/kismet.conf ]]; then
        if [[ -f kismet_site.conf ]]; then
            sudo cp kismet_site.conf /etc/kismet/kismet_site.conf
        fi
    fi
    
    # Setup passwordless sudo for Kismet
    echo "$USER ALL=(ALL) NOPASSWD: /usr/bin/kismet" | sudo tee /etc/sudoers.d/kismet-$USER
    
    log_success "Kismet configured"
}

# Setup environment file
setup_environment() {
    log_info "Setting up environment configuration..."
    
    if [[ ! -f .env ]]; then
        cp .env.example .env
        log_info "Created .env file from .env.example"
        log_warning "Please review and update .env file with your specific configuration"
    else
        log_info ".env file already exists"
    fi
}

# Initialize database
init_database() {
    log_info "Initializing database..."
    
    # Load database schema
    mysql -u dashboard -psecurepass security_dashboard < init.sql
    
    log_success "Database initialized"
}

# Create systemd service
create_service() {
    log_info "Creating systemd service..."
    
    sudo tee /etc/systemd/system/wiguard.service > /dev/null <<EOF
[Unit]
Description=WiGuard Security Dashboard
After=network.target mysql.service

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=$(pwd)/venv/bin/python $(pwd)/flaskkk.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    sudo systemctl daemon-reload
    sudo systemctl enable wiguard
    
    log_success "Systemd service created"
}

# Test installation
test_installation() {
    log_info "Testing installation..."
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Test database connection
    python3 -c "
import MySQLdb
try:
    conn = MySQLdb.connect(
        host='localhost',
        user='dashboard',
        passwd='securepass',
        db='security_dashboard'
    )
    print('✅ Database connection successful')
    conn.close()
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    exit(1)
"
    
    # Test Python imports
    python3 -c "
try:
    import flask
    import MySQLdb
    import requests
    import psutil
    print('✅ Python dependencies imported successfully')
except ImportError as e:
    print(f'❌ Import failed: {e}')
    exit(1)
"
    
    log_success "Installation test completed"
}

# Main installation process
main() {
    echo
    log_info "Starting WiGuard installation..."
    echo
    
    check_root
    detect_os
    
    echo
    read -p "Continue with installation? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Installation cancelled"
        exit 0
    fi
    
    install_system_deps
    setup_mysql
    setup_python
    configure_kismet
    setup_environment
    init_database
    create_service
    test_installation
    
    echo
    log_success "🎉 WiGuard installation completed successfully!"
    echo
    echo "Next steps:"
    echo "1. Review and update the .env file with your configuration"
    echo "2. Start the service: sudo systemctl start wiguard"
    echo "3. Check status: sudo systemctl status wiguard"
    echo "4. Access the dashboard: http://localhost:5053"
    echo
    echo "For manual start:"
    echo "  source venv/bin/activate"
    echo "  python3 flaskkk.py"
    echo
    log_info "Installation log saved to install.log"
}

# Run main function and log output
main 2>&1 | tee install.log
