#!/bin/bash

path_prepend() {
    eval export ${1}="$2:`eval echo \\$\${1} | sed -e "s#$2##g" -e "s#^:*##g"`"
}

LSBRELEASE="`which lsb_release 2>/dev/null`"
MTYPE="`uname -m`"
DEFMARCH="slc5-gcc43-opt"
if [ -n "$LSBRELEASE" ] ; then
    case `lsb_release -rs | cut -d. -f 1` in
       5) MARCH="slc5-gcc43-opt" ;;
       6) MARCH="slc6-gcc46-opt" ;;
       *) MARCH="$DEFMARCH" ;;
    esac
    ARCH="$MTYPE-$MARCH"
else
    ARCH="$MTYPE-$DEFMARCH"
fi

# Check if we're running executed or sourced
if [ "$BASH_SOURCE" == "$0" ] ; then
    echo "You should source binsetup, not execute it"
    exit 1
fi

# Get the full path to the software root directory
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ] ; do
    SOURCE="$(readlink "$SOURCE")"
done
DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
SWDIR="`readlink -f $DIR/..`"

if [ -d $SWDIR/local/$ARCH/bin ] ; then
    path_prepend PATH $SWDIR/local/$ARCH/bin
fi
