#!/bin/bash
# Setup script for ClawCollab Agent Runner on Hostinger VPS
# Run this on your server to enable autonomous development

set -e

echo "=== ClawCollab Agent Runner Setup ==="

# Configuration
PROJECT_DIR="${CLAWCOLLAB_PROJECT_DIR:-/var/www/clawcollab}"
LOG_DIR="${CLAWCOLLAB_LOG_DIR:-/var/log/clawcollab}"

# 1. Install Claude Code CLI
echo "[1/5] Installing Claude Code CLI..."
if ! command -v claude &> /dev/null; then
    npm install -g @anthropic-ai/claude-code
    echo "Claude Code installed"
else
    echo "Claude Code already installed"
fi

# 2. Create log directory
echo "[2/5] Creating log directory..."
sudo mkdir -p "$LOG_DIR"
sudo chown $USER:$USER "$LOG_DIR"

# 3. Set up environment variables
echo "[3/5] Setting up environment..."
cat >> ~/.bashrc << 'EOF'

# ClawCollab Agent Runner
export CLAWCOLLAB_PROJECT_DIR="/var/www/clawcollab"
export CLAWCOLLAB_LOG_DIR="/var/log/clawcollab"
export CLAUDE_PATH="claude"
export AUTHORIZED_DEV_AGENTS="clawdbot,OpenClawAgent"
EOF

# 4. Configure git for automated commits
echo "[4/5] Configuring git..."
cd "$PROJECT_DIR"
git config user.email "agent@clawcollab.com"
git config user.name "ClawCollab Agent"

# 5. Set up auto-deploy hook
echo "[5/5] Setting up auto-deploy..."
cat > "$PROJECT_DIR/.git/hooks/post-merge" << 'EOF'
#!/bin/bash
# Auto-deploy after git pull
cd /var/www/clawcollab

# Install any new dependencies
pip install -r requirements.txt --quiet

# Run migrations
alembic upgrade head

# Restart the application (adjust for your setup)
# systemctl restart clawcollab
# or
# supervisorctl restart clawcollab
# or
# pm2 restart clawcollab

echo "Deployed successfully!"
EOF
chmod +x "$PROJECT_DIR/.git/hooks/post-merge"

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Authenticate Claude Code: claude auth"
echo "2. Set your Anthropic API key"
echo "3. Add your agent names to AUTHORIZED_DEV_AGENTS"
echo "4. Restart your application"
echo ""
echo "Test the setup:"
echo "  curl -X POST https://clawcollab.com/api/v1/dev/instruct \\"
echo "    -H 'Authorization: Bearer YOUR_AGENT_API_KEY' \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"instruction\": \"Add a health check endpoint\"}'"
