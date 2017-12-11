#!/usr/bin/env python
from __future__ import print_function

import os
import sys
import getopt
import json
import requests
import time
import unittest

from pyangbind.lib.xpathhelper import YANGPathHelper
from pyangbind.lib.serialise import pybindJSONDecoder

TESTNAME = "openconfig-interfaces"

# generate bindings in this folder
def setup_test():
  global this_dir
  global del_dirs

  try:
    opts, args = getopt.getopt(sys.argv[1:], "k", ["keepfiles"])
  except getopt.GetoptError as e:
    print(str(e))
    sys.exit(127)

  pythonpath = os.environ.get("PATH_TO_PYBIND_TEST_PYTHON") if \
                os.environ.get('PATH_TO_PYBIND_TEST_PYTHON') is not None \
                  else sys.executable
  pyangpath = os.environ.get('PYANGPATH') if \
                os.environ.get('PYANGPATH') is not None else False
  pyangbindpath = os.environ.get('PYANGBINDPATH') if \
                os.environ.get('PYANGBINDPATH') is not None else False
  assert pyangpath is not False, "could not find path to pyang"
  assert pyangbindpath is not False, "could not resolve pyangbind directory"

  OC = "https://raw.githubusercontent.com/openconfig/" + \
            "public/master/release/models/"
  RFC = "https://raw.githubusercontent.com/robshakir/" + \
            "yang/master/standard/ietf/RFC/"
  FETCH_FILES = [
                  (OC + "openconfig-extensions.yang", "include"),
                  (OC + "types/openconfig-types.yang", "include"),
                  (OC + "interfaces/openconfig-if-ip.yang", "openconfig"),
                  (OC + "interfaces/openconfig-if-ethernet.yang", "openconfig"),
                  (OC + "interfaces/openconfig-if-aggregate.yang", "openconfig"),
                  (OC + "interfaces/openconfig-interfaces.yang", "openconfig"),
                  (OC + "vlan/openconfig-vlan.yang", "include"),
                  (OC + "vlan/openconfig-vlan-types.yang", "include"),
                  (OC + "types/openconfig-inet-types.yang", "include"),
                  (OC + "types/openconfig-yang-types.yang", "include"),
                  (RFC + "ietf-inet-types.yang", "include"),
                  (RFC + "ietf-yang-types.yang", "include"),
                  (RFC + "ietf-interfaces.yang", "include")
                ]

  this_dir = os.path.dirname(os.path.realpath(__file__))
  del_dirs = []
  for fn in FETCH_FILES:
    wrdir = os.path.join(this_dir, fn[1])
    if not os.path.exists(wrdir):
      os.mkdir(wrdir)
    if wrdir not in del_dirs:
      del_dirs.append(wrdir)
    wrpath = os.path.join(this_dir, fn[1], fn[0].split("/")[-1])
    if not os.path.exists(wrpath):
      got = False
      count = 0
      for i in range(0,4):
        response = requests.get(fn[0])
        if response.status_code != 200:
          time.sleep(2)
        else:
          got = True
          f = open(wrpath, 'w')
          f.write(response.text)
          f.close()
          break
      assert got is True, "Could not get file %s from GitHub (response: %s)" \
                % (response.status_code, fn[0])

  files_str = " ".join([os.path.join(this_dir, "openconfig", i) for i in
                        os.listdir(os.path.join(this_dir, "openconfig"))])

  cmd = "%s " % pythonpath
  cmd += "%s --plugindir %s/pyangbind/plugin" % (pyangpath, pyangbindpath)
  cmd += " -f pybind --split-class-dir %s/ocbind" % this_dir
  cmd += " -p %s" % this_dir
  cmd += " -p %s" % os.path.join(this_dir, "include")
  cmd += " --use-xpathhelper"
  cmd += " --lax-quote-checks"
  for i in ["openconfig-interfaces", "openconfig-if-aggregate", "openconfig-if-ip"]:
    cmd += " %s" % os.path.join(this_dir, "openconfig", "%s.yang" % i)
  os.system(cmd)

def teardown_test():
  global this_dir
  global del_dirs
  del_dirs.append(os.path.join(this_dir, "ocbind"))
  for dirname in del_dirs:
    for root, dirs, files in os.walk(os.path.join(dirname), topdown=False):
      for name in files:
        os.remove(os.path.join(root, name))
      for name in dirs:
        os.rmdir(os.path.join(root, name))
    os.rmdir(dirname)

class PyangbindOCIntf(unittest.TestCase):
  def __init__(self, *args, **kwargs):
    unittest.TestCase.__init__(self, *args, **kwargs)

    import ocbind
    self.ph = YANGPathHelper()
    self.instance = ocbind.openconfig_interfaces(path_helper=self.ph)

  def test_001_populated_intf_type(self):
    i0 = self.instance.interfaces.interface.add("eth0")
    self.assertNotEqual(len(i0.config.type._restriction_dict), 0)

if __name__ == '__main__':
  keepfiles = False
  args = sys.argv
  if '-k' in args:
    keepfiles = True
    args.remove('-k')
  setup_test()
  T = unittest.main(exit=False, argv=args)
  if len(T.result.errors) or len(T.result.failures):
    exitcode = 127
  else:
    exitcode = 0
  if keepfiles is False:
    teardown_test()
  sys.exit(exitcode)
