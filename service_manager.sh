#!/bin/bash
"""
Service Management Script for WiGuard Dashboard
Provides easy service installation, management, and monitoring
"""

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="/opt/wiguard-dashboard"
SERVICE_USER="www-data"
SYSTEMD_DIR="/etc/systemd/system"
CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Helper functions
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root"
        exit 1
    fi
}

check_systemd() {
    if ! command -v systemctl >/dev/null 2>&1; then
        print_error "Systemd is not available on this system"
        exit 1
    fi
}

install_services() {
    print_status "Installing WiGuard Dashboard services..."
    
    # Create install directory
    mkdir -p "$INSTALL_DIR"
    
    # Copy application files
    print_status "Copying application files..."
    cp -r "$CURRENT_DIR"/* "$INSTALL_DIR/"
    
    # Create service user if it doesn't exist
    if ! id "$SERVICE_USER" &>/dev/null; then
        print_status "Creating service user: $SERVICE_USER"
        useradd -r -s /bin/false -d "$INSTALL_DIR" "$SERVICE_USER"
    fi
    
    # Set up Python virtual environment
    print_status "Setting up Python virtual environment..."
    cd "$INSTALL_DIR"
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Create necessary directories
    mkdir -p logs data
    chown -R "$SERVICE_USER:$SERVICE_USER" logs data
    
    # Copy and install systemd service files
    print_status "Installing systemd service files..."
    cp systemd/wiguard-dashboard.service "$SYSTEMD_DIR/"
    cp systemd/wiguard-monitor.service "$SYSTEMD_DIR/"
    
    # Reload systemd
    systemctl daemon-reload
    
    # Enable services
    systemctl enable wiguard-dashboard.service
    systemctl enable wiguard-monitor.service
    
    print_success "Services installed successfully!"
    print_status "Start services with: sudo systemctl start wiguard-dashboard"
}

uninstall_services() {
    print_status "Uninstalling WiGuard Dashboard services..."
    
    # Stop and disable services
    systemctl stop wiguard-dashboard.service wiguard-monitor.service 2>/dev/null || true
    systemctl disable wiguard-dashboard.service wiguard-monitor.service 2>/dev/null || true
    
    # Remove service files
    rm -f "$SYSTEMD_DIR/wiguard-dashboard.service"
    rm -f "$SYSTEMD_DIR/wiguard-monitor.service"
    
    # Reload systemd
    systemctl daemon-reload
    
    print_success "Services uninstalled!"
    print_warning "Application files remain in $INSTALL_DIR"
}

start_services() {
    print_status "Starting WiGuard Dashboard services..."
    
    # Start main dashboard first
    systemctl start wiguard-dashboard.service
    sleep 3
    
    # Start monitoring service
    systemctl start wiguard-monitor.service
    
    print_success "Services started!"
}

stop_services() {
    print_status "Stopping WiGuard Dashboard services..."
    
    systemctl stop wiguard-monitor.service wiguard-dashboard.service
    
    print_success "Services stopped!"
}

restart_services() {
    print_status "Restarting WiGuard Dashboard services..."
    
    stop_services
    sleep 2
    start_services
}

status_services() {
    print_status "WiGuard Dashboard Service Status:"
    echo
    
    echo "Dashboard Service:"
    systemctl status wiguard-dashboard.service --no-pager -l
    echo
    
    echo "Monitor Service:"
    systemctl status wiguard-monitor.service --no-pager -l
    echo
    
    # Show recent logs
    print_status "Recent Dashboard Logs:"
    journalctl -u wiguard-dashboard.service --no-pager -n 10
    echo
    
    print_status "Recent Monitor Logs:"
    journalctl -u wiguard-monitor.service --no-pager -n 10
}

logs_services() {
    service="${1:-dashboard}"
    lines="${2:-50}"
    
    case "$service" in
        "dashboard")
            journalctl -u wiguard-dashboard.service -n "$lines" -f
            ;;
        "monitor")
            journalctl -u wiguard-monitor.service -n "$lines" -f
            ;;
        "all")
            journalctl -u wiguard-dashboard.service -u wiguard-monitor.service -n "$lines" -f
            ;;
        *)
            print_error "Unknown service: $service"
            print_status "Available services: dashboard, monitor, all"
            exit 1
            ;;
    esac
}

update_configuration() {
    print_status "Updating service configuration..."
    
    # Copy updated service files
    cp systemd/wiguard-dashboard.service "$SYSTEMD_DIR/"
    cp systemd/wiguard-monitor.service "$SYSTEMD_DIR/"
    
    # Reload systemd
    systemctl daemon-reload
    
    print_success "Configuration updated! Restart services to apply changes."
}

health_check() {
    print_status "Running WiGuard Dashboard health check..."
    
    # Check service status
    if systemctl is-active --quiet wiguard-dashboard.service; then
        print_success "Dashboard service is running"
    else
        print_error "Dashboard service is not running"
        return 1
    fi
    
    if systemctl is-active --quiet wiguard-monitor.service; then
        print_success "Monitor service is running"
    else
        print_warning "Monitor service is not running"
    fi
    
    # Check HTTP endpoint
    if curl -s -f http://localhost:5053/api/ping >/dev/null; then
        print_success "Dashboard HTTP endpoint is responding"
    else
        print_error "Dashboard HTTP endpoint is not responding"
        return 1
    fi
    
    # Run system validation
    if [ -f "$INSTALL_DIR/system_validator.py" ]; then
        cd "$INSTALL_DIR"
        source venv/bin/activate
        if python3 system_validator.py --quick >/dev/null 2>&1; then
            print_success "System validation passed"
        else
            print_warning "System validation found issues"
        fi
    fi
    
    print_success "Health check completed!"
}

backup_configuration() {
    backup_dir="/tmp/wiguard-backup-$(date +%Y%m%d_%H%M%S)"
    print_status "Creating configuration backup in $backup_dir..."
    
    mkdir -p "$backup_dir"
    
    # Backup configuration files
    cp "$INSTALL_DIR/.env" "$backup_dir/" 2>/dev/null || true
    cp "$INSTALL_DIR"/*.conf "$backup_dir/" 2>/dev/null || true
    cp "$SYSTEMD_DIR/wiguard-*.service" "$backup_dir/" 2>/dev/null || true
    
    # Create backup info
    cat > "$backup_dir/backup_info.txt" << EOF
WiGuard Dashboard Configuration Backup
Created: $(date)
System: $(uname -a)
Dashboard Version: $(cd "$INSTALL_DIR" && git describe --tags 2>/dev/null || echo "unknown")
EOF
    
    print_success "Backup created in $backup_dir"
}

show_help() {
    cat << EOF
WiGuard Dashboard Service Management Script

Usage: $0 <command> [options]

Commands:
    install         Install WiGuard Dashboard services
    uninstall       Uninstall WiGuard Dashboard services
    start           Start all services
    stop            Stop all services
    restart         Restart all services
    status          Show service status and logs
    logs [service]  Show logs (dashboard|monitor|all) [default: dashboard]
    update-config   Update service configuration files
    health-check    Run comprehensive health check
    backup          Create configuration backup

Examples:
    $0 install                 # Install services
    $0 start                   # Start all services
    $0 logs monitor            # Show monitor service logs
    $0 health-check           # Check system health

For more information, see the documentation.
EOF
}

# Main script logic
main() {
    case "${1:-}" in
        "install")
            check_root
            check_systemd
            install_services
            ;;
        "uninstall")
            check_root
            check_systemd
            uninstall_services
            ;;
        "start")
            check_root
            check_systemd
            start_services
            ;;
        "stop")
            check_root
            check_systemd
            stop_services
            ;;
        "restart")
            check_root
            check_systemd
            restart_services
            ;;
        "status")
            check_systemd
            status_services
            ;;
        "logs")
            check_systemd
            logs_services "${2:-dashboard}" "${3:-50}"
            ;;
        "update-config")
            check_root
            check_systemd
            update_configuration
            ;;
        "health-check")
            health_check
            ;;
        "backup")
            backup_configuration
            ;;
        "help"|"--help"|"-h")
            show_help
            ;;
        "")
            print_error "No command specified"
            show_help
            exit 1
            ;;
        *)
            print_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
