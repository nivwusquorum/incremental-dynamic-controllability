#!/bin/bash
set -o nounset
set -o errexit

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
pushd $DIR/../
for x in $(ls raw_xml/* | sort -n -t t -k 3)
do
    filename=$(basename "$x")
    extension="${filename##*.}"
    filename="${filename%.*}"
    if [[ "$extension" == "xml" ]]
    then
        echo "Parsing $x"
        python scripts/xml_parser.py --input_file=$x --output_type=dot > graphviz_tmp.dot
        dot -Tpdf graphviz_tmp.dot -o visualized/$filename.pdf
        rm graphviz_tmp.dot
    fi
done
popd