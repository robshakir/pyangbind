#!/usr/bin/env python

import os
import sys
import getopt
import unittest
import importlib
from pyangbind.lib.yangtypes import safe_name
from pyangbind.lib.xpathhelper import YANGPathHelper
import pyangbind.lib.pybindJSON as pbJ
import json

TESTNAME = "misc"

k = False

# generate bindings in this folder
def setup_test():
  try:
    opts, args = getopt.getopt(sys.argv[1:], "k", ["keepfiles"])
  except getopt.GetoptError as e:
    sys.exit(127)

  global k
  global this_dir

  for o, a in opts:
    if o in ["-k", "--keepfiles"]:
      k = True

  pythonpath = os.environ.get("PATH_TO_PYBIND_TEST_PYTHON") if \
                os.environ.get('PATH_TO_PYBIND_TEST_PYTHON') is not None \
                  else sys.executable
  pyangpath = os.environ.get('PYANGPATH') if \
                os.environ.get('PYANGPATH') is not None else False
  pyangbindpath = os.environ.get('PYANGBINDPATH') if \
                os.environ.get('PYANGBINDPATH') is not None else False
  assert pyangpath is not False, "could not find path to pyang"
  assert pyangbindpath is not False, "could not resolve pyangbind directory"

  this_dir = os.path.dirname(os.path.realpath(__file__))

  cmd = "%s " % pythonpath
  cmd += "%s --plugindir %s/pyangbind/plugin" % (pyangpath, pyangbindpath)
  cmd += " -f pybind"
  cmd += " -p %s" % this_dir
  cmd += " --use-extmethods"
  cmd += " --split-class-dir %s/bindings" % this_dir
  cmd += " --use-xpathhelper"
  cmd += " %s/%s.yang" % (this_dir, TESTNAME)
  os.system(cmd)

def teardown_test():
  global k
  global this_dir

  if not k:
    os.system("/bin/rm -rf %s/bindings" % this_dir)

class PyangbindMiscTests(unittest.TestCase):

  def __init__(self, *args, **kwargs):
    unittest.TestCase.__init__(self, *args, **kwargs)

    self.ph = YANGPathHelper()

    err = None
    try:
      globals()["bindings"] = importlib.import_module("bindings")
    except ImportError as e:
      err = e
    self.assertIs(err, None)
    self.instance = bindings.misc(path_helper=self.ph)

  # Check that we can ingest an OpenConfig style list entry
  # with a leafref to the key
  def test_001_setleafref(self):
    globals()["misc"] = importlib.import_module("bindings.a")
    a = misc.a()
    a.foo = "stringval"

    self.instance.a.append(a)
    self.assertEqual(unicode(self.instance.a["stringval"].foo), u"stringval")
    self.assertEqual(self.instance.a["stringval"].config.foo, u"stringval")

  def test_002_checklistkeytype(self):
    globals()["miscb"] = importlib.import_module("bindings.b")
    b = miscb.b()
    b.foo = "stringvalone"
    b.bar = "stringvaltwo"

    self.instance.b.append(b)
    self.assertEqual(type(self.instance.b.keys()[0]), unicode)

  def test_003_checklistkeytype(self):
    globals()["miscc"] = importlib.import_module("bindings.c")
    c = miscc.c()
    c.one = 42

    self.instance.c.append(c)
    self.assertEqual(type(self.instance.c.keys()[0]), int)

if __name__ == '__main__':
  setup_test()
  T = unittest.main(exit=False)
  if len(T.result.errors) or len(T.result.failures):
    exitcode = 127
  else:
    exitcode = 0
  teardown_test()
  sys.exit(exitcode)
