#!/bin/bash

echo "Setting up Talisman pre-commit hook..."

# Remove any existing pre-commit hooks and old emoji replacement script
if [ -f .git/hooks/pre-commit ]; then
    echo "Removing existing pre-commit hook..."
    rm .git/hooks/pre-commit
fi

if [ -f precommithook-Replace-emoji.py ]; then
    echo "Removing old emoji replacement pre-commit hook..."
    rm precommithook-Replace-emoji.py
fi

# Download and install Talisman
echo "Downloading Talisman..."
curl --silent https://raw.githubusercontent.com/thoughtworks/talisman/main/global_install_scripts/install.bash > /tmp/install_talisman.bash

# Make it executable and run
chmod +x /tmp/install_talisman.bash

# Install Talisman as pre-commit hook
echo "Installing Talisman as pre-commit hook..."
/tmp/install_talisman.bash pre-commit

# Create Talisman configuration file
echo "Creating Talisman configuration..."
cat > .talismanrc << 'EOF'
# Talisman configuration file
# https://github.com/thoughtworks/talisman

# File patterns to ignore
fileignoreconfig:
- filename: .env.example
  checksum: # Will be auto-generated
- filename: transcriptions/README.md
  checksum: # Will be auto-generated
- filename: docs/log_training.md
  checksum: # Will be auto-generated (already redacted)

# Allowed patterns (for legitimate use cases)
allowed_patterns:
- "REDACTED"  # Allow the word REDACTED in files
- "hf_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"  # Allow redacted token format

# Custom detectors to disable if needed
# custom_patterns:
# - pattern: "custom_regex_pattern"
#   reason: "Why this pattern should be ignored"

# Severity levels: low, medium, high
threshold: medium

# Scan options
scan_hidden_files: false
EOF

# Create .talismanignore for files that should be completely ignored
cat > .talismanignore << 'EOF'
# Files to completely ignore from Talisman scanning
.env.example
*.pyc
__pycache__/
.git/
.venv/
node_modules/
*.log
EOF

# Update .gitignore to include Talisman files
echo "" >> .gitignore
echo "# Talisman" >> .gitignore
echo ".talismanrc" >> .gitignore
echo ".talismanignore" >> .gitignore

# Clean up
rm /tmp/install_talisman.bash

echo "Talisman setup completed!"
echo ""
echo "Configuration files created:"
echo "- .talismanrc (Talisman configuration)"
echo "- .talismanignore (Files to ignore)"
echo ""
echo "Talisman will now scan for secrets on every commit."
echo "To test it, try: git add . && git commit -m 'test'"
echo ""
echo "Useful Talisman commands:"
echo "- Skip Talisman for a commit: TALISMAN_UNSAFE_SKIP=true git commit -m 'message'"
echo "- Update checksums: talisman --githook pre-commit --scan"
echo "- Check current status: talisman --githook pre-commit"