#!/usr/bin/env python
#####################################################################
# CRIC site info tool                                               #
# LJSFi Framework 2.1.0                                             #
# Alessandro De Salvo <Alessandro.DeSalvo@roma1.infn.it> - 20231018 #
#####################################################################

__version__ = "$Revision: 1.2 $"[11:-1]

__HELP__="""CRIC site info tool %s.
Usage: cric-site-info [OPTION]

Options:
  --help                        Display this help and exit.
  --debug | -d                  Debug mode
  --corecount | -c <pres>       Core count for panda resource <pres>
  --endpoint | -e <name>        Endpoint name
  --fsconf | -f                 Show frontier setup
  --has-proxyconfig | -P        Return true if the site is configured to use proxyconfig
  --proxyconfig | -p            Force proxyconfig setup for Frontier
  --id | -i                     Show the site id
  --jobmanages | -j <pres>      Show the jobmanager type for the panda resource <pres>
  --maxfs | -m <num>            Do not allow more than <num> serverurls for Frontier
  --queues | -q <pres>          Show queues data for panda resource <pres>
  --resinfo | -I <pres>         Show info on panda resource <pres>
  --setype | -S                 Show the SE type of a given endpoint
  --site | -s <sitename>        Site name
  --show-site-name | -n <pres>  Show the site name of the panda resource <pres>

Alessandro De Salvo <Alessandro.DeSalvo@roma1.infn.it>.
"""

try:
    import json
except:
    import simplejson as json
try:
    import commands
    commandstool = commands
except:
    import subprocess
    commandstool = subprocess
import os, sys
import time
import getopt
import string
import re
try:
    import hashlib
except:
    import md5 as hashlib

__CRIC_SITE_INFO__ = "https://atlas-cric.cern.ch/api/atlas/site/query/?json"
__CRIC_SITE_INFO_SITE__ = "https://atlas-cric.cern.ch/api/atlas/site/query/?json&site=%s"
#__CRIC_SITE_INFO_CACHE__ = "http://atlas-agis-api.cern.ch/jsoncache/list_sites.json"
__CRIC_SITE_INFO_CACHE__ = __CRIC_SITE_INFO__
__CURL_EXEC__ = "curl -S --connect-timeout 60 -o '%s' '%s' 2>/dev/null"
__CACHE_FILE__ = "/var/tmp/.cricinfo_%s/cric-site-info" % os.getuid()
__CACHE_EXPIRY__ = 3600
__STALE_TMPFILE__ = 200
__TMPFILE__     = "%s.tmp" % __CACHE_FILE__
__MAX_BACKUP_FILES__ = 10
#__BPROXY_MAP__ = {
#                       "cern.ch": "http://atlasbpfrontier.cern.ch:3127",
#                       "gridpp.rl.ac.uk": "http://atlasbpfrontier.cern.ch:3127",
#                       "lcg.triumf.ca": "http://atlasbpfrontier.fnal.gov:3127",
#                       "in2p3.fr": "http://atlasbpfrontier.cern.ch:3127",
#                     }
#__DEFAULT_BPROXIES__ = ["http://atlasbpfrontier.cern.ch:3127","http://atlasbpfrontier.fnal.gov:3127"]
__BPROXY_MAP__ = {
                       "cern.ch": "http://v4f.hl-lhc.net:6082",
                       "gridpp.rl.ac.uk": "http://v4f.hl-lhc.net:6082",
                       "lcg.triumf.ca": "http://v4f.hl-lhc.net:6082",
                       "in2p3.fr": "http://v4f.hl-lhc.net:6082",
                 }
__DEFAULT_BPROXIES__ = ["http://v4f.hl-lhc.net:6082"]
__PROXY_DEFAULT_AUTOCONFIG__ = "(serverurl=http://atlascern-frontier.openhtc.io:8080/atlr)(serverurl=http://atlascern1-frontier.openhtc.io:8080/atlr)(serverurl=http://atlascern2-frontier.openhtc.io:8080/atlr)(serverurl=http://atlascern3-frontier.openhtc.io:8080/atlr)(serverurl=http://atlascern4-frontier.openhtc.io:8080/atlr)(proxyconfigurl=http://grid-wpad/wpad.dat)(proxyconfigurl=http://lhchomeproxy.cern.ch/wpad.dat)(proxyconfigurl=http://lhchomeproxy.fnal.gov/wpad.dat)"

