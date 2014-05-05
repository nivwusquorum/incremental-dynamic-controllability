#!/bin/bash
set -o nounset
set -o errexit

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )/../"

function openpdf {
    evince $1 >/dev/null 2>&1 & disown
}
[ -d .tmp ] || mkdir .tmp
for x in $@
do
    filename=$(basename "$x")
    extension="${filename##*.}"
    filename="${filename%.*}"
    if [[ "$extension" == "xml" ]]
    then
        INPUT_TYPE="xml"
    elif [[ "$extension" == "in" ]]
    then
        INPUT_TYPE="parsable"
    else
        echo "unsupported extension"
        exit 1
    fi
    python scripts/parser.py --input_file=$x --input_type=$INPUT_TYPE --output_type=dot > .tmp/graphviz_tmp.dot
    dot -Tpdf .tmp/graphviz_tmp.dot -o .tmp/$filename.pdf
    openpdf .tmp/$filename.pdf
done
