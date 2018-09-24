#!/usr/bin/env python
"""
    get Frontier/Squid Environment and other site informations
    from ATLAS Grid Information System or DQ2 ToA if no AGIS clients
    are available

@author: Alessandro De Salvo, Florentin Bujor
@contact: Alessandro.De.Salvo@cern.ch, florentin.bujor@cern.ch
@ $Id: getFrontierEnv.py 128 2012-03-01 15:23:12Z florentin.bujor $
"""

import sys
import getopt
import os
import ConfigParser
import re
import string
try:
  from agis.api.AGIS import AGIS
  from agis.utils.exceptions import *
except:
  AGIS = None
try:
  import dq2.info.TiersOfATLAS as ToA
  fsquidmap=ToA.ToACache.fsquidmap
except:
  ToA = None

def getFrontierEnvDQ2(gocname):
  # Build the FRONTIER_SERVER env from the mapped servers and squids
  # Eg.
  # FRONTIER_SERVER="(serverurl=http://atlassq1-fzk.gridka.de:8021/fzk)
  #  (serverurl=http://squid-frontier.usatlas.bnl.gov:23128/frontieratbnl)
  #  (proxyurl=http://atlasvobox.lcg.cscs.ch:3128)
  #  (proxyurl=http://lcg-lrz-vobox.grid.lrz-muenchen.de:3128)"
  #
  fenv=''
  if fsquidmap.has_key(gocname):
    # First the frontier server(s)   
    for f in fsquidmap[gocname]['frontiers']:
      if f.find('http') == 0:
        fenv+='(serverurl=%s)'%f
      else:
        sys.stderr.write("Frontier url does not start with http...: %s\n" % f)

    # Then the Squid(s)
    for s in fsquidmap[gocname]['squids']:
      surl=''  
      if s=='local':
        if fsquidmap[gocname].has_key('mysquid'):
          surl=fsquidmap[gocname]['mysquid']
      else:
        if fsquidmap[s].has_key('mysquid'):
          surl=fsquidmap[s]['mysquid']
        else:
          sys.stderr.write("Configured remote Squid site %s has no squid\n!" % s)

      if surl.find('http') == 0:
        fenv+='(proxyurl=%s)'%surl
      else:
        sys.stderr.write("Squid url does not start with http...: %s\n" % surl)
  return fenv


def getFrontierEnvAGIS(site_name):
  try: #try if the site is defined in AGIS 
    site_configuration = a.list_fsconfigurations(site_name=site_name)

    try: #try if the primary frontier is defined  
      #Primary FRONTIER ###
      pfrontier = site_configuration[site_name].frontier.endpoint
      #Backup FRONTIER ###
      bfrontier = a.list_frontier_services(site = site_configuration[site_name].fbackup_sites)[0].endpoint
      #Primary SQUID ###
      try: #try if primary squid is defined
        psquid = a.list_squid_services(site=site_name)[0].endpoint
      #Backup SQUIDS ###
        bs = site_configuration[site_name].sbackup_sites
        if bs != []: #check of any backup squid defined
          bsquid = a.list_squid_services(site = site_configuration[site_name].sbackup_sites)[0].endpoint
          return 0, "(serverurl=%s)(serverurl=%s)(proxyurl=%s)(proxyurl=%s)" % (pfrontier,bfrontier,psquid,bsquid)
        else:
          return 0, "(serverurl=%s)(serverurl=%s)(proxyurl=%s)" % (pfrontier,bfrontier,psquid)
      except: #no primary squid defined
        bs = site_configuration[site_name].sbackup_sites
        no_bs = len(bs)
        if no_bs == 1:
          bsquid = a.list_squid_services(site = site_configuration[site_name].sbackup_sites)[0].endpoint
          return 0, "(serverurl=%s)(serverurl=%s)(proxyurl=%s)" % (pfrontier,bfrontier,bsquid)
        else:
          bsquid1 = a.list_squid_services(site = site_configuration[site_name].sbackup_sites)[0].endpoint
          bsquid2 = a.list_squid_services(site = site_configuration[site_name].sbackup_sites)[1].endpoint
          return 0, "(serverurl=%s)(serverurl=%s)(proxyurl=%s)(proxyurl=%s)" % (pfrontier,bfrontier,bsquid1,bsquid2)
    except Exception, mm: #no primary frontier defined
      return 1, "Empty record for site: %s" % mm
  except AGISException, m: #AGIS NonExistsException; the site is not present/defined in AGIS
    return 2, "ERROR: %s" % m


