#!/bin/bash
set -o nounset
set -o errexit

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
pushd $DIR/../
[ -d parsable ] || mkdir parsable
for x in $(ls raw_xml/* | sort -n -t t -k 3)
do
    filename=$(basename "$x")
    extension="${filename##*.}"
    filename="${filename%.*}"
    if [[ "$extension" == "xml" ]]
    then
        echo "Parsing $x"
        python scripts/xml_parser.py --input_file=$x --output_type=parsable > parsable/$filename.in 
    fi
done
popd