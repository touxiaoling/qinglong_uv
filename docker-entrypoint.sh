#!/bin/sh
set -eu

# The release's download catalog determines which Python patches uv can install.
uv self update || printf '%s\n' 'Could not update uv. Continuing with the installed release.' >&2
env -u UV_PYTHON uv python upgrade || printf '%s\n' 'Could not upgrade managed Python installations.' >&2
uv cache prune --force || printf '%s\n' 'Could not prune the uv cache.' >&2

export UV_MANAGED_PYTHON=1
exec uv run --locked --no-dev -m qinglong "$@"
