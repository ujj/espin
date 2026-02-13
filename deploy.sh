#!/bin/bash
set -euo pipefail

ESPIN_DIR="$HOME/workspace/play/experiments/espin"
HOMEBREW_DIR="$HOME/workspace/play/experiments/homebrew-espin"
TAG="v1.0.0"
REMOTE="origin"
BRANCH="master"

echo "=== Step 1: Push espin repo (single squashed commit) ==="
cd "$ESPIN_DIR"
git add -A
git commit --amend -m "espin v1.0.0: local voice-to-text for macOS" 2>/dev/null || true

echo "=== Step 2: Re-tag ==="
git tag -d "$TAG" 2>/dev/null || true
git tag "$TAG"

echo "=== Step 3: Force push code + tag ==="
git push --force "$REMOTE" "$BRANCH"
git push --force "$REMOTE" "$TAG"

echo "=== Step 4: Get new SHA ==="
sleep 3  # give GitHub a moment to process
SHA=$(curl -sL "https://github.com/ujj/espin/archive/refs/tags/${TAG}.tar.gz" | shasum -a 256 | awk '{print $1}')
echo "New SHA: $SHA"

if [ -z "$SHA" ] || [ ${#SHA} -ne 64 ]; then
    echo "ERROR: Failed to get valid SHA. Aborting."
    exit 1
fi

echo "=== Step 5: Update tap (homebrew-espin) Formula + SHA and push ==="
sed -i '' "s/sha256 \"[a-f0-9]*\"/sha256 \"${SHA}\"/" "$HOMEBREW_DIR/Formula/espin.rb"
cd "$HOMEBREW_DIR"
git add -A
git commit --amend -m "espin 1.0.0" 2>/dev/null || true
git push --force "$REMOTE" "$BRANCH"

echo ""
echo "=== Done ==="
echo "SHA: $SHA"
echo ""
echo "Test with:"
echo "  brew untap ujj/espin; brew tap ujj/espin; brew install espin"
