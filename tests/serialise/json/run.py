#!/usr/bin/env python

import os, sys, getopt, json
from lib.serialise import pybindJSONEncoder

TESTNAME="serialise-json"

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

  from bindings import serialise_json
  js = serialise_json()

  js.c1.l1.add(1)
  for s in ["int", "uint"]:
    for l in [8, 16, 32, 64]:
      name = "%s%s" % (s,l)
      x=getattr(js.c1.l1[1], "_set_%s" % name)
      x(1)
  js.c1.l1[1].restricted_integer = 6;
  js.c1.l1[1].string = "bear"
  js.c1.l1[1].restricted_string = "aardvark"
  js.c1.l1[1].union = 16
  js.c1.l1[1].union_list.append(16)
  js.c1.l1[1].union_list.append("chicken")

  js.c1.t1.add(16)
  js.c1.l1[1].leafref = 16

  from bitarray import bitarray
  js.c1.l1[1].binary = bitarray("010101")
  js.c1.l1[1].boolean = True
  js.c1.l1[1].enumeration = "one"
  js.c1.l1[1].identityref = "idone"
  js.c1.l1[1].typedef_one = "test"
  js.c1.l1[1].typedef_two = 8
  js.c1.l1[1].one_leaf = "hi"


  print js.get()

  for i in range(1,10):
    js.c1.l2.add(i)

  print json.dumps(js.get(), cls=pybindJSONEncoder, indent=4)


  # from ocbindings import bgp
  # from lib.xpathhelper import YANGPathHelper

  # ph = YANGPathHelper()

  # ocbgp = bgp(path_helper=ph)

  # add_peers = [
  #               ("192.168.1.1", "2856", "linx-peers"),
  #               ("172.16.12.2", "3356", "transit"),
  #               ("10.0.0.3", "5400", "private-peers"),
  #               ("10.0.0.4", "3300", "private-peers"),
  #               ("192.168.1.2", "6871", "linx-peers")
  #             ]

  # for e in add_peers:
  #   if not e[2] in ocbgp.bgp.peer_groups.peer_group:
  #     ocbgp.bgp.peer_groups.peer_group.add(e[2])
  #   if not e[0] in ocbgp.bgp.neighbors.neighbor:
  #     ocbgp.bgp.neighbors.neighbor.add(e[0])
  #     ocbgp.bgp.neighbors.neighbor[e[0]].config.peer_group = e[2]
  #     ocbgp.bgp.neighbors.neighbor[e[0]].config.peer_type = "EXTERNAL"
  #     ocbgp.bgp.neighbors.neighbor[e[0]].config.send_community = "STANDARD"
  #     ocbgp.bgp.neighbors.neighbor[e[0]].route_reflector.config.route_reflector_client = True
  #     ocbgp.bgp.neighbors.neighbor[e[0]].route_reflector.config.route_reflector_cluster_id = "192.168.1.1"


  # #ocbgp.bgp.neighbors.neighbor.add("42.42.42.42")
  # #ocbgp.bgp.neighbors.neighbor["42.42.42.42"].config.peer_group = "DOES NOT EXIST!"

  # print ocbgp.bgp.peer_groups.get(filter=True)

  # print json.dumps(ocbgp.get(), cls=pybindJSONEncoder, indent=4)

  if not k:
    os.system("/bin/rm %s/bindings.py" % this_dir)
    os.system("/bin/rm %s/bindings.pyc" % this_dir)

if __name__ == '__main__':
  main()