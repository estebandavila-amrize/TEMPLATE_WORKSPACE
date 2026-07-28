# git-push.ps1 — Push all workspace changes to GitHub
# Usage: triggered from the "Push to GitHub" hook in Kiro
# or manually: powershell -File scripts/git-push.ps1 "optional message"

$ErrorActionPreference = "Stop"

$MSG = if ($args[0]) { $args[0] } else { "Automatic update from Kiro - $(Get-Date -Format 'yyyy-MM-dd HH:mm')" }

Write-Host "=== Pushing to GitHub ==="
$branch = git branch --show-current
Write-Host "Branch: $branch"
Write-Host "Remote: $(git remote get-url origin)"
Write-Host ""

# Show which files will be committed
Write-Host "--- Detected changes ---"
git status --short
Write-Host ""

# Stage all changes (respects .gitignore)
git add .

# Check if there is anything to commit
$diff = git diff --cached --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "No new changes to commit."
    exit 0
}

# Commit
git commit -m $MSG

# Push to current branch
git push origin $branch

Write-Host ""
Write-Host "=== Done! Changes pushed to origin/$branch ==="
