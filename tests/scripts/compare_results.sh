#!/bin/bash
set -o nounset
set -o errexit
TEST_DIR="$( pushd $1 > /dev/null  && pwd && popd > /dev/null)"
DIR="$( pushd  "$( dirname "${BASH_SOURCE[0]}" )"/../.. > /dev/null && pwd && popd > /dev/null)"
#pushd $DIR/../../

pushd $DIR
for filepath in $TEST_DIR/*
do
    fullfilename=$(basename "$filepath")
    extension="${fullfilename##*.}"
    filename="${fullfilename%.*}"
    if [[ $extension == "in" ]]
    then 
        python tests/scripts/parser.py --input_file=$filepath \
                                           --input_type=parsable \
                                           --output_type=xml \
                                            > $DIR/xml_input.tmp
        cp $filepath parsable_input.tmp
    elif [[ $extension == "xml" ]]
    then
        cp $filepath xml_input.tmp
        python tests/scripts/parser.py --input_file=$filepath \
                                           --input_type=xml \
                                           --output_type=parsable \
                                            > $DIR/parsable_input.tmp
    else
        echo "skipping $fullfilename: unsupported extension"
        continue
    fi
    if !(/usr/bin/time -f'%e' \
        java -jar java/dc-checking.jar xml_input.tmp 100000 \
        > java_output.tmp \
        2> java_time.tmp)
    then 
        echo "$(tput setaf 1)Testing $fullfilename: Java failed$(tput sgr0)"
        cat java_output.tmp | sed "s/^/  >>/"
        continue
    fi
    if !(/usr/bin/time -f'%e' \
        python tester.py < parsable_input.tmp \
        > python_output.tmp \
        2> python_time.tmp)
    then 
        echo "$(tput setaf 1)Testing $fullfilename: Python failed$(tput sgr0)"
        cat python_time.tmp 
        echo "lpl"
        continue
    fi
    tests/scripts/output_flip.sh java_output.tmp
    JAVA_OUTPUT=$(cat java_output.tmp)
    PYTHON_OUTPUT=$(cat python_output.tmp)
    JAVA_TIME=$(cat java_time.tmp)
    PYTHON_TIME=$(cat python_time.tmp)
    if diff -bs java_output.tmp python_output.tmp > /dev/null 2>&1
    then
        echo "$(tput setaf 2)Testing $fullfilename: match (answer: $JAVA_OUTPUT, Java time: $JAVA_TIME, Python time: $PYTHON_TIME)$(tput sgr0)"
    else 
        echo "$(tput setaf 1)Testing $fullfilename: mismatch (Java answer: $JAVA_OUTPUT, Python answer: $PYTHON_OUTPUT, Java time: $JAVA_TIME, Python time: $PYTHON_TIME)$(tput sgr0)"
    fi
done
# clean up
for file in {xml_input.tmp,parsable_input.tmp,java_output.tmp,python_output.tmp,java_time.tmp,python_time.tmp}
do
    [ -f $file ] && rm $file
done
popd 



#popd