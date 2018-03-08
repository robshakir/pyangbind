#!/usr/bin/env python

import os
import sys
import getopt
import unittest
from pyangbind.lib.yangtypes import safe_name
from pyangbind.lib.xpathhelper import YANGPathHelper
from pyangbind.lib.serialise import pybindJSONDecoder
import pyangbind.lib.pybindJSON as pbJ
import json


this_dir = os.path.dirname(os.path.realpath(__file__))


# generate bindings in this folder
def setup_test():
  try:
    opts, args = getopt.getopt(sys.argv[1:], "k", ["keepfiles"])
  except getopt.GetoptError:
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

  cmd = "%s " % pythonpath
  cmd += "%s --plugindir %s/pyangbind/plugin" % (pyangpath, pyangbindpath)
  cmd += " -f pybind -o %s/bindings.py" % this_dir
  cmd += " -p %s" % this_dir
  cmd += " --use-extmethods"
  cmd += " --use-xpathhelper"
  cmd += " %s/root-tc04-a.yang %s/root-tc04-b.yang" % (this_dir, this_dir)
  os.system(cmd)


def teardown_test():
  os.system("/bin/rm %s/bindings.py" % this_dir)
  os.system("/bin/rm %s/bindings.pyc" % this_dir)


class PyangbindXpathRootTC04(unittest.TestCase):

  def __init__(self, *args, **kwargs):
    unittest.TestCase.__init__(self, *args, **kwargs)

    err = None
    try:
      import bindings
    except ImportError as e:
      err = e
    self.assertIs(err, None)
    self.path_helper = YANGPathHelper()
    self.instance_a = bindings.root_tc04_a(path_helper=self.path_helper)
    self.instance_b = bindings.root_tc04_b(path_helper=self.path_helper)

  def test_001_check_containers(self):
    self.assertIsNot(getattr(self.instance_a, safe_name("root-tc04-a"), None), None)
    self.assertIsNot(getattr(self.instance_b, safe_name("root-tc04-b"), None), None)

  def test_002_base_gets(self):
    # each of these raise exceptions so will cause test case failures
    self.path_helper.get_unique("/")
    self.path_helper.get_unique("/root-tc04-a")
    self.path_helper.get_unique("/root-tc04-b")

  def test_003_base_sets(self):
    a = self.path_helper.get_unique("/root-tc04-a")
    a.a = "little-cottonwood"
    self.assertEqual(self.instance_a.root_tc04_a.a, "little-cottonwood")
    b = self.path_helper.get_unique("/root-tc04-b")
    b.b = "big-cottonwood"
    self.assertEqual(self.instance_b.root_tc04_b.b, "big-cottonwood")

  def test_004_serialise(self):
    self.instance_a.root_tc04_a.a = "emigration"
    self.instance_b.root_tc04_b.b = "alpine-fork"
    expected_json = json.load(open(os.path.join(this_dir, "json", "04-serialise.json")))
    v = json.loads(pbJ.dumps(self.path_helper.get_unique("/")))
    self.assertEqual(v, expected_json)

    expected_ietf_json = json.load(open(os.path.join(this_dir, "json", "04b-ietf-serialise.json")))
    v = json.loads(pbJ.dumps(self.path_helper.get_unique("/"), mode="ietf"))
    self.assertEqual(v, expected_ietf_json)

  def test_005_deserialise(self):
    root = self.path_helper.get_unique("/")
    fh = open(os.path.join(this_dir, "json", "05-deserialise.json"), 'r')
    pybindJSONDecoder.load_json(json.load(fh), None, None, obj=root)
    v = json.loads(pbJ.dumps(self.path_helper.get_unique("/")))
    x = json.load(open(os.path.join(this_dir, "json", "05-deserialise.json"), 'r'))
    self.assertEqual(v, x)

  def test_006_ietf_deserialise(self):
    root = self.path_helper.get_unique("/")
    fh = open(os.path.join(this_dir, "json", "06-deserialise-ietf.json"), 'r')
    pybindJSONDecoder.load_ietf_json(json.load(fh), None, None, obj=root)
    v = json.loads(pbJ.dumps(self.path_helper.get_unique("/"), mode="ietf"))
    x = json.load(open(os.path.join(this_dir, "json", "06-deserialise-ietf.json"), 'r'))
    self.assertEqual(v, x)


if __name__ == '__main__':
  keepfiles = False
  args = sys.argv
  if '-k' in args:
    args.remove('-k')
    keepfiles = True
  setup_test()
  T = unittest.main(exit=False)
  if len(T.result.errors) or len(T.result.failures):
    exitcode = 127
  else:
    exitcode = 0
  if keepfiles is False:
    teardown_test()
  sys.exit(exitcode)
