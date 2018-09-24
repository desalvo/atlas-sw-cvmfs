#/bin/csh
###################################################
# ATLAS local setup script for compatibility libs
# Alessandro De Salvo <Alessandro.De.Salvo@cern.ch>
# 20130708
###################################################

set SCVERSION="setup-compat.sh v1.0 - 20130708"

set SCCUC="slc6"
set SCOPTS=(`getopt -l dev,help,quiet Dhq $*`)
if ($? != 0) then
    echo "Terminating..."
    exit 1
endif

eval set argv=\($SCOPTS:q\)

while (1)
    switch ($1:q)
        case -h:
        case --help:
            cat <<EOD
Usage: setup-compat.sh [OPTION]
   OPTIONS
   -------
   --help|-h          Display this help
   --quiet|-q         Suppress extra printing
   --dev|-D           Use the slc6-dev area instead of the production one
$SCVERSION
Alessandro De Salvo <Alessandro.DeSalvo@roma1.infn.it>
EOD
            set SCSKIPALL="yes"; shift
            breaksw
        case -D:
        case --dev:
            set SCCUC="slc6-dev"; shift
            breaksw
        case -q:
        case --quiet:
            set SCQUIET="yes";shift
            breaksw
        case --:
            shift
            break
        default:
            exit 1
    endsw
end

if (! $?SCSKIPALL) then
    if ($?1 && "$1" != "") then
        set PLATF="$1"
    else
        set PLATF = "i686-slc5-gcc43-opt"
    endif
    set OSBINVER=`echo $PLATF | sed -e 's/\(i686\|x86_64\)[-_]\(slc[0-9]*\)[-_]\(gcc[0-9]*\)[-_]\(.*\)/\2/g'`
    if (! $?VO_ATLAS_SW_DIR) then
       set VO_ATLAS_SW_DIR="/cvmfs/atlas.cern.ch/repo/sw"
    endif
    set GLV=`getconf  GNU_LIBC_VERSION | awk '{print $NF}' | awk -F. '{printf "%d%02d", $1, $2}'`
    if ($GLV > 205 && "$OSBINVER" == "slc5") then
        # Only set CMTUSERCONTEXT for slc6 or later OS versions when using slc5 binaries
        setenv CMTUSERCONTEXT "`dirname $VO_ATLAS_SW_DIR`/tools/${SCCUC}/cmt"
        if (! $?SCQUIET) then
            echo "Setting up CMTUSERCONTEXT=${CMTUSERCONTEXT} for slc5 binaries on slc6 OS or later"
        endif
    else
        if ($?CMTUSERCONTEXT) then
            unsetenv CMTUSERCONTEXT
        endif
    endif
endif

unset SCVERSION SCshowHelp SCOPTS SCSKIPALL SCQUIET SCCUC OSBINVER GLV