if ("VO_ATLAS_SW_DIR" in os.environ):
    __DEFAULT_CRIC_SITE_INFO__ = "%s/local/etc/cric_sites.json" % os.environ["VO_ATLAS_SW_DIR"]
    __CRIC_STATIC_SITE_INFO__ = "%s/local/etc/cric_static_site_info.json" % os.environ["VO_ATLAS_SW_DIR"]
    __CRIC_OVERRIDE_SITE_INFO__ = "%s/local/etc/cric_override_sites.json" % os.environ["VO_ATLAS_SW_DIR"]
    __CRIC_SCHEDCONF__ = "%s/local/etc/cric_pandaqueues.json" % os.environ["VO_ATLAS_SW_DIR"]
else:
    #sys.stderr.write("No VO_ATLAS_SW_DIR set, using /cvmfs/atlas.cern.ch/repo/sw\n")
    __DEFAULT_CRIC_SITE_INFO__ = "/cvmfs/atlas.cern.ch/repo/sw/local/etc/cric_sites.json"
    __CRIC_STATIC_SITE_INFO__ = "/cvmfs/atlas.cern.ch/repo/sw/local/etc/cric_static_sites.json"
    __CRIC_OVERRIDE_SITE_INFO__ = "/cvmfs/atlas.cern.ch/repo/sw/local/etc/cric_override_sites.json"
    __CRIC_SCHEDCONF__ = "/cvmfs/atlas.cern.ch/repo/sw/local/etc/cric_pandaqueues.json"

short_options = "c:de:hfiI:j:m:n:pPq:Ss:"
long_options = ["corecount=","debug", "endpoint=", "fsconf", "has-proxyconfig", "help", "jobmanager=", "id", "maxfs=", "proxyconfig", "queues=", "resinfo=", "setype", "site=", "show-site-name="]

