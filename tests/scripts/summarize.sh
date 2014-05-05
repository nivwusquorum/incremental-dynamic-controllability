#!/bin/bash
set -o nounset
set -o errexit

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
pushd $DIR/../
for x in $(ls raw_xml/* | sort -n -t t -k 3)
do
    echo "summary of $x:"
    python scripts/xml_parser.py --input_file=$x --output_type=summary
done
popd