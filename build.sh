#!/usr/bin/env bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
# Exit on error
set -o errexit

# Modify this line as needed for your package manager (pip, poetry, etc.)
uv sync

python nabokov_admin.py