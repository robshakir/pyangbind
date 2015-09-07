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

  pyangpath = os.environ.get('PYANGPATH') if os.environ.get('PYANGPATH') is not None else False
  pyangbindpath = os.environ.get('PYANGBINDPATH') if os.environ.get('PYANGBINDPATH') is not None else False
  assert not pyangpath == False, "could not find path to pyang"
  assert not pyangbindpath == False, "could not resolve pyangbind directory"

  this_dir = os.path.dirname(os.path.realpath(__file__))
  os.system("%s --plugindir %s -f pybind -o %s/bindings.py %s/%s.yang" % (pyangpath, pyangbindpath, this_dir, this_dir, TESTNAME))


  from bindings import openconfig_bgp_juniper

  global_config = {"my_as": 2856,}
  peer_group_list = ["groupA", "groupB"]
  peers = [("1.1.1.1", "groupA", 3741), ("1.1.1.2", "groupA", 5400,),
          ("1.1.1.3", "groupA", 29636), ("2.2.2.2", "groupB", 12767)]

  bgp = openconfig_bgp_juniper()

  except_thrown = False
  try:
    bgp.system = False
  except AttributeError:
    except_thrown = True

  assert except_thrown == True, "Trying to set a missing container did not result" + \
    " in an attribute error (%s != True)" % except_thrown

  bgp.juniper_config.bgp.global_.as_ = global_config["my_as"]
  for peer_group in peer_group_list:
    bgp.juniper_config.bgp.peer_group.add(peer_group)

  for peer in peers:
    bgp.juniper_config.bgp.peer_group[peer[1]].neighbor.add(peer[0])
    bgp.juniper_config.bgp.peer_group[peer[1]].neighbor[peer[0]].peer_as = peer[2]


  bgp_filter_response = {'juniper-config': {'bgp': {'global': {'as': '2856'},
                            'peer-group': {'groupA': {'group-name': 'groupA',
                                                      'neighbor': {'1.1.1.1': {'neighbor-name': '1.1.1.1',
                                                                               'peer-as': '3741'},
                                                                   '1.1.1.2': {'neighbor-name': '1.1.1.2',
                                                                               'peer-as': '5400'},
                                                                   '1.1.1.3': {'neighbor-name': '1.1.1.3',
                                                                               'peer-as': '29636'}}},
                                           'groupB': {'group-name': 'groupB',
                                                      'neighbor': {'2.2.2.2': {'neighbor-name': '2.2.2.2',
                                                                               'peer-as': '12767'}}}}}}}
  bgp_unfilter_response = {'juniper-config': {'bgp': {'global': {'as': '2856'},
                            'peer-group': {'groupA': {'group-name': 'groupA',
                                                      'neighbor': {'1.1.1.1': {'neighbor-name': '1.1.1.1',
                                                                               'peer-as': '3741'},
                                                                   '1.1.1.2': {'neighbor-name': '1.1.1.2',
                                                                               'peer-as': '5400'},
                                                                   '1.1.1.3': {'neighbor-name': '1.1.1.3',
                                                                               'peer-as': '29636'}},
                                                      'peer-type': ''},
                                           'groupB': {'group-name': 'groupB',
                                                      'neighbor': {'2.2.2.2': {'neighbor-name': '2.2.2.2',
                                                                               'peer-as': '12767'}},
                                                      'peer-type': ''}}}}}
  assert bgp.get() == bgp_unfilter_response, "unfiltered get response did not match"
  assert bgp.get(filter=True) == bgp_filter_response, "filtered get response did not match"

  if not k:
    os.system("/bin/rm %s/bindings.py" % this_dir)
    os.system("/bin/rm %s/bindings.pyc" % this_dir)

if __name__ == '__main__':
  main()
