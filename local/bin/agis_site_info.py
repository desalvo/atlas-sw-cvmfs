#!/usr/bin/env python
#####################################################################
# AGIS site info tool                                               #
# LJSFi Framework 2.0.0                                             #
# Alessandro De Salvo <Alessandro.DeSalvo@roma1.infn.it> - 20140212 #
#####################################################################

__version__ = "$Revision: 1.3 $"[11:-1]

__HELP__="""AGIS site info tool %s.
Usage: agis-site-info [OPTION]

Options:
  --help                        Display this help and exit.
  --debug | -d                  Debug mode
  --corecount | -c <pres>       Core count for panda resource <pres>
  --endpoint | -e <name>        Endpoint name
  --fsconf | -f                 Show frontier setup
  --id | -i                     Show the site id
  --jobmanages | -j <pres>      Show the jobmanager type for the panda resource <pres>
  --maxfs | -m <num>            Do not allow more than <num> serverurls for Frontier
  --queues | -q <pres>          Show queues data for panda resource <pres>
  --resinfo | -I <pres>         Show info on panda resource <pres>
  --setype | -S                 Show the SE type of a give endpoint
  --site | -s <sitename>        Site name
  --show-site-name | -n <pres>  Show the site name of the panda resource <pres>

Alessandro De Salvo <Alessandro.DeSalvo@roma1.infn.it>.
"""

try:
    import json
except:
    import simplejson as json
import os, sys, commands
import time
import getopt
import string
import re
try:
    import hashlib
except:
    import md5 as hashlib

__AGIS_SITE_INFO__ = "http://atlas-agis-api-0.cern.ch/request/site/query/list/?json"
__AGIS_SITE_INFO_SITE__ = "http://atlas-agis-api-0.cern.ch/request/site/query/list/?json&site=%s"
__AGIS_SITE_INFO_CACHE__ = "http://atlas-agis-api.cern.ch/jsoncache/list_sites.json"
__CURL_EXEC__ = "curl -S --connect-timeout 60 -o '%s' '%s' 2>/dev/null"
__CACHE_FILE__ = "/var/tmp/.agisinfo_%s/agis-site-info" % os.getuid()
__CACHE_EXPIRY__ = 3600
__STALE_TMPFILE__ = 200
__TMPFILE__     = "%s.tmp" % __CACHE_FILE__
__MAX_BACKUP_FILES__ = 10
__BPROXY_MAP__ = {
                       "cern.ch": "http://atlasbpfrontier.cern.ch:3127",
                       "gridpp.rl.ac.uk": "http://atlasbpfrontier.cern.ch:3127",
                       "lcg.triumf.ca": "http://atlasbpfrontier.fnal.gov:3127",
                       "in2p3.fr": "http://atlasbpfrontier.cern.ch:3127",
                     }
__DEFAULT_BPROXIES__ = ["http://atlasbpfrontier.cern.ch:3127","http://atlasbpfrontier.fnal.gov:3127"]

if (os.environ.has_key("VO_ATLAS_SW_DIR")):
    __DEFAULT_AGIS_SITE_INFO__ = "%s/local/etc/agis_site_info.json" % os.environ["VO_ATLAS_SW_DIR"]
    __AGIS_STATIC_SITE_INFO__ = "%s/local/etc/agis_static_site_info.json" % os.environ["VO_ATLAS_SW_DIR"]
    __AGIS_SCHEDCONF__ = "%s/local/etc/agis_schedconf.json" % os.environ["VO_ATLAS_SW_DIR"]
else:
    #sys.stderr.write("No VO_ATLAS_SW_DIR set, using /cvmfs/atlas.cern.ch/repo/sw\n")
    __DEFAULT_AGIS_SITE_INFO__ = "/cvmfs/atlas.cern.ch/repo/sw/local/etc/agis_site_info.json"
    __AGIS_STATIC_SITE_INFO__ = "/cvmfs/atlas.cern.ch/repo/sw/local/etc/agis_static_site_info.json"
    __AGIS_SCHEDCONF__ = "/cvmfs/atlas.cern.ch/repo/sw/local/etc/agis_schedconf.json"

short_options = "c:de:hfiI:j:m:n:q:Ss:"
long_options = ["corecount=","debug", "endpoint=", "fsconf", "help", "jobmanager=", "id", "maxfs=", "queues=", "resinfo=", "setype", "site=", "show-site-name="]