def getConfig(conffile,sitename,service):
    config = ConfigParser.ConfigParser()
    try:
        config.read(conffile)
        if (config.has_section(sitename)):
            if (config.has_option(sitename, service)):
                return config.get(sitename, service)
    except:
        pass
    return ''


short_options = "dFf:lLp:rsh"
long_options  = ["debug", "frontier", "help", "file=", "list-proto", "proto=", "regexp", "setype", "siteid", "agis", "dq2"]
__HELP__="""Frontier Setup helper %s.
Usage: %s [OPTION] [sitename]

Options:
  --help                        display this help and exit.
  --debug         | -d          debug mode
  --frontier      | -F          get frontier settings
  --file          | -f <file>   Use <file> to get the site list
  --list-proto    | -l          display the supported SE protocols
  --proto=<proto> | -p <proto>  use the <proto> protocol
  --regexp        | -r          display the SURL to TURL regexp
                                for a specific protocol (needs --proto)
  --setype        | -s          display the SE type
  --siteid        | -L          display the local site ID
  --agis
  --dq2
Alessandro De Salvo <Alessandro.DeSalvo@roma1.infn.it>,
Florentin Bujor <florentin.bujor@cern.ch>.
"""

__version__ = "$Revision: 2.1 $"[11:-1]

conffile="auto-setup.conf"
if (os.environ.has_key('VO_ATLAS_SW_DIR')): conffile=os.path.join(os.environ['VO_ATLAS_SW_DIR'],'local','etc',conffile)

debug = False

def usage():
  progName = os.path.basename(sys.argv[0])
  print __HELP__ % (__version__.strip(),progName)


