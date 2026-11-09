#!/bin/bash

# Startup script for DAAV with Docker Compose

set -e

echo "🚀 Starting DAAV with Docker Compose"
echo "===================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed"
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f "backendApi/.env" ]; then
    echo "📝 Creating .env file for backend..."
    cp backendApi/.env.example backendApi/.env
    echo "✅ .env file created. You can modify it if needed."
fi

# Function to display options
show_menu() {
    echo ""
    echo "Choose an option:"
    echo "1) Start all services"
    echo "2) Start with Mongo Express (administration interface)"
    echo "3) Stop all services"
    echo "4) Rebuild and restart"
    echo "5) View logs"
    echo "6) View service status"
    echo "7) Clean up (removes volumes - WARNING)"
    echo "8) Exit"
}

# Function to start services
start_services() {
    echo "🔄 Starting services..."
    docker-compose up -d
    echo "✅ Services started!"
    echo ""
    echo "🌐 Service access:"
    echo "   - Frontend: http://localhost:8080"
    echo "   - Backend:  http://localhost:8081"
}

# Function to start with Mongo Express
start_with_admin() {
    echo "🔄 Starting services with Mongo Express..."
    docker-compose --profile admin up -d
    echo "✅ Services started with administration interface!"
    echo ""
    echo "🌐 Service access:"
    echo "   - Frontend:      http://localhost:8080"
    echo "   - Backend:       http://localhost:8081"
    echo "   - Mongo Express: http://localhost:8083 (admin/admin123)"
}

# Function to stop services
stop_services() {
    echo "⏹️ Stopping services..."
    docker-compose down
    echo "✅ Services stopped!"
}

# Function to rebuild
rebuild_services() {
    echo "🔨 Rebuilding and restarting..."
    docker-compose down
    docker-compose build --no-cache
    docker-compose up -d
    echo "✅ Services rebuilt and restarted!"
}

# Function to view logs
show_logs() {
    echo "📋 Service logs (Ctrl+C to exit)..."
    docker-compose logs -f
}

# Function to view status
show_status() {
    echo "📊 Service status:"
    docker-compose ps
}

# Function to clean up
clean_all() {
    echo "⚠️  WARNING: This action will delete all data!"
    read -p "Are you sure? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🧹 Cleaning up..."
        docker-compose down -v
        docker system prune -f
        echo "✅ Cleanup completed!"
    else
        echo "❌ Cleanup cancelled"
    fi
}

# Main loop
while true; do
    show_menu
    read -p "Your choice (1-8): " choice
    
    case $choice in
        1)
            start_services
            ;;
        2)
            start_with_admin
            ;;
        3)
            stop_services
            ;;
        4)
            rebuild_services
            ;;
        5)
            show_logs
            ;;
        6)
            show_status
            ;;
        7)
            clean_all
            ;;
        8)
            echo "👋 Goodbye!"
            exit 0
            ;;
        *)
            echo "❌ Invalid option"
            ;;
    esac
    
    echo ""
    read -p "Press Enter to continue..."
done