class agisSiteInfo:
    debug = False
    mode = None

    def setDebug(self, flag=False):
        self.debug = flag

    def getAgisData(self,site=None):
        # Get the json files from AGIS
        asinfo = None
        assinfo = None
        agis_site_data = []
        agis_static_site_data = []

        cachedir = os.path.dirname(__CACHE_FILE__)
        if (not os.path.exists(cachedir)): os.makedirs(cachedir)
        agisurl = __AGIS_SITE_INFO_CACHE__
        tmpfile = __TMPFILE__
        cachefile = __CACHE_FILE__
        timestamp = time.strftime('%s')
        cachebackup = "%s.%s" % (cachefile,timestamp)
        json_site_data = None

        if (os.path.exists(__DEFAULT_AGIS_SITE_INFO__)):
            try:
                asinfo = __DEFAULT_AGIS_SITE_INFO__
                if (self.debug): sys.stderr.write("Reading AGIS site data from %s\n" % asinfo)
                agis_site_info = open(asinfo,'r')
                json_site_data = agis_site_info.read()
                agis_site_info.close()
            except:
                if (self.debug): sys.stderr.write("Failed to read AGIS site data from %s\n" % asinfo)
                json_site_data = None

        if (not json_site_data):
            asinfo = cachefile
            refresh = True
            if (os.path.exists(cachefile)):
                now = time.time()
                st = os.stat(cachefile)
                if ((now - st.st_mtime) < __CACHE_EXPIRY__): refresh = False
            if (not refresh):
                if (self.debug): sys.stderr.write("Using cached AGIS data\n")
            else:
                if (self.debug): sys.stderr.write("Refreshing AGIS data\n")
                try:
                    if (self.debug): sys.stderr.write("Getting AGIS site data from %s\n" % agisurl)
                    s,o = commands.getstatusoutput(__CURL_EXEC__ % (tmpfile, agisurl))
                    if (s != 0):
                        print o
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
                    sys.stderr.write("Cannot read AGIS data\n")
                    asinfo = None
                    json_site_data = None

            if (asinfo):
                try:
                    if (self.debug): sys.stderr.write("Reading AGIS site data from %s\n" % asinfo)
                    agis_site_info = open(asinfo,'r')
                    json_site_data = agis_site_info.read()
                    agis_site_info.close()
                except:
                    json_site_data = None

        if (os.path.exists(__AGIS_STATIC_SITE_INFO__)): assinfo = __AGIS_STATIC_SITE_INFO__
        elif (os.path.exists(os.path.basename(__AGIS_STATIC_SITE_INFO__))): assinfo = os.path.basename(__AGIS_STATIC_SITE_INFO__)
        elif (os.path.exists("~/.%s" % os.path.basename(__AGIS_STATIC_SITE_INFO__))): assinfo = "~/.%s" % os.path.basename(__AGIS_STATIC_SITE_INFO__)

        if (assinfo):
            try:
                agis_static_site_info = open(assinfo,'r')
                json_static_site_data = agis_static_site_info.read()
                agis_static_site_info.close()
                if (self.debug): sys.stderr.write("Loading AGIS static_site data from %s\n" % assinfo)
                agis_static_site_data = json.loads(json_static_site_data)
                if (self.debug): sys.stderr.write("AGIS static site data loaded from %s\n" % assinfo)
            except:
                agis_static_site_data = []
                sys.stderr.write("Cannot read AGIS static site info\n")

        if (json_site_data):
            try:
                if (self.debug): sys.stderr.write("Loading AGIS site data\n")
                agis_site_data = json.loads(json_site_data)
                if (self.debug): sys.stderr.write("AGIS site data loaded\n")
                if (type(agis_site_data) == type({}) and agis_site_data.has_key('error')): agis_site_data = []
            except:
                sys.stderr.write("Cannot read AGIS site info\n")
                raise

        if (agis_static_site_data): agis_site_data = agis_static_site_data + agis_site_data

        return agis_site_data

    def getAgisSchedconf(self,pandares=None):
        # Get the json files from AGIS
        ascinfo = None
        agis_schedconf_data = []
        json_schedonf_data = None

        if (os.path.exists(__AGIS_SCHEDCONF__)):
            try:
                ascinfo = __AGIS_SCHEDCONF__
                if (self.debug): sys.stderr.write("Reading AGIS schedconf data from %s\n" % ascinfo)
                agis_schedconf_info = open(ascinfo,'r')
                json_schedconf_data = agis_schedconf_info.read()
                agis_schedconf_info.close()
            except:
                if (self.debug): sys.stderr.write("Failed to read AGIS schedconf data from %s\n" % ascinfo)
                json_schedconf_data = None

        if (json_schedconf_data):
            try:
                if (self.debug): sys.stderr.write("Loading AGIS schedconf data\n")
                agis_schedconf_data = json.loads(json_schedconf_data)
                if (self.debug): sys.stderr.write("AGIS schedconf data loaded\n")
                if (type(agis_schedconf_data) == type({}) and agis_schedconf_data.has_key('error')): agis_schedconf_data = []
            except:
                sys.stderr.write("Cannot read AGIS schedconf info\n")

        return agis_schedconf_data

    def getFSConf(self, site=None, maxserv=8):
        fsconf = ""
        fserv_patt = re.compile("http://([^.]+).([^:/]*).*")
        agis_site_data = self.getAgisData(site)
        if (self.debug): sys.stderr.write("Searching site %s\n" % site)
        for site_data in agis_site_data:
            if (site_data["name"] == site):
                bproxy_map = []
                if (site_data.has_key("fsconf")):
                    fsconfdata = site_data["fsconf"]
                    if fsconfdata.has_key("frontier"):
                        # Count all items
                        fs_num = {}
                        tot_fs_num = 0
                        for fserv in fsconfdata["frontier"]:
                            fs_num[fserv[0]] = 1
                            if (len(fserv) == 2): fs_num[fserv[0]] += len(fserv[1])
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
                            if (len(fserv) == 2):
                                ns = 1
                                for node,status in fserv[1].iteritems():
                                    if (status == 'ACTIVE' and ns < fs_num[fserv[0]]):
                                        fsconf += "(serverurl=%s)" % node
                                        ns += 1
                                    else:
                                        if (self.debug): sys.stderr.write("SKIP serverurl %s" % node)
                    if fsconfdata.has_key("squid"):
                        for fsquid in fsconfdata["squid"]:
                            fsconf += "(proxyurl=%s)" % fsquid[0]
                            if (len(fsquid) == 2):
                                for node,status in fsquid[1].iteritems():
                                    if (status == 'ACTIVE'): fsconf += "(proxyurl=%s)" % node
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
            agis_site_data = self.getAgisData()
            if (self.debug): sys.stderr.write("Searching resource %s\n" % pandares)
            for site_data in agis_site_data:
                sitename = site_data["name"]
                if (self.debug): sys.stderr.write("Scanning site %s\n" % sitename)
                if (site_data.has_key("presources")):
                    for pandasite in site_data["presources"].keys():
                        for pres in site_data["presources"][pandasite]:
                            if (pres == pandares): return sitename
        return None

    def getCoreCount(self, pandares=None):
        if (pandares):
            agis_sc_data = self.getAgisSchedconf()
            if (self.debug): sys.stderr.write("Searching resource %s\n" % pandares)
            for sc_data in agis_sc_data:
                if (agis_sc_data[sc_data]["panda_resource"] == pandares):
                    if (agis_sc_data[sc_data].has_key("corecount") and agis_sc_data[sc_data]["corecount"] is not None):
                        return agis_sc_data[sc_data]["corecount"]
                    else:
                        return 1
        return None

    def getJobManager(self, pandares=None):
        if (pandares):
            agis_sc_data = self.getAgisSchedconf()
            if (self.debug): sys.stderr.write("Searching resource %s\n" % pandares)
            for sc_data in agis_sc_data:
                if (agis_sc_data[sc_data]["panda_resource"] == pandares):
                    queues = agis_sc_data[sc_data]["queues"]
                    jm_list = []
                    for queue in queues:
                        if (queue["ce_jobmanager"] not in jm_list):
                            jm_list.append(queue["ce_jobmanager"])
                    jm_list.sort()
                    if (jm_list): return jm_list[0]
        return None

    def getResInfo(self, pandares=None):
        if (pandares):
            agis_sc_data = self.getAgisSchedconf()
            if (self.debug): sys.stderr.write("Searching resource %s\n" % pandares)
            for sc_data in agis_sc_data:
                if (agis_sc_data[sc_data]["panda_resource"] == pandares):
                    return agis_sc_data[sc_data]
        return None

    def getID(self, site=None):
        id = None
        agis_site_data = self.getAgisData(site)
        patts = (
                  re.compile('.*_SCRATCHDISK')
                , re.compile('.*_DATADISK')
                )
        exclude_patt = re.compile('.*TAPE')
        last_ep = None
        for site_data in agis_site_data:
            if (site_data["name"] == site):
                if (site_data.has_key("ddmendpoints")):
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
            agis_site_data = self.getAgisData(site)
            for site_data in agis_site_data:
                if (site_data["name"] == site):
                    if (site_data.has_key("ddmendpoints")):
                        ddmepdata = site_data["ddmendpoints"]
                        if (ddmepdata.has_key(endpoint)):
                            seinfo = ddmepdata[endpoint]["se_impl"]
                    if (seinfo): break
        return seinfo


