#!/usr/bin/env bash
# usage: run.sh <routing.xml> <profile> <params|-> <hh|astar> <out.json> [routes]
D=$(cd "$(dirname "$0")/.." && pwd)
java -Xmx6g -cp "$D/mapcreator/lib/*" "$D/harness/Harness.java" "$1" "$2" "$3" "$4" "${6:-$D/harness/routes.txt}" "$5" "$D"/maps/*.obf 2> "$5.log"
