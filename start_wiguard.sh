#!/bin/bash
"""
Enhanced WiGuard Dashboard Startup Script
Includes validation, interface management, and monitoring
"""

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
DASHBOARD_PORT=${FLASK_PORT:-5053}
DASHBOARD_HOST=${FLASK_HOST:-127.0.0.1}
INTERFACE_CHECK=${INTERFACE_CHECK:-true}
PERFORMANCE_MONITOR=${PERFORMANCE_MONITOR:-false}
VALIDATION_CHECK=${VALIDATION_CHECK:-true}

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

# Cleanup function
cleanup() {
    print_status "Cleaning up..."
    if [[ -n "$DASHBOARD_PID" ]]; then
        kill $DASHBOARD_PID 2>/dev/null || true
    fi
    if [[ -n "$MONITOR_PID" ]]; then
        kill $MONITOR_PID 2>/dev/null || true
    fi
    if [[ -n "$PERFORMANCE_PID" ]]; then
        kill $PERFORMANCE_PID 2>/dev/null || true
    fi
    exit 0
}

trap cleanup SIGINT SIGTERM

# Pre-flight checks
pre_flight_checks() {
    print_status "Running pre-flight checks..."
    
    # Check if we're in the right directory
    if [[ ! -f "flaskkk.py" ]]; then
        print_error "flaskkk.py not found. Are you in the correct directory?"
        exit 1
    fi
    
    # Activate virtual environment if available
    if [[ -d "venv" ]]; then
        print_status "Activating virtual environment..."
        source venv/bin/activate
    fi
    
    # Run system validation if enabled
    if [[ "$VALIDATION_CHECK" == "true" && -f "system_validator.py" ]]; then
        print_status "Running system validation..."
        if ! python3 system_validator.py --quick >/dev/null 2>&1; then
            print_warning "System validation found issues. Continue anyway? (y/N)"
            read -r response
            if [[ ! "$response" =~ ^[Yy]$ ]]; then
                exit 1
            fi
        else
            print_success "System validation passed"
        fi
    fi
    
    # Check network interfaces if enabled
    if [[ "$INTERFACE_CHECK" == "true" && -f "interface_manager.py" ]]; then
        print_status "Checking network interfaces..."
        if python3 interface_manager.py --discover --json > /tmp/wiguard-interfaces.json 2>/dev/null; then
            wireless_count=$(python3 -c "import json; data=json.load(open('/tmp/wiguard-interfaces.json')); print(sum(1 for info in data['interfaces'].values() if info['type'] == 'wireless'))" 2>/dev/null || echo "0")
            monitor_count=$(python3 -c "import json; data=json.load(open('/tmp/wiguard-interfaces.json')); print(sum(1 for info in data['interfaces'].values() if info['monitor_capable']))" 2>/dev/null || echo "0")
            
            print_success "Found $wireless_count wireless interface(s), $monitor_count monitor-capable"
            
            if [[ "$monitor_count" -eq 0 && "$wireless_count" -gt 0 ]]; then
                print_warning "No monitor-capable interfaces found. Wireless monitoring will be limited."
                print_status "You can create a monitor interface with: python3 interface_manager.py --create-monitor wlan0"
            fi
        else
            print_warning "Interface check failed"
        fi
    fi
    
    # Check if ports are available
    if netstat -tuln 2>/dev/null | grep -q ":$DASHBOARD_PORT "; then
        print_error "Port $DASHBOARD_PORT is already in use"
        print_status "You can change the port by setting FLASK_PORT environment variable"
        exit 1
    fi
    
    print_success "Pre-flight checks completed"
}

# Start performance monitoring if enabled
start_performance_monitor() {
    if [[ "$PERFORMANCE_MONITOR" == "true" && -f "performance_monitor.py" ]]; then
        print_status "Starting performance monitoring..."
        python3 performance_monitor.py --monitor 30 > logs/performance.log 2>&1 &
        PERFORMANCE_PID=$!
        print_success "Performance monitoring started (PID: $PERFORMANCE_PID)"
    fi
}

