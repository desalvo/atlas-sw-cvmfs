###################################################
# ATLAS local setup script for yampl libs
# Alessandro De Salvo <Alessandro.De.Salvo@cern.ch>
# 20140311
###################################################

PLATF="x86_64-slc5-gcc43-opt"
SYVERSION="setup-yampl.sh v1.0 - 20150828"
SYshowHelp() {
    cat <<EOD
Usage: setup-yampl.sh [OPTION]
   OPTIONS
   -------
   --help|-h          Display this help
   --arch|-a <arch>   Use <arch> architecture, defaults to $PLATF
   --quiet|-q         Suppress extra printing
$SCVERSION
Alessandro De Salvo <Alessandro.DeSalvo@roma1.infn.it>
EOD
}

SYenvmunge() {
    if ! echo $LD_LIBRARY_PATH | /bin/egrep -q "(^|:)$1($|:)" ; then
        [ -n "$LD_LIBRARY_PATH" ] && LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$1 || LD_LIBRARY_PATH=$1
    fi
    if [ -n "$2" ] ; then
        if ! echo $PYTHONPATH | /bin/egrep -q "(^|:)$1($|:)" ; then
            [ -n "$PYTHONPATH" ] && PYTHONPATH=$PYTHONPATH:$2 || PYTHONPATH=$2
        fi
    fi
}

SYOPTS=`getopt -o a:hq -l arch:,help,quiet -- "$@"`
if [ $? != 0 ] ; then echo "Terminating..."; exit -1 ; fi

for i in `echo $SYOPTS`; do
    case "$i" in
        --arch|-a)       PLATF="$2"; shift 2;;
        --help|-h)       SCshowHelp; SYSKIPALL="yes"; break;;
        --quiet|-q)      SYQUIET="yes"; shift;;
        --)              break;;
    esac
done

if [ -z "$SYSKIPALL" ] ; then
    PYFULLVER="`python -c 'import platform;v=platform.python_version_tuple();print "%s.%s.%s" % (v[0],v[1],v[2])'`"
    PYVER="`python -c 'import platform;v=platform.python_version_tuple();print "%s.%s" % (v[0],v[1])'`"
    [ -z "$VO_ATLAS_SW_DIR" ] && VO_ATLAS_SW_DIR="/cvmfs/atlas.cern.ch/repo/sw"
    LIBYAMPL="${VO_ATLAS_SW_DIR}/local/${PLATF}/yampl/1.0/lib"
    PYYAMPL="${VO_ATLAS_SW_DIR}/local/noarch/python-yampl/1.0/lib.linux-x86_64-${PYFULLVER}"
    [ ! -d $PYYAMPL ] && PYYAMPL="${VO_ATLAS_SW_DIR}/local/noarch/python-yampl/1.0/lib.linux-x86_64-${PYVER}"
    [ ! -d "$PYYAMPL" ] && unset PYYAMPL
    SYenvmunge $LIBYAMPL $PYYAMPL
    export LD_LIBRARY_PATH PYTHONPATH
fi

unset SYVERSION SYshowHelp SYOPTS SYSKIPALL SYQUIET SYenvmunge
