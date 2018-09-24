#!/bin/bash
# Get the full path to the software root directory
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ] ; do
    SOURCE="$(readlink "$SOURCE")"
done
DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
export ATLAS_LOCAL_ROOT_BASE="`readlink -f $DIR/../../ATLASLocalRootBase`"
source ${ATLAS_LOCAL_ROOT_BASE}/user/atlasLocalSetup.sh --quiet
source ${ATLAS_LOCAL_ROOT_BASE}/packageSetups/atlasLocalROOTSetup.sh --rootVersion=5.34.04-x86_64-slc5-gcc4.3 --skipConfirm
