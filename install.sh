#!/usr/bin/env bash
set -euo pipefail

install_dir="${PREFIX:-$HOME/.local/bin}"

curl -fsSL "https://raw.githubusercontent.com/ribomo/opencode-sandbox/main/opencode-sandbox" \
  -o "$install_dir/opencode-sandbox"

chmod +x "$install_dir/opencode-sandbox"

printf 'Installed to: %s/opencode-sandbox\n' "$install_dir"

if [[ ":$PATH:" != *":$install_dir:"* ]]; then
  printf 'Warning: %s is not on your PATH.\n' "$install_dir"
fi
