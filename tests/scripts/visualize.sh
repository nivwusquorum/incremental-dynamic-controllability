#!/bin/bash
set -o nounset
set -o errexit

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
FILE_PATH="$( pushd $(dirname $1) > /dev/null  && echo $(pwd)/$(basename $1) && popd > /dev/null)"

function openpdf {
    evince $1 >/dev/null 2>&1 & disown
}

pushd $DIR/../../
pwd
[ -d .tmp ] || mkdir .tmp
filename=$(basename "$1")
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
python tests/scripts/parser.py --input_file=$FILE_PATH --input_type=$INPUT_TYPE --output_type=dot > .tmp/graphviz_tmp.dot
dot -Tpdf .tmp/graphviz_tmp.dot -o .tmp/$filename.pdf
openpdf .tmp/$filename.pdf
popd