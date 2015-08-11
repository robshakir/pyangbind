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
  print "%s --plugindir %s -f pybind -o %s/bindings.py --use-xpathhelper %s/%s.yang" % (pyangpath, pyangbindpath, this_dir, this_dir, TESTNAME)
  os.system("%s --plugindir %s -f pybind -o %s/bindings.py --use-xpathhelper %s/%s.yang" % (pyangpath, pyangbindpath, this_dir, this_dir, TESTNAME))


  from bindings import list_tc01 as ytest

  yhelper =  YANGPathHelper()
  yobj = ytest(path_helper=yhelper)

  t1_leaflist(yobj,tree=yhelper)
  t2_list(yobj,tree=yhelper)
  t3_leaflist_remove(yobj, tree=yhelper)
  t4_list_remove(yobj, tree=yhelper)
  t5_typedef_leaflist_add_del(yobj, tree=yhelper)
  t6_typedef_list_add(yobj, tree=yhelper)

  if not k:
    os.system("/bin/rm %s/bindings.py" % this_dir)
    os.system("/bin/rm %s/bindings.pyc" % this_dir)

def t1_leaflist(yobj,tree=False):
  del_tree = False
  if not tree:
    del_tree = True
    tree = YANGPathHelper()

  for a in ["mackerel", "trout", "haddock", "flounder"]:
    yobj.container.t1.append(a)

  for tc in [("mackerel", True), ("haddock", True), ("minnow", False)]:
    validref = False
    try:
      yobj.reference.t1_ptr = tc[0]
      validref = True
    except ValueError:
      pass
    assert validref == tc[1], "Reference was incorrectly set for a leaflist" + \
        " (%s not in %s -> %s != %s)" % (tc[0], str(yobj.container.t1), validref, tc[1])

  for tc in [("flounder", "exists"), ("minnow", "does not exist")]:
    validref = False
    try:
      yobj.reference.t1_ptr_noexist = tc[0]
      validref = True
    except ValueError:
      pass
    assert validref == True, "Reference was incorrectly set for a leaflist with" + \
      " require_instance set to false (%s threw error, but it %s)" % tc[1]

  if del_tree:
    del tree

def t2_list(yobj,tree=False):
  del_tree = False
  if not tree:
    del_tree = True
    tree = YANGPathHelper()

  for o in ["kangaroo", "wallaby", "koala", "dingo"]:
    yobj.container.t2.add(o)

  for tc in [("kangaroo", True), ("koala", True), ("wombat", False)]:
    validref = False
    try:
      yobj.reference.t2_ptr = tc[0]
      validref = True
    except ValueError:
      pass
    assert validref == tc[1], "Reference was incorrectly set for a list" + \
      " (%s not in %s -> %s != %s)" % (tc[0], yobj.container.t2.keys(), validref, tc[1])

  if del_tree:
    del tree

def t3_leaflist_remove(yobj, tree=False):
  del_tree = False
  if not tree:
    del_tree = True
    tree = YANGPathHelper()

  for b in ["oatmeal-stout", "amber-ale", "pale-ale", "pils", "ipa", "session-ipa"]:
    yobj.container.t3.append(b)

  for b in [("session-ipa", 1), ("amber-ale", 1), ("moose-drool", 0)]:
    path = "/container/t3/%s" % b[0]
    retr = tree.get(path)
    assert len(retr) == b[1], "Retrieve of a leaflist element returned the wrong number of elements (%s -> %d != %d)" % (b[0], len(retr), b[1])
    rem = False
    try:
      yobj.container.t3.remove(b[0])
      rem = True
    except ValueError:
      pass
    assert rem == bool(b[1]), "Removal of a leaflist element did not return expected result (%s -> %s != %s)" % (b[0], rem, bool(b[1]))
    new_retr = tree.get(path)
    assert len(new_retr) == 0, "An element was not correctly removed from the leaf-list (%s -> len(%s) = %d)" % (b[0], path, len(new_retr))

  for b in ["sunshine", "fat-tire", "ranger", "snapshot"]:
    yobj.container.t3.append(b)

  for b in [("snapshot", 1), ("ranger", 1), ("trout-slayer", 0)]:
    path = "/container/t3/%s" % b[0]
    retr = tree.get(path)
    assert len(retr) == b[1], "Retrieve of a leaflist element returned the wrong number of elements (%s -> %d != %d)" % (b[0], len(retr), b[1])

    popped_obj = yobj.container.t3.pop()
    if popped_obj == b[0]:
      expected_obj = True
    else:
      expected_obj = False
    assert expected_obj == bool(b[1]), "Popped object was not the object that was expected (%s != %s)" % (b[0],popped_obj)
    new_retr = tree.get(path)
    assert len(new_retr) == 0, "An element was not correctly removed from the leaf-list (%s -> len(%s) = %d)" % (b[0], path, len(new_retr))

  if del_tree:
    del tree

