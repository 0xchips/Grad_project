#!/bin/bash
# WiGuard Dashboard Setup Script
# This script sets up the WiGuard Dashboard on different systems

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_warning "Running as root. Some operations may require elevated privileges."
    fi
}

# Detect operating system
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v apt-get >/dev/null 2>&1; then
            OS="debian"
            PACKAGE_MANAGER="apt-get"
        elif command -v yum >/dev/null 2>&1; then
            OS="redhat"
            PACKAGE_MANAGER="yum"
        elif command -v pacman >/dev/null 2>&1; then
            OS="arch"
            PACKAGE_MANAGER="pacman"
        else
            OS="linux"
            PACKAGE_MANAGER="unknown"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        PACKAGE_MANAGER="brew"
    else
        OS="unknown"
        PACKAGE_MANAGER="unknown"
    fi
    
    print_status "Detected OS: $OS"
}

# Install system dependencies
install_system_dependencies() {
    print_status "Installing system dependencies..."
    
    case $OS in
        "debian")
            sudo apt-get update
            sudo apt-get install -y python3 python3-pip python3-venv python3-dev \
                libmysqlclient-dev build-essential libssl-dev libffi-dev \
                wireless-tools aircrack-ng net-tools iw nmap git
            ;;
        "redhat")
            sudo yum update -y
            sudo yum install -y python3 python3-pip python3-devel \
                mysql-devel gcc openssl-devel libffi-devel \
                wireless-tools aircrack-ng net-tools iw nmap git
            ;;
        "arch")
            sudo pacman -Syu --noconfirm
            sudo pacman -S --noconfirm python python-pip python-virtualenv \
                mariadb-libs base-devel openssl libffi \
                wireless_tools aircrack-ng net-tools iw nmap git
            ;;
        "macos")
            if ! command -v brew >/dev/null 2>&1; then
                print_error "Homebrew not found. Please install Homebrew first."
                print_status "Visit: https://brew.sh/"
                exit 1
            fi
            brew update
            brew install python3 mysql-client nmap git
            print_warning "Some wireless tools may not be available on macOS"
            ;;
        *)
            print_warning "Unknown OS. You may need to install dependencies manually:"
            print_status "Required: python3, python3-pip, python3-dev, mysql-dev, wireless-tools"
            ;;
    esac
}

# Setup Python virtual environment
setup_python_env() {
    print_status "Setting up Python virtual environment..."
    
    # Create virtual environment if it doesn't exist
    if [[ ! -d "venv" ]]; then
        python3 -m venv venv
        print_success "Created virtual environment"
    else
        print_status "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install Python dependencies
    if [[ -f "requirements.txt" ]]; then
        print_status "Installing Python dependencies from requirements.txt..."
        pip install -r requirements.txt
    else
        print_status "Installing essential Python dependencies..."
        pip install flask flask-cors mysqlclient scapy termcolor python-dotenv psutil requests
    fi
    
    print_success "Python environment setup complete"
}

# Setup configuration
setup_configuration() {
    print_status "Setting up configuration..."
    
    # Copy example environment file if .env doesn't exist
    if [[ ! -f ".env" ]] && [[ -f ".env.example" ]]; then
        cp .env.example .env
        print_success "Created .env file from example"
        print_warning "Please edit .env file to configure your settings"
    fi
    
    # Create logs directory
    mkdir -p logs
    
    # Set appropriate permissions
    chmod 755 logs
    
    print_success "Configuration setup complete"
}

