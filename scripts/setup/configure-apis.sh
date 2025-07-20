#!/bin/bash
# API Keys and Configuration Setup Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC    # Get script directory and project root
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
    
    print_info "Script directory: $SCRIPT_DIR"
    print_info "Project root: $PROJECT_ROOT"
    
    # Change to project root
    cd "$PROJECT_ROOT"
    
    # Verify we're in the right place
    if [ ! -f "pyproject.toml" ]; then
        print_error "Not in project root directory (pyproject.toml not found)"
        print_error "Current directory: $(pwd)"
        exit 1
    fi[0m' # No Color

# Function to print colored output
print_info() {
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

print_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

# Function to prompt for input with default value
prompt_input() {
    local prompt="$1"
    local default="$2"
    local var_name="$3"
    local sensitive="${4:-false}"
    
    if [ "$sensitive" = "true" ]; then
        echo -n -e "${BLUE}$prompt${NC}"
        if [ -n "$default" ]; then
            echo -n " (current: ***hidden***)"
        fi
        echo -n ": "
        read -s input
        echo
    else
        echo -n -e "${BLUE}$prompt${NC}"
        if [ -n "$default" ]; then
            echo -n " (current: $default)"
        fi
        echo -n ": "
        read input
    fi
    
    if [ -z "$input" ] && [ -n "$default" ]; then
        input="$default"
    fi
    
    eval "$var_name='$input'"
}

# Function to validate API key format
validate_openai_key() {
    local key="$1"
    if [[ "$key" =~ ^sk-[a-zA-Z0-9]{48,}$ ]]; then
        return 0
    else
        return 1
    fi
}

# Function to test OpenAI API key
test_openai_key() {
    local key="$1"
    print_info "Testing OpenAI API key..."
    
    response=$(curl -s -w "%{http_code}" -o /tmp/openai_test.json \
        -H "Authorization: Bearer $key" \
        -H "Content-Type: application/json" \
        "https://api.openai.com/v1/models")
    
    if [ "$response" = "200" ]; then
        print_success "OpenAI API key is valid!"
        return 0
    else
        print_error "OpenAI API key test failed (HTTP $response)"
        if [ -f /tmp/openai_test.json ]; then
            cat /tmp/openai_test.json
        fi
        return 1
    fi
}

# Function to setup Google Drive API
setup_google_drive() {
    print_step "Setting up Google Drive API"
    echo
    echo "To set up Google Drive API, you need to:"
    echo "1. Go to Google Cloud Console (https://console.cloud.google.com/)"
    echo "2. Create a new project or select existing one"
    echo "3. Enable Google Drive API"
    echo "4. Create credentials (OAuth 2.0 Client ID or Service Account)"
    echo "5. Download the credentials JSON file"
    echo
    
    prompt_input "Path to Google Drive credentials JSON file" "$CURRENT_GOOGLE_CREDENTIALS" "google_credentials_path"
    prompt_input "Path to store Google Drive token file" "$CURRENT_GOOGLE_TOKEN" "google_token_path"
    
    # Create directories if they don't exist
    if [ -n "$google_credentials_path" ]; then
        mkdir -p "$(dirname "$google_credentials_path")"
    fi
    if [ -n "$google_token_path" ]; then
        mkdir -p "$(dirname "$google_token_path")"
    fi
    
    # Validate credentials file exists
    if [ -n "$google_credentials_path" ] && [ ! -f "$google_credentials_path" ]; then
        print_warning "Credentials file not found: $google_credentials_path"
        print_info "Make sure to download and place your Google credentials file there"
    fi
}

# Function to setup database
setup_database() {
    print_step "Setting up Database Configuration"
    echo
    echo "Choose your database type:"
    echo "1. SQLite (simple, local file - recommended for development)"
    echo "2. PostgreSQL (production-ready)"
    echo "3. MySQL (alternative production option)"
    echo
    
    read -p "Select database type (1-3): " db_choice
    
    case $db_choice in
        1)
            database_url="sqlite+aiosqlite:///./data/agent.db"
            print_info "Using SQLite database: ./data/agent.db"
            mkdir -p ./data
            ;;
        2)
            prompt_input "PostgreSQL host" "localhost" "pg_host"
            prompt_input "PostgreSQL port" "5432" "pg_port"
            prompt_input "PostgreSQL database name" "intelligent_agent" "pg_db"
            prompt_input "PostgreSQL username" "postgres" "pg_user"
            prompt_input "PostgreSQL password" "" "pg_password" true
            database_url="postgresql+asyncpg://$pg_user:$pg_password@$pg_host:$pg_port/$pg_db"
            ;;
        3)
            prompt_input "MySQL host" "localhost" "mysql_host"
            prompt_input "MySQL port" "3306" "mysql_port"
            prompt_input "MySQL database name" "intelligent_agent" "mysql_db"
            prompt_input "MySQL username" "root" "mysql_user"
            prompt_input "MySQL password" "" "mysql_password" true
            database_url="mysql+aiomysql://$mysql_user:$mysql_password@$mysql_host:$mysql_port/$mysql_db"
            ;;
        *)
            print_error "Invalid choice"
            database_url="sqlite+aiosqlite:///./data/agent.db"
            ;;
    esac
}