class cricSiteInfo:
    debug = False
    mode = None

    def setDebug(self, flag=False):
        self.debug = flag

    def getCricData(self,site=None):
        # Get the json files from CRIC
        asinfo = None
        assinfo = None
        cric_site_data = []
        cric_static_site_data = []

        cachedir = os.path.dirname(__CACHE_FILE__)
        if (not os.path.exists(cachedir)): os.makedirs(cachedir)
        cricurl = __CRIC_SITE_INFO_CACHE__
        tmpfile = __TMPFILE__
        cachefile = __CACHE_FILE__
        timestamp = time.strftime('%s')
        cachebackup = "%s.%s" % (cachefile,timestamp)
        json_site_data = None

        if (os.path.exists(__DEFAULT_CRIC_SITE_INFO__)):
            st = os.stat(__DEFAULT_CRIC_SITE_INFO__)
            sys.stderr.write("Size of CRIC cache file %s is %d\n" % (__DEFAULT_CRIC_SITE_INFO__,st.st_size))
            try:
                asinfo = __DEFAULT_CRIC_SITE_INFO__
                if (self.debug): sys.stderr.write("Reading CRIC site data from %s\n" % asinfo)
                cric_site_info = open(asinfo,'r')
                json_site_data = cric_site_info.read()
                cric_site_info.close()
            except:
                if (self.debug): sys.stderr.write("Failed to read CRIC site data from %s\n" % asinfo)
                json_site_data = None

        if (not json_site_data):
            asinfo = cachefile
            refresh = True
            if (os.path.exists(cachefile)):
                now = time.time()
                st = os.stat(cachefile)
                if ((now - st.st_mtime) < __CACHE_EXPIRY__): refresh = False
            if (not refresh):
                if (self.debug): sys.stderr.write("Using cached CRIC data\n")
            else:
                if (self.debug): sys.stderr.write("Refreshing CRIC data\n")
                try:
                    if (self.debug): sys.stderr.write("Getting CRIC site data from %s\n" % cricurl)
                    s,o = commandstool.getstatusoutput(__CURL_EXEC__ % (tmpfile, cricurl))
                    if (s != 0):
                        print (o)
                        raise
                    # Rotate files
                    if (os.path.exists(cachefile)): os.rename(cachefile,cachebackup)
                    if (os.path.exists(tmpfile)): os.rename(tmpfile,cachefile)
                    # Cleanup files
                    bfd = os.path.dirname(cachebackup)
                    backuplist = os.listdir(bfd)
                    blist = []
                    for backupfile in backuplist:
                        fparts = backupfile.split(".")
                        if (len(fparts) > 1):
                            fts = fparts[1]
                            if (fts < timestamp): blist.append(backupfile)
                    blist.sort(reverse=True)
                    if (self.debug): sys.stderr.write("%s\n" % blist)
                    maxindx = __MAX_BACKUP_FILES__ -1
                    if (len(blist) >= __MAX_BACKUP_FILES__):
                        for bfile in blist[maxindx:]:
                            bfp = os.path.join(bfd,bfile)
                            if (self.debug): sys.stderr.write("Removing %s\n" % bfp)
                            os.remove(bfp)
                except:
                    sys.stderr.write("Cannot read CRIC data\n")
                    asinfo = None
                    json_site_data = None

            if (asinfo):
                try:
                    if (self.debug): sys.stderr.write("Reading CRIC site data from %s\n" % asinfo)
                    cric_site_info = open(asinfo,'r')
                    json_site_data = cric_site_info.read()
                    cric_site_info.close()
                except:
                    json_site_data = None

        # Static site info
        if (os.path.exists(__CRIC_STATIC_SITE_INFO__)): assinfo = __CRIC_STATIC_SITE_INFO__
        elif (os.path.exists(os.path.basename(__CRIC_STATIC_SITE_INFO__))): assinfo = os.path.basename(__CRIC_STATIC_SITE_INFO__)
        elif (os.path.exists(os.path.expanduser("~/.%s" % os.path.basename(__CRIC_STATIC_SITE_INFO__)))): assinfo = os.path.expanduser("~/.%s" % os.path.basename(__CRIC_STATIC_SITE_INFO__))

        if (assinfo):
            try:
                cric_static_site_info = open(assinfo,'r')
                json_static_site_data = cric_static_site_info.read()
                cric_static_site_info.close()
                if (self.debug): sys.stderr.write("Loading CRIC static_site data from %s\n" % assinfo)
                cric_static_site_data = json.loads(json_static_site_data)
                if (self.debug): sys.stderr.write("CRIC static site data loaded from %s\n" % assinfo)
            except:
                cric_static_site_data = []
                sys.stderr.write("Cannot read CRIC static site info\n")

        if (json_site_data):
            try:
                if (self.debug): sys.stderr.write("Loading CRIC site data\n")
                cric_site_data = json.loads(json_site_data)
                if (self.debug): sys.stderr.write("CRIC site data loaded\n")
                if (type(cric_site_data) == type({}) and 'error' in cric_site_data): cric_site_data = []
            except:
                sys.stderr.write("Cannot read CRIC site info\n")
                raise

        if (cric_static_site_data): cric_site_data = cric_static_site_data + cric_site_data

        return cric_site_data

    def getCricDataOverrides(self,site=None):
        # Get the json extra data from an override file
        ovrinfo = None
        cric_site_data = {}
        cric_override_site_data = []

        # Override site info
        if (os.path.exists(__CRIC_OVERRIDE_SITE_INFO__)): ovrinfo = __CRIC_OVERRIDE_SITE_INFO__
        elif (os.path.exists(os.path.basename(__CRIC_OVERRIDE_SITE_INFO__))): ovrinfo = os.path.basename(__CRIC_OVERRIDE_SITE_INFO__)
        elif (os.path.exists(os.path.expanduser("~/.%s" % os.path.basename(__CRIC_OVERRIDE_SITE_INFO__)))): ovrinfo = os.path.expanduser("~/.%s" % os.path.basename(__CRIC_OVERRIDE_SITE_INFO__))

        if (ovrinfo):
            try:
                cric_site_info = open(ovrinfo,'r')
                json_site_data = cric_site_info.read()
                cric_site_info.close()
                if (self.debug): sys.stderr.write("Loading CRIC override data from %s\n" % ovrinfo)
                cric_site_data = json.loads(json_site_data)
                if (self.debug): sys.stderr.write("CRIC override site data loaded from %s\n" % ovrinfo)
            except:
                cric_site_data = []
                sys.stderr.write("Cannot read CRIC override site info\n")

        if (site and site in cric_site_data.keys()):
            cric_override_site_data = cric_site_data[site]

        return cric_override_site_data

    def getCricSchedconf(self,pandares=None):
        # Get the json files from CRIC
        ascinfo = None
        cric_schedconf_data = []
        json_schedonf_data = None

        if (os.path.exists(__CRIC_SCHEDCONF__)):
            try:
                ascinfo = __CRIC_SCHEDCONF__
                if (self.debug): sys.stderr.write("Reading CRIC schedconf data from %s\n" % ascinfo)
                cric_schedconf_info = open(ascinfo,'r')
                json_schedconf_data = cric_schedconf_info.read()
                cric_schedconf_info.close()
            except:
                if (self.debug): sys.stderr.write("Failed to read CRIC schedconf data from %s\n" % ascinfo)
                json_schedconf_data = None
        else:
            if (self.debug): sys.stderr.write("Cannot find %s\n" % __CRIC_SCHEDCONF__)
            json_schedconf_data = None

        if (json_schedconf_data):
            try:
                if (self.debug): sys.stderr.write("Loading CRIC schedconf data\n")
                cric_schedconf_data = json.loads(json_schedconf_data)
                if (self.debug): sys.stderr.write("CRIC schedconf data loaded\n")
                if (type(cric_schedconf_data) == type({}) and 'error' in cric_schedconf_data): cric_schedconf_data = []
            except:
                sys.stderr.write("Cannot read CRIC schedconf info\n")

        return cric_schedconf_data

    def getFSConf(self, site=None, maxserv=8, force_proxyconfig=False):
        fsconf = ""
        fserv_patt = re.compile("http://([^.]+).([^:/]*).*")
        cric_site_data = self.getCricData(site)
        if (self.debug): sys.stderr.write("Searching site %s\n" % site)
        for site_name in cric_site_data.keys():
            if (site_name == site):
                site_data = cric_site_data[site_name]
                site_data_overrides = self.getCricDataOverrides(site)
                bproxy_map = []
                has_proxyconfig = None
                if (force_proxyconfig): has_proxyconfig = True
                elif ("has_proxyconfig" in site_data_overrides): has_proxyconfig = site_data_overrides["has_proxyconfig"]
                elif ("has_proxyconfig" in site_data): has_proxyconfig = site_data["has_proxyconfig"]
                if (self.debug): sys.stderr.write("Proxyconfig for site %s is %s\n" % (site, has_proxyconfig))
                if (has_proxyconfig):
                    if (site_data_overrides and "fsconf" in site_data_overrides and "proxyconfig" in site_data_overrides["fsconf"]):
                      fsconf = "%s" % site_data_overrides["fsconf"]["proxyconfig"]
                    elif ("fsconf" in site_data and "proxyconfig" in site_data["fsconf"]):
                      fsconf = "%s" % site_data["fsconf"]["proxyconfig"]
                    else:
                      fsconf = __PROXY_DEFAULT_AUTOCONFIG__
                else:
                    if ("fsconf" in site_data):
                        fsconfdata = site_data["fsconf"]
                        if ("frontier" in fsconfdata):
                            # Count all items
                            fs_num = {}
                            tot_fs_num = 0
                            for fserv in fsconfdata["frontier"]:
                                fs_num[fserv[0]] = 1
                                if (len(fserv) >= 2): fs_num[fserv[0]] += len(fserv[1])
                                tot_fs_num += fs_num[fserv[0]]
                            if (tot_fs_num > maxserv):
                                factor = float(maxserv) / float(tot_fs_num)
                                tot_fs_num = 0
                                for dom in fs_num.keys():
                                    if (tot_fs_num < maxserv):
                                        fs_num[dom] = int(factor * fs_num[dom]) + 1
                                        if (tot_fs_num + fs_num[dom] > maxserv): fs_num[dom] = maxserv - tot_fs_num
                                        tot_fs_num += fs_num[dom]
                            for fserv in fsconfdata["frontier"]:
                                try:
                                    if (fserv_patt.match(fserv[0])):
                                        fdomain = fserv_patt.match(fserv[0]).group(2)
                                        if (__BPROXY_MAP__[fdomain] not in bproxy_map):
                                            bproxy_map.append(__BPROXY_MAP__[fdomain])
                                except:
                                    bproxy_map = __DEFAULT_BPROXIES__
                                fsconf += "(serverurl=%s)" % fserv[0]
                                if (len(fserv) >= 2):
                                    ns = 1
                                    if ("iteritems" in dir(fserv[1])):
                                        # Python 2
                                        fserv_info = fserv[1].iteritems()
                                    else:
                                        # Python 3
                                        fserv_info = fserv[1].items()
                                    for node,status in fserv_info:
                                        if (status == 'ACTIVE' and ns < fs_num[fserv[0]]):
                                            fsconf += "(serverurl=%s)" % node
                                            ns += 1
                                        else:
                                            if (self.debug): sys.stderr.write("SKIP serverurl %s" % node)
                        if ("squid" in fsconfdata):
                            for fsquid in fsconfdata["squid"]:
                                fsconf += "(proxyurl=%s)" % fsquid[0]
                                if (len(fsquid) >= 2):
                                    if ("iteritems" in dir(fsquid[1])):
                                        # Python 2
                                        fsquid_info = fsquid[1].iteritems()
                                    else:
                                        # Python 3
                                        fsquid_info = fsquid[1].items()
                                    for node,status in fsquid_info:
                                        if (status == 'ACTIVE'): fsconf += "(proxyurl=%s)" % node
                        if (site_data_overrides and "preferipfamily" in site_data_overrides["fsconf"]):
                            fsconf += "(preferipfamily=%s)" % site_data_overrides["fsconf"]["preferipfamily"]
                        elif ("preferipfamily" in fsconfdata):
                            fsconf += "(preferipfamily=%s)" % fsconfdata["preferipfamily"]
                        if (fsconf and bproxy_map):
                            bproxies = ""
                            for bproxy in bproxy_map:
                                bproxies += "(proxyurl=%s)" % bproxy
                            if (len(bproxy_map) < 2):
                                for bproxy in __DEFAULT_BPROXIES__:
                                    if (bproxy not in bproxy_map):
                                        bproxies += "(proxyurl=%s)" % bproxy
                            fsconf += bproxies
                            break
        return fsconf

    def getSiteName(self, pandares=None):
        if (pandares):
            cric_site_data = self.getCricData()
            if (self.debug): sys.stderr.write("Searching resource %s\n" % pandares)
            for sitename in cric_site_data.keys():
                site_data = cric_site_data[sitename]
                if (self.debug): sys.stderr.write("Scanning site %s\n" % sitename)
                if ("presources" in site_data):
                    for pandasite in site_data["presources"].keys():
                        for pres in site_data["presources"][pandasite]:
                            if (self.debug):  sys.stderr.write("Checking %s=%s" % (pres, pandares))
                            if (pres == pandares): return sitename
        return None

    def getCoreCount(self, pandares=None):
        if (pandares):
            cric_sc_data = self.getCricSchedconf()
            if (self.debug): sys.stderr.write("Searching resource %s\n" % pandares)
            for sc_data in cric_sc_data:
                if (cric_sc_data[sc_data]["panda_resource"] == pandares):
                    if ("corecount" in cric_sc_data[sc_data] and cric_sc_data[sc_data]["corecount"] is not None):
                        return cric_sc_data[sc_data]["corecount"]
                    else:
                        return 1
        return None

    def getJobManager(self, pandares=None):
        if (pandares):
            cric_sc_data = self.getCricSchedconf()
            if (self.debug): sys.stderr.write("Searching resource %s\n" % pandares)
            for sc_data in cric_sc_data:
                if (cric_sc_data[sc_data]["panda_resource"] == pandares):
                    queues = cric_sc_data[sc_data]["queues"]
                    jm_list = []
                    for queue in queues:
                        if (queue["ce_jobmanager"] not in jm_list):
                            jm_list.append(queue["ce_jobmanager"])
                    jm_list.sort()
                    if (jm_list): return jm_list[0]
        return None

    def getResInfo(self, pandares=None):
        if (pandares):
            cric_sc_data = self.getCricSchedconf()
            if (self.debug): sys.stderr.write("Searching resource %s\n" % pandares)
            for sc_data in cric_sc_data:
                if (cric_sc_data[sc_data]["panda_resource"] == pandares):
                    return cric_sc_data[sc_data]
        return None

    def getID(self, site=None):
        id = None
        cric_site_data = self.getCricData(site)
        patts = (
                  re.compile('.*_SCRATCHDISK')
                , re.compile('.*_DATADISK')
                )
        exclude_patt = re.compile('.*TAPE')
        last_ep = None
        for site_name in cric_site_data.keys():
            if (site_name == site):
                site_data = cric_site_data[site_name]
                if ("ddmendpoints" in site_data):
                    for p in patts:
                        for ep in site_data["ddmendpoints"].keys():
                            if (p.match(ep)):
                                id = ep
                                break
                            else:
                                if (not exclude_patt.match(ep)): last_ep = ep
                        if (id): break
                if (id): break
        if (not id and last_ep): id = last_ep
        return id

    def getSEinfo(self, site=None, endpoint=None):
        seinfo = None
        if (site and endpoint):
            cric_site_data = self.getCricData(site)
            for sitename in cric_site_data.keys():
                if (sitename == site):
                    site_data = cric_site_data[sitename]
                    if ("ddmendpoints" in site_data):
                        ddmepdata = site_data["ddmendpoints"]
                        if (endpoint in ddmepdata):
                            seinfo = ddmepdata[endpoint]["se_impl"]
                    if (seinfo): break
        return seinfo

    def getProxyconfig(self, site=None, force_proxyconfig=False):
        cric_site_data = self.getCricData(site)
        if (self.debug): sys.stderr.write("Searching proxyconfig for site %s\n" % site)
        has_proxyconfig = None
        for site_name in cric_site_data.keys():
            if (site_name == site):
                site_data = cric_site_data[site_name]
                if (force_proxyconfig): has_proxyconfig = True
                elif ("has_proxyconfig" in site_data): has_proxyconfig = site_data["has_proxyconfig"]
        return has_proxyconfig


