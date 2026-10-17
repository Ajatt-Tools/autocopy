#!/bin/bash
# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

set -euo pipefail

ROOT_DIR=$(git rev-parse --show-toplevel)
readonly ROOT_DIR

# Use the same shared formatter as AJT_Japanese without touching the bundled submodule.
"$ROOT_DIR/autocopy/ajt_common/format.sh" \
	--include autocopy \
	--include tests \
	--include playground \
	--exclude autocopy/ajt_common
