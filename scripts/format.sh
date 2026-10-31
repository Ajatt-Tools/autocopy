#!/bin/bash
# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

set -euo pipefail

ROOT_DIR=$(git rev-parse --show-toplevel)
readonly ROOT_DIR

# Use the same shared formatter as AJT_Japanese without touching the bundled submodule.
# Adapted from https://github.com/Ajatt-Tools/mergenotes/blob/b83f34948238a79e8f7f08c3a1a256c0f51908d6/scripts/format.sh
# Forward --check so validation uses the same file scope without rewriting source files.
"$ROOT_DIR/autocopy/ajt_common/format.sh" \
	--include autocopy \
	--include tests \
	--include playground \
	--include autocopy/ajt_common \
	--exclude autocopy/__about__.py \
	"$@"