cricinfo = cricSiteInfo()
mode = None
site = None
endpoint = None
maxserv = 8
force_proxyconfig = False
rc   = 0

if __name__ == "__main__":
    # Get the CLI options
    try:
        opts, args = getopt.getopt(sys.argv[1:],
                     short_options,
                     long_options,
                     )
    except getopt.GetoptError:
        # Print the help
        print (__HELP__)
        sys.exit(-1)
    for cmd, arg in opts:
        if (cmd in ('--help',) or cmd in ('-h',)):
            print (__HELP__)
            sys.exit()
        elif (cmd in ('--corecount',) or cmd in ('-c',)):
            mode = "corecount"
            pandares = arg
        elif (cmd in ('--debug',) or cmd in ('-d',)):
            cricinfo.setDebug(True)
        elif (cmd in ('--endpoint',) or cmd in ('-e',)):
            endpoint = arg
        elif (cmd in ('--fsconf',) or cmd in ('-f',)):
            mode = "fsconf"
        elif (cmd in ('--has-proxyconfig',) or cmd in ('-P',)):
            mode = "get-proxyconfig"
        elif (cmd in ('--id',) or cmd in ('-i',)):
            mode = "id"
        elif (cmd in ('--jobmanager',) or cmd in ('-j',)):
            mode = "jobmanager"
            pandares = arg
        elif (cmd in ('--proxyconfig',) or cmd in ('-p',)):
            force_proxyconfig = True
        elif (cmd in ('--queues',) or cmd in ('-q',)):
            mode = "queues"
            pandares = arg
        elif (cmd in ('--resinfo',) or cmd in ('-I',)):
            mode = "resinfo"
            pandares = arg
        elif (cmd in ('--maxfs',) or cmd in ('-m',)):
            maxserv = int(arg)
        elif (cmd in ('--seinfo',) or cmd in ('-S',)):
            mode = "seinfo"
        elif (cmd in ('--site',) or cmd in ('-s',)):
            site = arg
        elif (cmd in ('--show-site-name',) or cmd in ('-n',)):
            mode = "show-site-name"
            pandares = arg

    if (mode == "fsconf"):
        if (site):
            fsconf = cricinfo.getFSConf(site, maxserv, force_proxyconfig)
            if (fsconf): print (fsconf)
            else: rc = 10
        else:
            sys.stderr.write("No site specified\n")
            rc = 1

    if (mode == "get-proxyconfig"):
        if (site):
            has_proxyconfig = cricinfo.getProxyconfig(site, force_proxyconfig)
            if (has_proxyconfig): print ("true")
            else: print ("false")
        else:
            sys.stderr.write("No site specified\n")
            rc = 1

    if (mode == "corecount"):
        if (pandares):
            corecount = cricinfo.getCoreCount(pandares)
            if (corecount): print (corecount)
            else: rc = 10
        else:
            sys.stderr.write("No panda resource specified\n")
            rc = 1

    if (mode == "jobmanager"):
        if (pandares):
            jobmanager = cricinfo.getJobManager(pandares)
            if (jobmanager): print (jobmanager)
            else: rc = 10
        else:
            sys.stderr.write("No panda resource specified\n")
            rc = 1

    if (mode == "queues"):
        if (pandares):
            resinfo = cricinfo.getResInfo(pandares)
            if (resinfo["queues"]):
                for queue in resinfo["queues"]:
                    if (queue["ce_state"] == "ACTIVE"):
                        print ("%s %s %s" % (queue["ce_endpoint"],queue["ce_jobmanager"],queue["ce_queue_name"]))
            else: rc = 10
        else:
            sys.stderr.write("No panda resource specified\n")
            rc = 1

    if (mode == "resinfo"):
        if (pandares):
            res_info = cricinfo.getResInfo(pandares)
            if (res_info):
                queues = []
                for queue in res_info["queues"]:
                    if (queue["ce_state"] == "ACTIVE" and not (queue["ce_queue_name"],queue["ce_jobmanager"]) in queues): queues.append((queue["ce_queue_name"],queue["ce_jobmanager"]))
                queues.sort()
                if (queues):
                    for queue in queues:
                        print ("%s,%s,%s,%s,%s" % (res_info["atlas_site"],res_info["panda_site"],pandares,queue[1],queue[0]))
                elif ("jobmanager" in res_info):
                    print ("%s,%s,%s,%s,%s" % (res_info["atlas_site"],res_info["panda_site"],pandares,res_info["jobmanager"],res_info["jobmanager"]))
                else:
                    print ("%s,%s,%s,unknown,unknown" % (res_info["atlas_site"],res_info["panda_site"],pandares))
            else: rc = 10
        else:
            sys.stderr.write("No panda resource specified\n")
            rc = 1

    if (mode == "show-site-name"):
        if (pandares):
            sitename = cricinfo.getSiteName(pandares)
            if (sitename): print (sitename)
            else: rc = 10
        else:
            sys.stderr.write("No panda resource specified\n")
            rc = 1

    if (mode == "seinfo"):
        if (site and endpoint):
            seinfo = cricinfo.getSEinfo(site, endpoint)
            if (seinfo): print (seinfo)
            else: rc = 10
        else:
            sys.stderr.write("No site or endpoint specified\n")
            rc = 1

    if (mode == "id"):
        if (site):
            id = cricinfo.getID(site)
            if (id): print (id)
            else: rc = 10
        else:
            sys.stderr.write("No site specified\n")
            rc = 1

    sys.exit(rc)
