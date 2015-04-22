#!/usr/bin/env python

import os, sys, getopt

TESTNAME="openconfig-bgp-juniper"

# generate bindings in this folder

def main():
  try:
    opts, args = getopt.getopt(sys.argv[1:], "k", ["keepfiles"])
  except getopt.GetoptError as e:
    print str(e)
    sys.exit(127)

  k = False
  for o, a in opts:
    if o in ["-k", "--keepfiles"]:
      k = True

  this_dir = os.path.dirname(os.path.realpath(__file__))
  os.system("/usr/local/bin/pyang --plugindir /Users/rjs/Code/pyangbind/btplugin \
    -f bt -o %s/bindings.py %s/%s.yang" % (this_dir, this_dir, TESTNAME))


  from bindings import openconfig_bgp_juniper

  global_config = {"my_as": 2856,}
  peer_group_list = ["groupA", "groupB"]
  peers = [("1.1.1.1", "groupA", 3741), ("1.1.1.2", "groupA", 5400,),
          ("1.1.1.3", "groupA", 29636), ("2.2.2.2", "groupB", 12767)]

  bgp = openconfig_bgp_juniper()

  bgp.juniper_config.bgp.global_.as_ = global_config["my_as"]
  for peer_group in peer_group_list:
    bgp.juniper_config.bgp.peer_group.add(peer_group)

  for peer in peers:
    bgp.juniper_config.bgp.peer_group[peer[1]].neighbor.add(peer[0])
    bgp.juniper_config.bgp.peer_group[peer[1]].neighbor[peer[0]].peer_as = peer[2]

  assert bgp.get() == {'juniper-config': {'bgp': {'peer-group': {'groupA':
                      {'peer-type': False, 'neighbor': {'1.1.1.1': {'neighbor-name':
                      '1.1.1.1', 'peer-as': '3741'}, '1.1.1.2': {'neighbor-name': '1.1.1.2',
                       'peer-as': '5400'}, '1.1.1.3': {'neighbor-name': '1.1.1.3', 'peer-as': '29636'}},
                      'group-name': 'groupA'}, 'groupB': {'peer-type': False, 'neighbor':
                      {'2.2.2.2': {'neighbor-name': '2.2.2.2', 'peer-as': '12767'}}, 'group-name':
                      'groupB'}}, 'global': {'as': '2856'}}}}, \
    "bgp config build for juniper did not match expected values"

  #import pprint
  #pp = pprint.PrettyPrinter(indent=4)
  #pp.pprint(bgp.get())

  if not k:
    os.system("/bin/rm %s/bindings.py" % this_dir)
    os.system("/bin/rm %s/bindings.pyc" % this_dir)

if __name__ == '__main__':
  main()
