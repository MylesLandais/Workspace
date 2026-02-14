#!/bin/bash

echo "EMERGENCY CLEANUP: Removing sensitive information disclosure"
echo "========================================================="

# Step 1: Remove the sensitive file from git tracking
echo "1. Removing docs/log_training.md from git tracking..."
git rm --cached docs/log_training.md 2>/dev/null || echo "File not in git index"

# Step 2: Move the file to a hidden local copy
echo "2. Making file hidden and local-only..."
if [ -f docs/log_training.md ]; then
    mv docs/log_training.md docs/.log_training.md.local
    echo "   Moved to docs/.log_training.md.local (hidden, local-only)"
fi

# Step 3: Add to .gitignore to prevent future commits
echo "3. Adding to .gitignore..."
cat >> .gitignore << 'EOF'

# Local training logs (contains sensitive information)
docs/.log_training.md.local
docs/log_training.md
**/log_training.md
**/.log_training.md.local

EOF

# Step 4: Create a safe template for future use
echo "4. Creating safe template..."
cat > docs/log_training_template.md << 'EOF'
# Training Log Template

## Date: [DATE]

### Environment Setup
- Model: [MODEL_NAME]
- Dataset: [DATASET_NAME] 
- Configuration: [CONFIG_DETAILS]

### Training Notes
- [TRAINING_NOTES]
- [OBSERVATIONS]

### Results
- [METRICS]
- [PERFORMANCE_NOTES]

## Important Notes:
- This file should be copied to .log_training.md.local for actual use
- Never commit actual training logs with sensitive information
- Use placeholder values like [REDACTED] for sensitive data
EOF

# Step 5: Completely rewrite git history to remove all traces
echo "5. Preparing to rewrite git history..."
echo "   WARNING: This will remove ALL traces of the sensitive file from git history"
echo "   Creating backup first..."

# Create backup
cp -r .git .git.emergency_backup

echo "6. Rewriting git history to remove sensitive file..."
git filter-branch --force --index-filter \
    'git rm --cached --ignore-unmatch docs/log_training.md' \
    --prune-empty --tag-name-filter cat -- --all

# Clean up git
echo "7. Cleaning up git references..."
rm -rf .git/refs/original/
git reflog expire --expire=now --all
git gc --prune=now --aggressive

echo ""
echo "EMERGENCY CLEANUP COMPLETED!"
echo "=========================="
echo ""
echo "Actions taken:"
echo "✓ Removed docs/log_training.md from git tracking"
echo "✓ Moved to hidden local file: docs/.log_training.md.local"
echo "✓ Added comprehensive .gitignore rules"
echo "✓ Created safe template: docs/log_training_template.md"
echo "✓ Rewrote git history to remove all traces"
echo "✓ Created backup at: .git.emergency_backup"
echo ""
echo "NEXT STEPS:"
echo "1. Review changes: git status"
echo "2. Commit the cleanup: git add . && git commit -m 'Emergency cleanup: remove sensitive training logs'"
echo "3. Force push to overwrite remote: git push --force-with-lease origin master"
echo ""
echo "IMPORTANT:"
echo "- The sensitive file is now at docs/.log_training.md.local (local only)"
echo "- Use docs/log_training_template.md for future training logs"
echo "- Never commit actual training logs with sensitive information"