# Function to generate secure secret key
generate_secret_key() {
    python3 -c "import secrets; print(secrets.token_urlsafe(32))"
}

# Main setup function
main() {
    echo -e "${GREEN}🚀 Intelligent Agent API Keys Setup${NC}"
    echo "================================================"
    echo
    
    # Get script directory and project root
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
    
    # Change to project root
    cd "$PROJECT_ROOT"
    
    # Check if .env file exists
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            print_info "Creating .env file from example..."
            cp .env.example .env
        else
            print_error ".env.example file not found!"
            exit 1
        fi
    fi
    
    # Read current values
    source .env 2>/dev/null || true
    CURRENT_OPENAI_KEY="$OPENAI_API_KEY"
    CURRENT_GOOGLE_CREDENTIALS="$GOOGLE_DRIVE_CREDENTIALS_FILE"
    CURRENT_GOOGLE_TOKEN="$GOOGLE_DRIVE_TOKEN_FILE"
    CURRENT_DATABASE_URL="$DATABASE_URL"
    CURRENT_SECRET_KEY="$SECRET_KEY"
    
    echo "Current configuration status:"
    echo "- OpenAI API Key: $([ "$CURRENT_OPENAI_KEY" != "your_openai_api_key_here" ] && echo "✅ Set" || echo "❌ Not set")"
    echo "- Google Drive: $([ "$CURRENT_GOOGLE_CREDENTIALS" != "path/to/credentials.json" ] && echo "✅ Configured" || echo "❌ Not configured")"
    echo "- Database: $([ "$CURRENT_DATABASE_URL" != "postgresql+asyncpg://user:password@localhost:5432/dbname" ] && echo "✅ Configured" || echo "❌ Default")"
    echo "- Secret Key: $([ "$CURRENT_SECRET_KEY" != "your_secret_key_here" ] && echo "✅ Set" || echo "❌ Default")"
    echo
    
    # Setup OpenAI API Key
    print_step "Setting up OpenAI API Key"
    echo
    echo "Get your OpenAI API key from: https://platform.openai.com/api-keys"
    echo
    
    prompt_input "OpenAI API Key" "$CURRENT_OPENAI_KEY" "openai_api_key" true
    
    if [ -n "$openai_api_key" ] && [ "$openai_api_key" != "your_openai_api_key_here" ]; then
        if validate_openai_key "$openai_api_key"; then
            if test_openai_key "$openai_api_key"; then
                print_success "OpenAI API key validated successfully!"
            else
                print_warning "OpenAI API key validation failed, but continuing..."
            fi
        else
            print_warning "OpenAI API key format seems invalid (should start with 'sk-')"
        fi
    fi
    
    # Setup Database
    setup_database
    
    # Setup Google Drive
    setup_google_drive
    
    # Generate secret key if needed
    if [ "$CURRENT_SECRET_KEY" = "your_secret_key_here" ] || [ -z "$CURRENT_SECRET_KEY" ]; then
        print_step "Generating secure secret key..."
        secret_key=$(generate_secret_key)
        print_success "Generated new secret key"
    else
        secret_key="$CURRENT_SECRET_KEY"
    fi
    
    # Optional services
    print_step "Optional Services Setup"
    echo
    echo "The following services are optional and can be configured later:"
    echo
    
    read -p "Do you want to configure Notion API? (y/N): " setup_notion
    if [[ "$setup_notion" =~ ^[Yy]$ ]]; then
        echo "Get your Notion API token from: https://www.notion.so/my-integrations"
        prompt_input "Notion API Token" "" "notion_api_token" true
        prompt_input "Notion Workspace ID (optional)" "" "notion_workspace_id"
    fi
    
    read -p "Do you want to configure Slack API? (y/N): " setup_slack
    if [[ "$setup_slack" =~ ^[Yy]$ ]]; then
        echo "Create a Slack app at: https://api.slack.com/apps"
        prompt_input "Slack Bot Token" "" "slack_bot_token" true
        prompt_input "Slack Signing Secret" "" "slack_signing_secret" true
        prompt_input "Slack App Token" "" "slack_app_token" true
    fi
    
    # Update .env file
    print_step "Updating .env file..."
    
    # Create backup
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
    
    # Update values
    sed -i.tmp "s|^OPENAI_API_KEY=.*|OPENAI_API_KEY=$openai_api_key|" .env
    sed -i.tmp "s|^DATABASE_URL=.*|DATABASE_URL=$database_url|" .env
    sed -i.tmp "s|^SECRET_KEY=.*|SECRET_KEY=$secret_key|" .env
    
    if [ -n "$google_credentials_path" ]; then
        sed -i.tmp "s|^GOOGLE_DRIVE_CREDENTIALS_FILE=.*|GOOGLE_DRIVE_CREDENTIALS_FILE=$google_credentials_path|" .env
    fi
    if [ -n "$google_token_path" ]; then
        sed -i.tmp "s|^GOOGLE_DRIVE_TOKEN_FILE=.*|GOOGLE_DRIVE_TOKEN_FILE=$google_token_path|" .env
    fi
    
    if [ -n "$notion_api_token" ]; then
        sed -i.tmp "s|^NOTION_API_TOKEN=.*|NOTION_API_TOKEN=$notion_api_token|" .env
        sed -i.tmp "s|^ENABLE_NOTION_TOOL=.*|ENABLE_NOTION_TOOL=true|" .env
    fi
    
    if [ -n "$slack_bot_token" ]; then
        sed -i.tmp "s|^SLACK_BOT_TOKEN=.*|SLACK_BOT_TOKEN=$slack_bot_token|" .env
        sed -i.tmp "s|^ENABLE_SLACK_TOOL=.*|ENABLE_SLACK_TOOL=true|" .env
    fi
    
    # Clean up temp files
    rm -f .env.tmp
    
    print_success "Configuration updated successfully!"
    echo
    
    # Show next steps
    print_step "Next Steps"
    echo
    echo "1. Test your configuration:"
    echo "   make run-simple"
    echo
    echo "2. Test API endpoints:"
    echo "   curl http://localhost:8000/health"
    echo
    echo "3. View API documentation:"
    echo "   http://localhost:8000/docs"
    echo
    echo "4. Test CLI tool:"
    echo "   poetry run python cli.py \"Create a test summary\""
    echo
    
    if [ -n "$google_credentials_path" ] && [ ! -f "$google_credentials_path" ]; then
        print_warning "Remember to download and place your Google Drive credentials file at:"
        echo "   $google_credentials_path"
        echo
    fi
    
    print_success "Setup complete! 🎉"
}

# Run main function
main "$@"
