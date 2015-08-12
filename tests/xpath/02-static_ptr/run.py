#!/usr/bin/env python

import sys
import os
import getopt

TESTNAME="ptr-tc02"

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
  os.system("%s --plugindir %s -f pybind -o %s/bindings.py --use-xpathhelper %s/%s.yang" % (pyangpath, pyangbindpath, this_dir, this_dir, TESTNAME))


  from bindings import ptr_tc02 as ytest

  yhelper =  YANGPathHelper()
  yobj = ytest(path_helper=yhelper)

  t1_listkey(yobj, tree=yhelper)

  if not k:
    os.system("/bin/rm %s/bindings.py" % this_dir)
    os.system("/bin/rm %s/bindings.pyc" % this_dir)

def t1_listkey(yobj,tree=False):
  del_tree = False
  if not tree:
    del_tree = True
    tree = YANGPathHelper()


  for x in range(0,100):
    yobj.container.t1a.add("x%s" % x)

  for x in range(0,100):
    assert yobj.container.t1a["x%s" % x].t1c.t1d == "x%s" % x, \
      "list key was not set correctly when acting as a pointer (%s != 'test')" % \
        (yobj.container.t1a["x%s" % x].t1c.t1d)
    assert str(yobj.container.t1a["x%s" % x].t1b) == "x%s" % x, \
      "list key pointer was not read correctly (value is %s)" % \
        yobj.container.t1a["x%s" % x].t1b

  if del_tree:
    del tree


if __name__ == '__main__':
  import_path = os.path.realpath(os.path.dirname(os.path.realpath(__file__)) + "/../../..")
  sys.path.insert(0, import_path)
  from lib.xpathhelper import YANGPathHelper, XPathError
  main()
