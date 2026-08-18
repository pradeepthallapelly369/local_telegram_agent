#!/bin/bash
# Launch Claude Code using the local OmniRoute server

export ANTHROPIC_BASE_URL="http://localhost:20128"
export ANTHROPIC_API_KEY="sk-no-key-required"
export ANTHROPIC_AUTH_TOKEN="sk-no-key-required"

echo "Starting Claude Code routed through OmniRoute..."
claude "$@"
