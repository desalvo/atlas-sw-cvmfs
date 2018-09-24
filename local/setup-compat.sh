###################################################
# ATLAS local setup script for compatibility libs
# Alessandro De Salvo <Alessandro.De.Salvo@cern.ch>
# 20130919
###################################################

PLATF="i686-slc5-gcc43-opt"
SCVERSION="setup-compat.sh v1.2 - 20131002"
SCshowHelp() {
    cat <<EOD
Usage: setup-compat.sh [OPTION]
   OPTIONS
   -------
   --help|-h          Display this help
   --arch|-a <arch>   Use <arch> architecture, defaults to $PLATF
   --quiet|-q         Suppress extra printing
   --dev|-D           Use the slc6-dev area instead of the production one
$SCVERSION
Alessandro De Salvo <Alessandro.DeSalvo@roma1.infn.it>
EOD
}

SCCUC="slc6"
SCOPTS=`getopt -o a:Dhq -l arch:,dev,help,quiet -- "$@"`
if [ $? != 0 ] ; then echo "Terminating..."; exit -1 ; fi

for i in `echo $SCOPTS`; do
    case "$i" in
        --arch|-a)       PLATF="$2"; shift 2;;
        --help|-h)       SCshowHelp; SCSKIPALL="yes"; break;;
        --dev|-D)        SCCUC="slc6-dev"; shift;;
        --quiet|-q)      SCQUIET="yes"; shift;;
        --)              break;;
    esac
done

if [ -z "$SCSKIPALL" ] ; then
    OSBINVER="`echo $PLATF | sed -e 's/\(i686\|x86_64\)[-_]\(slc[0-9]*\)[-_]\(gcc[0-9]*\)[-_]\(.*\)/\2/g'`"
    [ -z "$VO_ATLAS_SW_DIR" ] && VO_ATLAS_SW_DIR="/cvmfs/atlas.cern.ch/repo/sw"
    GLV="`getconf  GNU_LIBC_VERSION | awk '{print $NF}' | awk -F. '{printf "%d%02d", $1, $2}'`"
    if [ $GLV -gt 205 -a "$OSBINVER" = "slc5" ] ; then
        # Only set CMTUSERCONTEXT for slc6 or later OS versions when using slc5 binaries
        export CMTUSERCONTEXT="`dirname $VO_ATLAS_SW_DIR`/tools/${SCCUC}/cmt"
        [ -z "$SCQUIET" ] && echo "Setting up CMTUSERCONTEXT=${CMTUSERCONTEXT} for slc5 binaries on slc6 OS or later"
    else
        [ -n "$CMTUSERCONTEXT" ] && unset CMTUSERCONTEXT
    fi
fi

unset SCVERSION SCshowHelp SCOPTS SCSKIPALL SCQUIET SCCUC OSBINVER GLV
