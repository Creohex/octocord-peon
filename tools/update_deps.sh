#!/bin/bash

set -e

libs=("common" "telegram" "discord")

for lib in "${libs[@]}"; do
    folder="./peon_$lib"
    target_file="./dependencies/deps_$lib.txt"
    echo "Generating deps for $lib package ($target_file)..."
    poetry export -C "$folder" --output "$target_file" --without-urls
done

echo "done"
