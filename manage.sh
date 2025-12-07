#!/bin/bash
# Podcast Manager Service Management Script

SERVICE_BACKEND="podcast-manager-backend"
SERVICE_FRONTEND="podcast-manager-frontend-dev"

show_usage() {
    echo "Podcast Manager - Service Management"
    echo
    echo "Usage: sudo ./manage.sh [command]"
    echo
    echo "Commands:"
    echo "  start           Start all services"
    echo "  stop            Stop all services"
    echo "  restart         Restart all services"
    echo "  status          Show status of all services"
    echo "  logs            Show logs (press Ctrl+C to exit)"
    echo "  logs-backend    Show backend logs only"
    echo "  logs-frontend   Show frontend logs only"
    echo "  enable          Enable services to start on boot"
    echo "  disable         Disable services from starting on boot"
    echo "  build-frontend  Build frontend for production"
    echo "  test-backend    Test backend manually"
    echo
}

check_root() {
    if [ "$EUID" -ne 0 ]; then
        echo "Error: Please run as root (sudo)"
        exit 1
    fi
}

start_services() {
    echo "Starting services..."
    systemctl start $SERVICE_BACKEND
    if systemctl is-enabled $SERVICE_FRONTEND &>/dev/null; then
        systemctl start $SERVICE_FRONTEND
    fi
    echo "Done!"
    show_status
}

stop_services() {
    echo "Stopping services..."
    systemctl stop $SERVICE_BACKEND
    if systemctl is-active $SERVICE_FRONTEND &>/dev/null; then
        systemctl stop $SERVICE_FRONTEND
    fi
    echo "Done!"
}

restart_services() {
    echo "Restarting services..."
    systemctl restart $SERVICE_BACKEND
    if systemctl is-active $SERVICE_FRONTEND &>/dev/null; then
        systemctl restart $SERVICE_FRONTEND
    fi
    echo "Done!"
    show_status
}

show_status() {
    echo
    echo "=== Backend Service ==="
    systemctl status $SERVICE_BACKEND --no-pager -l
    echo
    if systemctl is-enabled $SERVICE_FRONTEND &>/dev/null; then
        echo "=== Frontend Service ==="
        systemctl status $SERVICE_FRONTEND --no-pager -l
        echo
    fi
}

show_logs() {
    echo "Showing logs (Ctrl+C to exit)..."
    echo
    if systemctl is-enabled $SERVICE_FRONTEND &>/dev/null; then
        journalctl -u $SERVICE_BACKEND -u $SERVICE_FRONTEND -f
    else
        journalctl -u $SERVICE_BACKEND -f
    fi
}

show_backend_logs() {
    echo "Showing backend logs (Ctrl+C to exit)..."
    echo
    journalctl -u $SERVICE_BACKEND -f
}

show_frontend_logs() {
    echo "Showing frontend logs (Ctrl+C to exit)..."
    echo
    journalctl -u $SERVICE_FRONTEND -f
}

enable_services() {
    echo "Enabling services to start on boot..."
    systemctl enable $SERVICE_BACKEND
    if systemctl is-enabled $SERVICE_FRONTEND &>/dev/null; then
        systemctl enable $SERVICE_FRONTEND
    fi
    echo "Done!"
}

disable_services() {
    echo "Disabling services from starting on boot..."
    systemctl disable $SERVICE_BACKEND
    if systemctl is-enabled $SERVICE_FRONTEND &>/dev/null; then
        systemctl disable $SERVICE_FRONTEND
    fi
    echo "Done!"
}

build_frontend() {
    echo "Building frontend..."
    cd /opt/podcast-manager/frontend || exit 1
    sudo -u podcastmgr npm run build
    echo "Done! Frontend built to dist/"
    echo
    echo "If using nginx, restart it:"
    echo "  sudo systemctl restart nginx"
}

test_backend() {
    echo "Testing backend manually..."
    echo "Press Ctrl+C to stop"
    echo
    cd /opt/podcast-manager || exit 1
    sudo -u podcastmgr bash -c "source venv/bin/activate && uvicorn podcastmanager.main:app --host 0.0.0.0 --port 8000"
}

# Main script
case "$1" in
    start)
        check_root
        start_services
        ;;
    stop)
        check_root
        stop_services
        ;;
    restart)
        check_root
        restart_services
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    logs-backend)
        show_backend_logs
        ;;
    logs-frontend)
        show_frontend_logs
        ;;
    enable)
        check_root
        enable_services
        ;;
    disable)
        check_root
        disable_services
        ;;
    build-frontend)
        check_root
        build_frontend
        ;;
    test-backend)
        check_root
        test_backend
        ;;
    *)
        show_usage
        ;;
esac