agisinfo = agisSiteInfo()
mode = None
site = None
endpoint = None
maxserv = 8
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
        print __HELP__
        sys.exit(-1)
    for cmd, arg in opts:
        if (cmd in ('--help',) or cmd in ('-h',)):
            print __HELP__
            sys.exit()
        elif (cmd in ('--corecount',) or cmd in ('-c',)):
            mode = "corecount"
            pandares = arg
        elif (cmd in ('--debug',) or cmd in ('-d',)):
            agisinfo.setDebug(True)
        elif (cmd in ('--endpoint',) or cmd in ('-e',)):
            endpoint = arg
        elif (cmd in ('--fsconf',) or cmd in ('-f',)):
            mode = "fsconf"
        elif (cmd in ('--id',) or cmd in ('-i',)):
            mode = "id"
        elif (cmd in ('--jobmanager',) or cmd in ('-j',)):
            mode = "jobmanager"
            pandares = arg
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
            fsconf = agisinfo.getFSConf(site, maxserv)
            if (fsconf): print fsconf
            else: rc = 10
        else:
            sys.stderr.write("No site specified\n")
            rc = 1

    if (mode == "corecount"):
        if (pandares):
            corecount = agisinfo.getCoreCount(pandares)
            if (corecount): print corecount
            else: rc = 10
        else:
            sys.stderr.write("No panda resource specified\n")
            rc = 1

    if (mode == "jobmanager"):
        if (pandares):
            jobmanager = agisinfo.getJobManager(pandares)
            if (jobmanager): print jobmanager
            else: rc = 10
        else:
            sys.stderr.write("No panda resource specified\n")
            rc = 1

    if (mode == "queues"):
        if (pandares):
            resinfo = agisinfo.getResInfo(pandares)
            if (resinfo["queues"]):
                for queue in resinfo["queues"]:
                    if (queue["ce_state"] == "ACTIVE"):
                        print "%s %s %s" % (queue["ce_endpoint"],queue["ce_jobmanager"],queue["ce_queue_name"])
            else: rc = 10
        else:
            sys.stderr.write("No panda resource specified\n")
            rc = 1

    if (mode == "resinfo"):
        if (pandares):
            res_info = agisinfo.getResInfo(pandares)
            if (res_info):
                queues = []
                for queue in res_info["queues"]:
                    if (queue["ce_state"] == "ACTIVE" and not (queue["ce_queue_name"],queue["ce_jobmanager"]) in queues): queues.append((queue["ce_queue_name"],queue["ce_jobmanager"]))
                queues.sort()
                if (queues):
                    for queue in queues:
                        print "%s,%s,%s,%s,%s" % (res_info["atlas_site"],res_info["panda_site"],pandares,queue[1],queue[0])
                elif (res_info.has_key("jobmanager")):
                    print "%s,%s,%s,%s,%s" % (res_info["atlas_site"],res_info["panda_site"],pandares,res_info["jobmanager"],res_info["jobmanager"])
                elif (res_info.has_key("jobmanager")):
                    print "%s,%s,%s,unknown,unknown" % (res_info["atlas_site"],res_info["panda_site"],pandares)
            else: rc = 10
        else:
            sys.stderr.write("No panda resource specified\n")
            rc = 1

    if (mode == "show-site-name"):
        if (pandares):
            sitename = agisinfo.getSiteName(pandares)
            if (sitename): print sitename
            else: rc = 10
        else:
            sys.stderr.write("No panda resource specified\n")
            rc = 1

    if (mode == "seinfo"):
        if (site and endpoint):
            seinfo = agisinfo.getSEinfo(site, endpoint)
            if (seinfo): print seinfo
            else: rc = 10
        else:
            sys.stderr.write("No site or endpoint specified\n")
            rc = 1

    if (mode == "id"):
        if (site):
            id = agisinfo.getID(site)
            if (id): print id
            else: rc = 10
        else:
            sys.stderr.write("No site specified\n")
            rc = 1

    sys.exit(rc)
