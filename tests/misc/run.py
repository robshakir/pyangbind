#!/usr/bin/env python

import os
import sys
import getopt
import unittest
from pyangbind.lib.xpathhelper import YANGPathHelper

TESTNAME = "misc"


# generate bindings in this folder
def setup_test():
  try:
    opts, args = getopt.getopt(sys.argv[1:], "k", ["keepfiles"])
  except getopt.GetoptError as e:
    sys.exit(127)

  global this_dir

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
  global this_dir

  os.system("/bin/rm -rf %s/bindings" % this_dir)


class PyangbindMiscTests(unittest.TestCase):

  def __init__(self, *args, **kwargs):
    unittest.TestCase.__init__(self, *args, **kwargs)

    self.ph = YANGPathHelper()

    err = None
    try:
      import bindings
    except ImportError as e:
      err = e
    self.assertIs(err, None)
    self.instance = bindings.misc(path_helper=self.ph)

  # Check that we can ingest an OpenConfig style list entry
  # with a leafref to the key
  def test_001_setleafref(self):
    import bindings.a as misca
    a = misca.a()
    a.foo = "stringval"

    self.instance.a.append(a)
    self.assertEqual(unicode(self.instance.a["stringval"].foo), u"stringval")
    self.assertEqual(self.instance.a["stringval"].config.foo, u"stringval")

  def test_002_checklistkeytype(self):
    import bindings.b as miscb
    b = miscb.b()
    b.foo = "stringvalone"
    b.bar = "stringvaltwo"

    self.instance.b.append(b)
    self.assertEqual(type(self.instance.b.keys()[0]), unicode)

  def test_003_checklistkeytype(self):
    import bindings.c as miscc
    c = miscc.c()
    c.one = 42

    self.instance.c.append(c)
    self.assertEqual(type(self.instance.c.keys()[0]), int)


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