# Check wireless capabilities
check_wireless_capabilities() {
    print_status "Checking wireless capabilities..."
    
    if command -v iwconfig >/dev/null 2>&1; then
        print_success "iwconfig found - wireless monitoring available"
    else
        print_warning "iwconfig not found - wireless monitoring may be limited"
    fi
    
    if command -v airmon-ng >/dev/null 2>&1; then
        print_success "airmon-ng found - monitor mode creation available"
    else
        print_warning "airmon-ng not found - monitor mode creation unavailable"
    fi
    
    if command -v iw >/dev/null 2>&1; then
        print_success "iw found - modern wireless tools available"
    else
        print_warning "iw not found - some wireless features may not work"
    fi
    
    # List available wireless interfaces
    print_status "Available network interfaces:"
    if command -v ip >/dev/null 2>&1; then
        ip link show | grep -E "(wlan|wifi)" || print_warning "No wireless interfaces found"
    elif command -v ifconfig >/dev/null 2>&1; then
        ifconfig -a | grep -E "(wlan|wifi)" || print_warning "No wireless interfaces found"
    else
        print_warning "Cannot list network interfaces"
    fi
}

# Setup database (optional)
setup_database() {
    print_status "Database setup..."
    
    if command -v mysql >/dev/null 2>&1; then
        print_status "MySQL found. You may need to configure the database manually."
        print_status "See init.sql for database schema."
    else
        print_warning "MySQL not found. Database features will be limited."
        print_status "You can install MySQL/MariaDB later if needed."
    fi
}

# Advanced system optimization
optimize_system() {
    print_status "Optimizing system for wireless monitoring..."
    
    # Kernel parameters for better performance
    if [[ $OS_TYPE == "linux" ]]; then
        print_status "Applying kernel optimizations..."
        
        # Network buffer optimizations
        sudo tee -a /etc/sysctl.conf > /dev/null << 'EOF'
# WiGuard Dashboard optimizations
net.core.rmem_max = 134217728
net.core.wmem_max = 134217728
net.core.netdev_max_backlog = 5000
net.core.netdev_budget = 600
EOF
        
        # Apply immediately
        sudo sysctl -p >/dev/null 2>&1 || true
        
        # Disable power management for wireless interfaces
        if command -v iwconfig >/dev/null 2>&1; then
            for iface in $(iwconfig 2>/dev/null | grep -o '^[a-z0-9]*'); do
                sudo iwconfig "$iface" power off 2>/dev/null || true
            done
        fi
        
        print_success "System optimizations applied"
    else
        print_warning "System optimizations only available on Linux"
    fi
}

# Enhanced system check with new tools
run_system_check() {
    print_status "Running comprehensive system check..."
    
    # Run system validator if available
    if [[ -f "system_validator.py" ]]; then
        print_status "Running system validation..."
        python3 system_validator.py --format text || print_warning "Validation found issues"
    fi
    
    # Check interface capabilities
    if [[ -f "interface_manager.py" ]]; then
        print_status "Checking network interfaces..."
        python3 interface_manager.py --discover || print_warning "Interface check failed"
    fi
    
    # Check performance baseline
    if [[ -f "performance_monitor.py" ]]; then
        print_status "Checking system performance baseline..."
        python3 performance_monitor.py --status || print_warning "Performance check failed"
    fi
}

# Setup development environment
setup_development() {
    print_status "Setting up development environment..."
    
    # Install development dependencies
    if [[ -f "requirements-dev.txt" ]]; then
        pip install -r requirements-dev.txt
    fi
    
    # Setup git hooks
    if [[ -d ".git" ]]; then
        print_status "Setting up git hooks..."
        mkdir -p .git/hooks
        
        # Pre-commit hook for validation
        cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
echo "Running pre-commit validation..."
python3 system_validator.py --quick --format text || exit 1
EOF
        chmod +x .git/hooks/pre-commit
    fi
    
    # Create development configuration
    if [[ ! -f ".env.development" ]]; then
        cp .env.example .env.development
        print_status "Created .env.development file"
    fi
    
    print_success "Development environment setup complete"
}

