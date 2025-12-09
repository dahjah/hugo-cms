#!/bin/bash
# Wrapper script for dembrandt that ensures Node 20 is active
# Usage: ./dembrandt_wrapper.sh <url> [--save-output] [--json-only]

source ~/.nvm/nvm.sh
nvm use 20 > /dev/null 2>&1

dembrandt "$@"
