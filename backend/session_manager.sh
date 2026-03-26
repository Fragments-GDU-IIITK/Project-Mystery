#!/usr/bin/env bash

set -euo pipefail

BASE_URL="http://localhost:3000/project_mystery_backend/0.1.0/sessions"
SESSION_NAME="test_session"
SESSION_ID="Oq_AZ99Zh7RZEtEP"

print_usage() {
    echo "Usage: $0 [--create_session | --load_session | --unload_session | --reset_session]"
    exit 1
}

create_session() {
    echo "Creating session..."
    curl -s -X POST "$BASE_URL/" \
        -H "Content-Type: application/json" \
        -d "{\"session_name\": \"$SESSION_NAME\"}"
    echo -e "\nDone."
}

load_session() {
    echo "Loading session..."
    curl -s -X POST "$BASE_URL/$SESSION_ID/load"
    echo -e "\nDone."
}

unload_session() {
    echo "Unloading session..."
    curl -s -X POST "$BASE_URL/unload"
    echo -e "\nDone."
}

reset_session() {
    echo "Resetting session..."
    curl -s -X POST "$BASE_URL/$SESSION_ID/reset"
    echo -e "\nDone."
}

# Ensure at least one argument is passed
if [[ $# -eq 0 ]]; then
    print_usage
fi

# Parse flags
case "$1" in
    --create_session)
        create_session
        ;;
    --load_session)
        load_session
        ;;
    --unload_session)
        unload_session
        ;;
    --reset_session)
        reset_session
        ;;
    *)
        print_usage
        ;;
esac