def t4_list_remove(yobj, tree=False):
  del_tree = False
  if not tree:
    del_tree = True
    tree = YANGPathHelper()

  for b in ["steam", "liberty", "california-lager", "porter", "ipa", "foghorn"]:
    yobj.container.t4.add(b)

  for b in [("steam", 1), ("liberty", 1), ("pygmy-owl", 0)]:
    path = "/container/t4[keyval=%s]" % b[0]
    retr = tree.get(path)
    assert len(retr) == b[1], "Retreive of a list element returned the wrong number of elements (%s -> %d != %d)" % (b[0], len(retr), b[1])
    rem = False
    try:
      yobj.container.t4.delete(b[0])
      rem = True
    except KeyError:
      pass
    assert rem == bool(b[1]), "Removal of a list element did not return expected result (%s -> %s != %s)" % (b[0], rem, bool(b[1]))
    new_retr = tree.get(path)
    assert len(new_retr) == 0, "An element was not correctly removed from the list (%s -> len(%s) = %d)" % (b[0], path, len(new_retr))

  if del_tree:
    del tree

def t5_typedef_leaflist_add_del(yobj,tree=False):
  del_tree = False
  if not tree:
    del_tree = True
    tree = YANGPathHelper()

  for a in ["quebec-city", "montreal", "laval", "gatineau"]:
    yobj.container.t5.append(a)

  for tc in [("quebec-city", True), ("montreal", True), ("dallas", False)]:
    validref = False
    try:
      yobj.reference.t5_ptr = tc[0]
      validref = True
    except ValueError:
      pass
    assert validref == tc[1], "Reference was incorrectly set for a leaflist" + \
        " (%s not in %s -> %s != %s)" % (tc[0], str(yobj.container.t5), validref, tc[1])

  for a in ["vancouver", "burnaby", "surrey", "richmond"]:
    yobj.container.t5.append(a)

  for tc in [("vancouver", 1), ("burnaby", 1), ("san-francisco", 0), ("surrey", 1), ("richmond", 1)]:
    path = "/container/t5/%s" % tc[0]
    retr = tree.get(path)
    assert len(retr) == tc[1], "Retreive of a leaflist element returned the wrong number of elements (%s -> %d != %d)" % (tc[0], len(retr), tc[1])
    rem = False
    try:
      yobj.container.t5.remove(tc[0])
      rem = True
    except ValueError:
      pass
    new_retr = tree.get(path)
    assert rem == bool(tc[1]), "An element was not correctly removed from a leaf-list (%s -> len(%s) = %d)" % (tc[0], path, len(new_retr))


  for tc in [("gatineau", 1), ("laval", 1), ("new-york-city", 0), ("quebec-city", 1)]:
    path = "/container/t5/%s" % (tc[0])
    retr = tree.get(path)
    assert len(retr) == tc[1], "Retrieve of a leaflist element returned the wrong number of elements (%s -> %d != %d)" % (tc[0], len(retr), tc[1])
    popped_obj = yobj.container.t5.pop()
    if popped_obj == tc[0]:
      expected_obj = True
    else:
      expected_obj = False
    assert expected_obj == bool(tc[1]), "Popped object was not the object that was expected (%s != %s)" % (tc[0],popped_obj)
    new_retr = tree.get(path)
    assert len(new_retr) == 0, "An element was not correctly removed from the leaf-list (%s -> len(%s) = %d)" % (tc[0], path, len(new_retr))

  if del_tree:
    del tree

def t6_typedef_list_add(yobj,tree=False):
  del_tree = False
  if not tree:
    del_tree = True
    tree = YANGPathHelper()

  for o in ["la-ciboire", "la-chipie", "la-joufflue", "la-matante"]:
    yobj.container.t6.add(o)

  for tc in [("la-ciboire", True), ("la-matante", True), ("heiniken", False)]:
    validref = False
    try:
      yobj.reference.t6_ptr = tc[0]
      validref = True
    except ValueError:
      pass
    assert validref == tc[1], "Reference was incorrectly set for a list" + \
      " (%s not in %s -> %s != %s)" % (tc[0], yobj.container.t6.keys(), validref, tc[1])

  if del_tree:
    del tree


if __name__ == '__main__':
  import_path = os.path.realpath(os.path.dirname(os.path.realpath(__file__)) + "/../../../")
  sys.path.insert(0, import_path)
  from lib.xpathhelper import YANGPathHelper, XPathError
  main()