# Create start script
create_start_script() {
    print_status "Creating start script..."
    
    cat > start_wiguard.sh << 'EOF'
#!/bin/bash
# WiGuard Dashboard Start Script

# Change to script directory
cd "$(dirname "$0")"

# Check if virtual environment exists
if [[ ! -d "venv" ]]; then
    echo "Virtual environment not found. Please run setup.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if .env exists
if [[ ! -f ".env" ]]; then
    echo "Configuration file .env not found. Please run setup.sh first."
    exit 1
fi

# Start the Flask application
echo "Starting WiGuard Dashboard..."
python3 flaskkk.py
EOF
    
    chmod +x start_wiguard.sh
    print_success "Created start_wiguard.sh script"
}

# Enhanced main menu
main() {
    print_status "Starting WiGuard Dashboard setup..."
    print_status "======================================="
    
    # Change to script directory
    cd "$(dirname "$0")"
    
    check_root
    detect_os
    
    # Ask user what to install
    echo
    print_status "Choose installation type:"
    echo "1. Full installation (recommended)"
    echo "2. Minimal installation" 
    echo "3. Development setup"
    echo "4. System optimization only"
    echo "5. Docker setup"
    echo "6. Service installation (systemd)"
    echo "7. System validation only"
    echo "8. Exit"
    echo
    
    read -p "Enter your choice (1-8): " choice
    
    case $choice in
        1)
            print_status "Running full installation..."
            install_system_dependencies
            setup_python_env
            setup_configuration
            check_wireless_capabilities
            setup_database
            optimize_system
            run_system_check
            ;;
        2)
            print_status "Running minimal installation..."
            install_system_dependencies
            setup_python_env
            setup_configuration
            run_system_check
            ;;
        3)
            print_status "Setting up development environment..."
            install_system_dependencies
            setup_python_env
            setup_configuration
            setup_development
            run_system_check
            ;;
        4)
            print_status "Running system optimization..."
            check_root
            optimize_system
            ;;
        5)
            print_status "Setting up Docker environment..."
            if command -v docker >/dev/null 2>&1; then
                cd docker
                docker-compose -f docker-compose.multiplatform.yml up -d
                print_success "Docker services started"
            else
                print_error "Docker not found. Install Docker first."
                exit 1
            fi
            ;;
        6)
            print_status "Installing systemd services..."
            check_root
            if [[ -f "service_manager.sh" ]]; then
                chmod +x service_manager.sh
                ./service_manager.sh install
            else
                print_error "Service manager not found"
                exit 1
            fi
            ;;
        7)
            print_status "Running system validation..."
            run_system_check
            ;;
        8)
            print_status "Exiting..."
            exit 0
            ;;
        *)
            print_error "Invalid choice"
            exit 1
            ;;
    esac
    
    echo
    print_success "Setup completed!"
    print_status "======================================="
    
    # Run system validation
    print_status "Running system validation..."
    if [[ -f "system_validator.py" ]]; then
        python3 system_validator.py --quick || print_warning "System validation found issues"
    fi
    
    if [[ $choice -eq 1 ]] || [[ $choice -eq 2 ]]; then
        echo
        print_status "Next steps:"
        echo "1. Edit .env file to configure your settings"
        echo "2. Set up MySQL database (see init.sql)"
        echo "3. Run validation: python3 system_validator.py"
        echo "4. Start services: ./service_manager.sh start"
        echo "   Or run manually: ./start_wiguard.sh"
        echo
        print_status "For wireless monitoring, ensure your interface is in monitor mode:"
        echo "sudo airmon-ng start wlan0"
        echo "Or use: python3 interface_manager.py --create-monitor wlan0"
        echo
        print_status "Access the dashboard at: http://localhost:5053"
        echo
        print_status "New tools available:"
        echo "• System validation: python3 system_validator.py"
        echo "• Interface management: python3 interface_manager.py"
        echo "• Performance monitoring: python3 performance_monitor.py"
        echo "• Service management: ./service_manager.sh"
    fi
}

# Handle script interruption
trap 'echo; print_error "Setup interrupted"; exit 1' INT TERM

# Run main function
main "$@"
