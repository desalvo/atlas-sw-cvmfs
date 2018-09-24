################################
#  Local configuration script  #
#     A. De Salvo 20120828     #
################################

if [ -z "$VO_ATLAS_SW_DIR" ] ; then
    # Get the full path to the software root directory
    if [ -n "${BASH_SOURCE}" ] ; then
        [ "${BASH_SOURCE[0]}" != "$0" ] && SCRIPT_PATH="${BASH_SOURCE[0]}"
    else
        SCRIPT_PATH="$(pwd -P)"
    fi
    if [ -z "$SCRIPT_PATH" ] ; then
        echo "Please source the setup.sh script"
        exit 1
    fi
    SCRIPT_PATH="$(readlink "$SCRIPT_PATH")"
    DIR="$( cd -P "$( dirname "$SCRIPT_PATH" )" && pwd )"
    export VO_ATLAS_SW_DIR="`readlink -f $DIR/../..`"
fi

# Set the Poolcond Path
export ATLAS_POOLCOND_PATH="/cvmfs/atlas.cern.ch/repo/conditions"

# Set the Path to cctools
[ -f $VO_ATLAS_SW_DIR/cctools/latest/setup.sh ] && source $VO_ATLAS_SW_DIR/cctools/latest/setup.sh

# Auto configuration
[ -f $VO_ATLAS_SW_DIR/local/bin/auto-setup ] && source $VO_ATLAS_SW_DIR/local/bin/auto-setup

# Overrides to the current values
[ -n "$ATLAS_LOCAL_AREA" ] && source $ATLAS_LOCAL_AREA/setup.sh
