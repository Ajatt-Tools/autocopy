#!/usr/bin/env bash

set -euo pipefail

addon_name=autocopy
root_dir=$(git rev-parse --show-toplevel)
output=${addon_name}.ankiaddon
readonly addon_name root_dir output

cd -- "$root_dir" || exit 1
rm -- "$output" 2>/dev/null || true

"$root_dir/autocopy/ajt_common/package.sh" \
	--package "AJT ${addon_name^}" \
	--name "AJT ${addon_name^}" \
	--zip_name "$output" \
	--root "autocopy" \
	"$@"

if ! [[ -f $output ]]; then
	echo "Missing file: $output"
	exit 1
fi
