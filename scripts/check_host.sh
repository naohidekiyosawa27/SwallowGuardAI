#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p build
g++ -std=c++17 -Wall -Wextra -Werror -pedantic -fsanitize=undefined \
    -I firmware/include firmware/host_tests/test_core.cpp -o build/test_core
./build/test_core

g++ -std=c++17 -Wall -Wextra -Werror -pedantic -fsanitize=undefined \
    -I firmware/include firmware/host_tests/test_reva_link.cpp -o build/test_reva_link
./build/test_reva_link