# Start the dashboard
start_dashboard() {
    print_status "Starting WiGuard Dashboard..."
    print_status "Host: $DASHBOARD_HOST"
    print_status "Port: $DASHBOARD_PORT"
    print_status "Dashboard URL: http://$DASHBOARD_HOST:$DASHBOARD_PORT"
    
    # Create logs directory if it doesn't exist
    mkdir -p logs
    
    # Check if we should use gunicorn or flask directly
    if command -v gunicorn >/dev/null 2>&1 && [[ -f "gunicorn.conf.py" ]]; then
        print_status "Starting with Gunicorn (production mode)..."
        gunicorn --config gunicorn.conf.py flaskkk:app &
        DASHBOARD_PID=$!
    else
        print_status "Starting with Flask development server..."
        python3 flaskkk.py &
        DASHBOARD_PID=$!
    fi
    
    print_success "Dashboard started (PID: $DASHBOARD_PID)"
    
    # Wait a moment for the server to start
    sleep 3
    
    # Test if the server is responding
    if curl -s -f "http://$DASHBOARD_HOST:$DASHBOARD_PORT/api/ping" >/dev/null 2>&1; then
        print_success "Dashboard is responding to requests"
    else
        print_warning "Dashboard may not be responding correctly"
    fi
}

# Show system status
show_status() {
    print_status "WiGuard Dashboard Status:"
    echo "=========================="
    echo "Dashboard URL: http://$DASHBOARD_HOST:$DASHBOARD_PORT"
    echo "Dashboard PID: ${DASHBOARD_PID:-Not running}"
    echo "Monitor PID: ${MONITOR_PID:-Not running}"
    echo "Performance PID: ${PERFORMANCE_PID:-Not running}"
    echo
    
    # Show interface status if available
    if [[ -f "/tmp/wiguard-interfaces.json" ]]; then
        print_status "Network Interfaces:"
        python3 -c "
import json
try:
    with open('/tmp/wiguard-interfaces.json') as f:
        data = json.load(f)
    for name, info in data['interfaces'].items():
        status = 'UP' if info['state'] == 'up' else 'DOWN'
        caps = []
        if info.get('monitor_capable'): caps.append('monitor')
        if info.get('injection_capable'): caps.append('injection')
        cap_str = '(' + ','.join(caps) + ')' if caps else ''
        print(f'  {name}: {info[\"type\"]} [{status}] {cap_str}')
except:
    print('  Interface information unavailable')
"
        echo
    fi
    
    # Show recent alerts if performance monitoring is enabled
    if [[ -f "logs/performance.log" ]]; then
        print_status "Recent Performance Alerts:"
        tail -n 5 logs/performance.log 2>/dev/null | grep -i "alert" || echo "  No recent alerts"
        echo
    fi
    
    print_status "Logs available in: logs/"
    print_status "Press Ctrl+C to stop all services"
}

# Monitor logs in the background
monitor_logs() {
    if [[ -f "logs/app.log" ]]; then
        tail -f logs/app.log &
    fi
}

# Main execution
main() {
    print_status "Starting WiGuard Dashboard..."
    print_status "==============================="
    
    # Run pre-flight checks
    pre_flight_checks
    
    # Start performance monitoring if enabled
    start_performance_monitor
    
    # Start the main dashboard
    start_dashboard
    
    # Show status
    show_status
    
    # Monitor in foreground
    if [[ "${1:-}" == "--daemon" ]]; then
        print_status "Running in daemon mode"
        wait
    else
        print_status "Running in interactive mode. Monitoring logs..."
        print_status "Access dashboard at: http://$DASHBOARD_HOST:$DASHBOARD_PORT"
        echo
        
        # Wait for processes
        wait
    fi
}

# Handle command line arguments
case "${1:-}" in
    "--help"|"-h")
        cat << EOF
WiGuard Dashboard Startup Script

Usage: $0 [options]

Options:
    --daemon        Run in daemon mode (background)
    --help, -h      Show this help message

Environment Variables:
    FLASK_HOST      Dashboard host (default: 127.0.0.1)
    FLASK_PORT      Dashboard port (default: 5053)
    INTERFACE_CHECK Check interfaces on startup (default: true)
    PERFORMANCE_MONITOR  Enable performance monitoring (default: false)
    VALIDATION_CHECK     Run validation checks (default: true)

Examples:
    $0                          # Start in interactive mode
    $0 --daemon                 # Start in daemon mode
    FLASK_PORT=8080 $0          # Start on port 8080
    PERFORMANCE_MONITOR=true $0 # Start with performance monitoring

EOF
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac
