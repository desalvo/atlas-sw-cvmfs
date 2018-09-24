export DQ2_LOCAL_SITE_ID=ROAMING
[ -n "$ATLAS_LOCAL_AREA" -a -f "$ATLAS_LOCAL_AREA/setup-dq2.sh" ] && source $ATLAS_LOCAL_AREA/setup-dq2.sh
[ -n "$ATLAS_LOCAL_AREA" -a -f "$ATLAS_LOCAL_AREA/setup-dq2.sh.local" ] && source $ATLAS_LOCAL_AREA/setup-dq2.sh.local
