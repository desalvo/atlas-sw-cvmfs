##############################
# ATLAS local setup script
# Alessandro De Salvo <Alessandro.De.Salvo@cern.ch>
# 20130708
##############################

SAVEDOPTS="$@"

while true ; do
    case "$1" in
        -s) PANDARES="$2";shift 2;;
        -*) shift;;
        --) shift; break;;
        *)  break;
        exit;;
    esac
done 

# Use PANDA_SITE_NAME, if defined
[ -n "$PANDA_SITE_NAME" ] && PANDARES="$PANDA_SITE_NAME"

# Use PANDA_RESOURCE, if defined
[ -n "$PANDA_RESOURCE" ] && PANDARES="$PANDA_RESOURCE"

if [ -n "$PANDARES" ] ; then
    echo "LOCAL-SETUP> PANDA RESOURCE: $PANDARES"
    PANDARES_OPT="-r $PANDARES"
else
    echo "LOCAL-SETUP> NO PANDA RESOURCE FOUND"
fi

if [ -z "$VO_ATLAS_SW_DIR" ] ; then
    export VO_ATLAS_SW_DIR="/cvmfs/atlas.cern.ch/repo/sw"
    echo "AUTO-SETUP> WARNING: VO_ATLAS_SW_DIR not set. Automatically set to $VO_ATLAS_SW_DIR"
fi
export ATLAS_POOLCOND_PATH="/cvmfs/atlas.cern.ch/repo/conditions"
if [ -z "$CMTUSERCONTEXT" ] ; then
    GLV="`getconf  GNU_LIBC_VERSION | awk '{print $NF}' | awk -F. '{printf "%d%02d", $1, $2}'`"
    [ $GLV -gt 205 ] && export CMTUSERCONTEXT="`dirname $VO_ATLAS_SW_DIR`/tools/slc6/cmt"
fi
[ -f $VO_ATLAS_SW_DIR/cctools/latest/setup.sh ] && source $VO_ATLAS_SW_DIR/cctools/latest/setup.sh
if [ -n "$PANDARES" ] ; then
    # Full auto setup if $PANDARES is defined
    echo "AUTO-SETUP> INFO: PANDA_RESOURCE=$PANDARES"
    echo "AUTO-SETUP> INFO: Full auto setup, calling $VO_ATLAS_SW_DIR/local/bin/auto-setup $PANDARES_OPT --"
    [ -f $VO_ATLAS_SW_DIR/local/bin/auto-setup ] && . $VO_ATLAS_SW_DIR/local/bin/auto-setup $PANDARES_OPT --
    echo "AUTO-SETUP> INFO: setting FRONTIER_SERVER=$FRONTIER_SERVER"
    echo "AUTO-SETUP> INFO: setting DQ2_LOCAL_SITE_ID=$DQ2_LOCAL_SITE_ID"
else
    # Selective auto setup if $PANDARES is not defined
    ASSWITCHER="$VO_ATLAS_SW_DIR/local/bin/auto-setup-switcher"
    [ -s "$ASSWITCHER" ] && ASMODE="`$ASSWITCHER 2> /dev/null`" || ASMODE="none"
    if [ "$ASMODE" != "auto" ] ; then
        [ -f $VO_ATLAS_SW_DIR/local/bin/auto-setup ] && . $VO_ATLAS_SW_DIR/local/bin/auto-setup -t $PANDARES_OPT --
        [ -n "$ATLAS_LOCAL_AREA" -a -s $ATLAS_LOCAL_AREA/setup.sh ] && source $ATLAS_LOCAL_AREA/setup.sh
        # Consistency checks
        echo "AUTO-SETUP> INFO: CUSTOM_SITE_NAME=$CUSTOM_SITE_NAME, ATLAS_SITE_NAME=$ATLAS_SITE_NAME, SITE_NAME=$SITE_NAME, PANDA_RESOURCE=$PANDARES"
        if [ -n "$FRONTIER_SERVER_TRIAL" ] ; then
            if [ "$FRONTIER_SERVER" != "$FRONTIER_SERVER_TRIAL" ] ; then
                echo "AUTO-SETUP> WARNING: auto-setup FRONTIER_SERVER differs from the local one [FRONTIER_SERVER=$FRONTIER_SERVER]"
            else
                echo "AUTO-SETUP> INFO: auto-setup FRONTIER_SERVER matches the local one"
            fi
        fi
        if [ -n "$DQ2_LOCAL_SITE_ID_TRIAL" ] ; then
            if [ "$DQ2_LOCAL_SITE_ID" != "$DQ2_LOCAL_SITE_ID_TRIAL" ] ; then
                echo "AUTO-SETUP> WARNING: auto-setup DQ2_LOCAL_SITE_ID differs from the local one [DQ2_LOCAL_SITE_ID=$DQ2_LOCAL_SITE_ID]"
            else
                echo "AUTO-SETUP> INFO: auto-setup DQ2_LOCAL_SITE_ID matches the local one"
            fi
        fi
    else
        echo "AUTO-SETUP> INFO: CUSTOM_SITE_NAME=$CUSTOM_SITE_NAME, ATLAS_SITE_NAME=$ATLAS_SITE_NAME, SITE_NAME=$SITE_NAME, PANDA_RESOURCE=$PANDARES"
        echo "AUTO-SETUP> INFO: auto setup enabled"
        echo "AUTO-SETUP> INFO: calling $VO_ATLAS_SW_DIR/local/bin/auto-setup $PANDARES_OPT --"
        [ -f $VO_ATLAS_SW_DIR/local/bin/auto-setup ] && . $VO_ATLAS_SW_DIR/local/bin/auto-setup $PANDARES_OPT --
        echo "AUTO-SETUP> INFO: setting FRONTIER_SERVER=$FRONTIER_SERVER"
        echo "AUTO-SETUP> INFO: setting DQ2_LOCAL_SITE_ID=$DQ2_LOCAL_SITE_ID"
    fi
fi
[ -n "$ATLAS_LOCAL_AREA" -a -s $ATLAS_LOCAL_AREA/setup.sh.local ] && source $ATLAS_LOCAL_AREA/setup.sh.local


# TEMPORARY FIX: Set up ATLAS_LOCAL_ROOT_BASE, if not yet set,
# useful tor RootCore. THIS SHOULD GO INTO THE AUTO-SETUP
[ -z "$CVMFSBASE" ] &&  export CVMFSBASE="`echo $VO_ATLAS_SW_DIR | sed -e 's/\/atlas.cern.ch\/repo\/sw//'`"
[ -z "$ATLAS_LOCAL_ROOT_BASE" ] && export ATLAS_LOCAL_ROOT_BASE="$CVMFSBASE/atlas.cern.ch/repo/ATLASLocalRootBase"

# YAMPL
[ -f $VO_ATLAS_SW_DIR/local/setup-yampl.sh ] && . $VO_ATLAS_SW_DIR/local/setup-yampl.sh --

# Fix for MadGraph
[ -n "$TMPDIR" ] && export GFORTRAN_TMPDIR=$TMPDIR

# Setup rucio, xrootd and davix
export ALRB_noGridMW=YES
source $ATLAS_LOCAL_ROOT_BASE/user/atlasLocalSetup.sh --quiet
export RUCIO_ACCOUNT=pilot
lsetup rucio xrootd davix

set -- "$SAVEDOPTS"