if __name__ == "__main__":

  #if (AGIS): a = AGIS(hostp='atlas-agis-api-dev.cern.ch:80')
  if (AGIS): a = AGIS(hostp='atlas-agis-api.cern.ch:80')
  ATLAS_site_name = None
  site_name_list_file = None
  debug = False

  mode = 'frontier'
  location = None
  info_source = None
  proto = None
  try:
    opts, args = getopt.getopt(sys.argv[1:], short_options, long_options)
  except getopt.GetoptError:
    usage()
    sys.exit(-1)
  for cmd, arg in opts:
    if (cmd in ('--help',) or cmd in ('-h',)):
      usage()
      sys.exit()
    elif (cmd in ('--debug',) or cmd in ('-d',)):
      debug = True
    elif (cmd in ('--file',) or cmd in ('-f',)):
      site_name_list_file = arg
    elif (cmd in ('--frontier',) or cmd in ('-F',)):
      mode = 'frontier'
    elif (cmd in ('--setype',) or cmd in ('-s',)):
      mode = 'setype'
    elif (cmd in ('--list-proto',) or cmd in ('-l',)):
      mode = 'listproto'
    elif (cmd in ('--proto',) or cmd in ('-p',)):
      proto = arg
    elif (cmd in ('--regexp',) or cmd in ('-r',)):
      mode = 'regexp'
    elif (cmd in ('--siteid',) or cmd in ('-L',)):
      mode = 'siteid'
    elif (cmd in ('--agis',)):
      info_source = 'AGIS'
    elif (cmd in ('--dq2',)):
      info_source = 'DQ2'

  if (len(sys.argv) > 1): location = sys.argv[len(sys.argv)-1]  

  #print info_source 

  if (info_source == 'AGIS'):
    ToA = None
  elif (info_source == 'DQ2'):
    AGIS = None


  if (debug):
    if (AGIS): sys.stderr.write("AGIS clients loaded\n")
    if (ToA):  sys.stderr.write("DQ2 clients loaded\n")

  if (not ToA and not AGIS):
    sys.stderr.write("No AGIS or DQ2 clients available\n")
    sys.exit(2)

  rc = 0 
  if (mode == 'frontier'):
    if (AGIS):
      if (debug): sys.stderr.write("Using AGIS clients\n")
      if (site_name_list_file):
        inFILE = open(site_name_list_file,'r')
        for site in inFILE.read().split('\n'):
          fe = getConfig(conffile,site,'FRONTIER_SERVER')
          if (not fe): frc, fe = getFrontierEnvAGIS(site)
          if (frc == 0 and fe): print "%s: %s" % (site,fe)
          rc += frc
        inFILE.close() 
      elif (location):
        fe=getConfig(conffile,location,'FRONTIER_SERVER')
        if (not fe): frc, fe = getFrontierEnvAGIS(location)
        if (frc == 0 and fe): print fe
        rc += frc
    elif (ToA):
      if (debug): sys.stderr.write("Using DQ2 clients\n")
      if (location):
        fe=getConfig(conffile,location,'FRONTIER_SERVER')
        if (not fe): frc,fe=getFrontierEnvDQ2(location)
        if (not fe): frc,fe=getFrontierEnvDQ2(location.upper())
        if (frc == 0 and fe): print fe
        rc += frc
      else:
        for gn in fsquidmap.keys():
          frc,fe=getFrontierEnvDQ2(gn)
          print gn,fe
          rc += frc
  elif (mode == 'listproto'):
    if (ToA):
      if (location):
        seinfo = ToA.getSiteProperty(location.upper(), 'seinfo')
    elif (AGIS):
        seinfo = a.get_seinfo_entry()[location.upper()]
    else:
      sys.stderr.write("No AGIS or DQ2 clients available\n")
    if (seinfo and seinfo.has_key('protocols')):
      for p in seinfo['protocols']:
        print p[0]
  elif (mode == 'regexp'):
    if (ToA):
      if (location):
        seinfo = ToA.getSiteProperty(location.upper(), 'seinfo')
    elif (AGIS):
        seinfo = a.get_seinfo_entry()[location.upper()]
    else:
      sys.stderr.write("No AGIS or DQ2 clients available\n")
    if (seinfo and seinfo.has_key('protocols')):
      for p in seinfo['protocols']:
        if (p[1].has_key('regexp')):
          #if (proto):
            if (proto == p[0]):
              print p[1]['regexp']
              break
            else:
              print "%s:%s" % (p[0],p[1]['regexp'])
  elif (mode == 'siteid'):
    if (location and ToA):
      sitename = { location : None }
      output = ToA.resolveGOC(sitename)
      p = (
            re.compile('.*SCRATCHDISK')
          , re.compile('.*DATADISK')
          , re.compile('.*')
          )
      dq2sitename = [ None, None, None, None ]
      for site in output.keys():
        for name in output[site]:
          r = None
          for rank in range(0,3):
            if (p[rank].match(name)):
              r = rank
              break
          if (r is None): r = 3
          dq2sitename[r]=name
      for sn in dq2sitename:
        if (sn):
          print sn
          sys.exit(0)
      sn = getConfig(conffile,location,'LOCAL_SITE_ID')
      if (sn):
        print sn
      else:
        sys.exit(1)
  elif (mode == 'setype'):
    if (ToA):
      seinfo = ToA.getSiteProperty(location.upper(), 'seinfo')
    elif (AGIS):
      seinfo = a.get_seinfo_entry()[location.upper()]
    else:
      sys.stderr.write("No AGIS or DQ2 clients available\n")
    if (seinfo): print seinfo['setype']
  sys.exit(rc)
