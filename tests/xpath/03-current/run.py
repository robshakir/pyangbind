#!/usr/bin/env python

import sys
import os
import getopt

TESTNAME="current-tc03"

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

  from bindings import current_tc03
  yhelper = YANGPathHelper()
  yobj = current_tc03(path_helper=yhelper)

  t1_currentref(yobj, tree=yhelper)

  if not k:
    os.system("/bin/rm %s/bindings.py" % this_dir)
    os.system("/bin/rm %s/bindings.pyc" % this_dir)

def t1_currentref(yobj, tree=False):
  del_tree = False
  if not tree:
    del_tree = True
    tree = YANGPathHelper()

  for i in [(1,2,), (3,4), (5,6)]:
    yobj.src_list.add("%s %s" % i)

  yobj.referencing_list.add(1)
  e = False
  try:
    yobj.referencing_list[1].source_val = "1"
    yobj.referencing_list[1].reference = "2"
  except ValueError:
    e = True

  assert e == False, "incorrectly rejected valid reference"

  assert yobj.src_list["1 2"].referenced == "1", "referenced value was incorrectly set"
  assert yobj.src_list["1 2"].value == "2", "referenced value was incorrectly set"

  if del_tree:
    del yhelper


if __name__ == '__main__':
  import_path = os.path.realpath(os.path.dirname(os.path.realpath(__file__)) + "/../../..")
  sys.path.insert(0, import_path)
  from lib.xpathhelper import YANGPathHelper, XPathError
  main()