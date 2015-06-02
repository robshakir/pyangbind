#!/usr/bin/env python

import sys
import os
import getopt

TESTNAME="list-tc01"

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
  print "%s --plugindir %s -f pybind -o %s/bindings.py %s/%s.yang" % (pyangpath, pyangbindpath, this_dir, this_dir, TESTNAME)
  os.system("%s --plugindir %s -f pybind -o %s/bindings.py %s/%s.yang" % (pyangpath, pyangbindpath, this_dir, this_dir, TESTNAME))


  from bindings import list_tc01 as t
  from xpathhelper import YANGPathHelper
  y=YANGPathHelper()
  x=t(path_helper=y)

  x.container.t1.append('fish')
  x.reference.t1_ptr = 'fish'

  x.container.t2.add('trout')
  x.container.t2.add('wallaby')
  x.reference.t2_ptr = 'wallaby'


  if not k:
    os.system("/bin/rm %s/bindings.py" % this_dir)
    os.system("/bin/rm %s/bindings.pyc" % this_dir)

def t1_leaflist(tree=False):
  del_tree = False
  if not tree:
    del_tree = True
    tree = YANGPathHelper()

if __name__ == '__main__':
  import_path = os.path.realpath(os.path.dirname(os.path.realpath(__file__)) + "/../..")
  sys.path.insert(0, import_path)
  from xpathhelper import YANGPathHelper, XPathError
  main()
