#!/bin/bash
# Get the full path to the software root directory
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ] ; do
    SOURCE="$(readlink "$SOURCE")"
done
DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
export ATLAS_LOCAL_ROOT_BASE="`readlink -f $DIR/../../ATLASLocalRootBase`"

# being conservative for grid sites and setting specific xrootd version 
#xrdversion=4.5.0

[ -n "$AtlasSetupSite" ] && AtlasSetupSiteSet="y"
source $ATLAS_LOCAL_ROOT_BASE/user/atlasLocalSetup.sh --quiet
[ -n "$AtlasSetupSiteSet" ] && unset AtlasSetupSite AtlasSetupSiteSet

#if [ -n "$CMTCONFIG" ]; then
#    arch=`echo $CMTCONFIG | cut -f 1 -d "-"`
#    slcVersion=`echo $CMTCONFIG | sed 's/.*slc\([[:digit:]*]\)-.*/\1/g'`
#else
#    arch=`uname -p`
#    GLV="`getconf  GNU_LIBC_VERSION | awk '{print $NF}' | awk -F. '{printf "%d%02d", $1, $2}'`"
#    if [ $GLV -le 205 ]; then
#        slcVersion="5"
#    else
#        slcVersion="6"
#    fi
#fi

#eval localSetupXRootD ${xrdversion}-${arch}-slc${slcVersion} --quiet

#  export ALRB_xrootdVersion=testing  # set if xrootdsetup-dev.sh
lsetup xrootd -q
