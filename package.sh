#!/usr/bin/env bash

set -euo pipefail

readonly addon_name=autocopy
readonly root_dir=$(git rev-parse --show-toplevel)
readonly branch=$(git branch --show-current)
readonly zip_name=${addon_name}_${branch}.ankiaddon

cd -- "$root_dir" || exit 1
rm -- "$zip_name" 2>/dev/null || true

export root_dir branch

git archive "$branch" --format=zip --output "$zip_name"

# package ajt common
(cd -- ajt_common && git archive HEAD --prefix="${PWD##*/}/" --format=zip -o "$root_dir/${PWD##*/}.zip")

zipmerge "$zip_name" ./*.zip
rm -- ./*.zip
