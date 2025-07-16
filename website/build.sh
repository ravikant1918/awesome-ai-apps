#!/bin/bash

# Hugo Website Build Script
# This script helps manage the Hugo website build process

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WEBSITE_DIR="$SCRIPT_DIR"
ROOT_DIR="$(dirname "$WEBSITE_DIR")"
README_FILE="$ROOT_DIR/Readme.md"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    if ! command_exists hugo; then
        print_error "Hugo is not installed. Please install Hugo Extended v0.146.0 or higher."
        exit 1
    fi
    
    if ! command_exists python3; then
        print_error "Python 3 is not installed. Please install Python 3.11 or higher."
        exit 1
    fi
    
    # Check Hugo version
    HUGO_VERSION=$(hugo version | grep -oE 'v[0-9]+\.[0-9]+\.[0-9]+' | head -1)
    print_status "Hugo version: $HUGO_VERSION"
    
    # Check if README exists
    if [ ! -f "$README_FILE" ]; then
        print_error "README file not found at $README_FILE"
        exit 1
    fi
    
    print_status "Prerequisites check passed!"
}

# Function to generate content from README
generate_content() {
    print_status "Generating content from README.md..."
    
    cd "$WEBSITE_DIR"
    
    # Install Python dependencies if needed
    if ! python3 -c "import yaml" 2>/dev/null; then
        print_status "Installing Python dependencies..."
        pip3 install pyyaml
    fi
    
    # Run the content generation script
    python3 scripts/parse_readme.py --readme "$README_FILE" --output .
    
    print_status "Content generation completed!"
}

# Function to build the site
build_site() {
    print_status "Building Hugo site..."
    
    cd "$WEBSITE_DIR"
    
    # Build the site
    if [ "$1" = "production" ]; then
        hugo --minify --environment production
    else
        hugo --minify
    fi
    
    print_status "Site build completed!"
}

# Function to serve the site locally
serve_site() {
    print_status "Starting Hugo development server..."
    
    cd "$WEBSITE_DIR"
    
    # Start the server
    hugo server --bind 0.0.0.0 --port 1313 --disableFastRender
}

# Function to clean build artifacts
clean_build() {
    print_status "Cleaning build artifacts..."
    
    cd "$WEBSITE_DIR"
    
    # Remove public directory
    if [ -d "public" ]; then
        rm -rf public
        print_status "Removed public directory"
    fi
    
    # Remove Hugo cache
    if [ -d "resources" ]; then
        rm -rf resources
        print_status "Removed resources directory"
    fi
    
    print_status "Clean completed!"
}

# Function to show help
show_help() {
    cat << EOF
Hugo Website Build Script

Usage: $0 [COMMAND]

Commands:
  generate    Generate content from README.md
  build       Build the Hugo site
  serve       Start development server
  clean       Clean build artifacts
  deploy      Generate content and build for production
  help        Show this help message

Examples:
  $0 generate          # Generate content from README
  $0 build             # Build the site
  $0 serve             # Start development server
  $0 deploy            # Full build for production
  $0 clean             # Clean build artifacts

EOF
}

# Main script logic
main() {
    case "${1:-help}" in
        generate)
            check_prerequisites
            generate_content
            ;;
        build)
            check_prerequisites
            build_site
            ;;
        serve)
            check_prerequisites
            generate_content
            serve_site
            ;;
        clean)
            clean_build
            ;;
        deploy)
            check_prerequisites
            generate_content
            build_site production
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

# Run the main function
main "$@"