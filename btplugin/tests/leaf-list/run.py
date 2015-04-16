#!/usr/bin/env python

import os, sys, getopt

TESTNAME="leaflist"

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
  os.system("/usr/local/bin/pyang --plugindir /Users/rjs/Code/pyangbind/btplugin -f bt -o %s/bindings.py %s/%s.yang" % (this_dir, this_dir, TESTNAME))

  from bindings import leaflist

  leaflist_instance = leaflist()

  assert hasattr(leaflist_instance, "container") == True, \
    "base container missing"

  assert hasattr(leaflist_instance.container, "leaflist") == True, \
    "leaf-list instance missing"

  assert len(leaflist_instance.container.leaflist) == 0, \
    "length of leaflist was not zero"

  leaflist_instance.container.leaflist.append("itemOne")

  assert len(leaflist_instance.container.leaflist) == 1, \
    "did not succesfully append string to list"

  assert leaflist_instance.container.leaflist[0] == "itemOne", \
    "cannot successfully address an item from the list"

  try:
    leaflist_instance.container.leaflist.append(int(1))
  except TypeError, m:
    pass

  assert len(leaflist_instance.container.leaflist) == 1, \
    "appended an element to the list erroneously"

  leaflist_instance.container.leaflist.append("itemTwo")
  assert leaflist_instance.container.leaflist[1] == "itemTwo", \
    "getitem did not return the correct value"

  leaflist_instance.container.leaflist[1] = "indexOne"
  assert leaflist_instance.container.leaflist[1] == "indexOne", \
    "setitem did not set the correct node"

  leaflist_instance.container.leaflist.insert(0,"indexZero")
  assert leaflist_instance.container.leaflist[0] == "indexZero", \
    "incorrectly set index 0 value"
  assert len(leaflist_instance.container.leaflist) == 4, \
    "list item was not added by insert()"

  del leaflist_instance.container.leaflist[0]
  assert len(leaflist_instance.container.leaflist) == 3, \
    "list item not succesfully removed by delitem"

  assert leaflist_instance.get() == \
    {'container': {'leaflist': ['itemOne', 'indexOne', 'itemTwo']}}, \
    "get did not correctly return the dictionary"


  if not k:
    os.system("/bin/rm %s/bindings.py" % this_dir)
    os.system("/bin/rm %s/bindings.pyc" % this_dir)

if __name__ == '__main__':
  main()
