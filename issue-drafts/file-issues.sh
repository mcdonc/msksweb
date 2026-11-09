#!/usr/bin/env bash
# File the msksweb issue drafts (01-scaffold.md … 11-ui-polish.md) to GitHub.
# Requires a token with the "Issues: Read and write" repository permission.
set -euo pipefail
cd "$(dirname "$0")"
REPO=mcdonc/msksweb
for f in [0-9][0-9]-*.md; do
  title=$(head -1 "$f" | sed 's/^#* *//')
  body=$(tail -n +2 "$f" | sed 's/^$//' | sed 1d)
  echo "filing: $title"
  gh issue create -R "$REPO" -t "$title" -b "$body"
done
