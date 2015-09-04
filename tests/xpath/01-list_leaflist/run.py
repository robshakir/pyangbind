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
    path = "/container/t3"
    retr = tree.get(path)
    passed = False
    assert len(retr) == 1, "Looking up a leaf-list element returned multiple elements erroneously (%s -> %d elements (%s))" \
      % (b[0], len(retr), retr)

    found = False
    try:
      v = retr[0].index(b[0])
      found = 1
    except ValueError:
      found = 0

    assert found == b[1], "When retrieving a leaf-list element, a known value was not in the list (%s -> %s (%s))" % (b[0], b[1], retr[0])

    rem = False
    try:
      yobj.container.t3.remove(b[0])
      rem = True
    except ValueError:
      pass
    assert rem == bool(b[1]), "Removal of a leaflist element did not return expected result (%s -> %s != %s)" % (b[0], rem, bool(b[1]))
    new_retr = tree.get(path)

    found = False
    try:
      v = new_retr[0].index(b[0])
      found = 1
    except ValueError:
      found = 0
    assert found == 0, "An element was not correctly removed from the leaf-list (%s -> %s [%s])" % (b[0], path, new_retr[0])

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

  for tc in [("vancouver", True), ("burnaby", True), ("san-francisco", False), ("surrey", True), ("richmond", True)]:
    path = "/container/t5"
    retr = tree.get(path)
    assert (tc[0] in retr[0]) == tc[1], "Retrieve of a leaf-list element did not return expected result (%s->%s %s)" % (tc[0], tc[1], (retr[0]))
    rem = False
    try:
      retr[0].remove(tc[0])
      rem = True
    except ValueError:
      pass
    new_retr = tree.get(path)
    assert rem == bool(tc[1]), "An element was not correctly removed from a leaf-list (%s -> len(%s) = %d)" % (tc[0], path, len(new_retr))


  for tc in [("gatineau", True), ("laval", True), ("new-york-city", False), ("quebec-city", True)]:
    path = "/container/t5"
    retr = tree.get(path)
    assert (tc[0] in retr[0]) == tc[1], "Retrieve of a leaf-list element did not return expected result (%s->%s %s)" % (tc[0], tc[1], (retr[0]))
    popped_obj = retr[0].pop()
    if popped_obj == tc[0]:
      expected_obj = True
    else:
      expected_obj = False
    assert expected_obj == bool(tc[1]), "Popped object was not the object that was expected (%s != %s)" % (tc[0],popped_obj)
    new_retr = tree.get(path)
    assert (tc[0] in new_retr[0]) == False, "Retrieve of a leaf-list element did not return expected result (%s->%s %s)" % (tc[0], tc[1], (new_retr[0]))

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

def t7_leaflist_of_leafrefs(yobj,tree=False):
  del_tree = False
  if not tree:
    del_tree = True
    tree = YANGPathHelper()

  test_list = [("snapshot", True), ("ranger", True), ("trout-slayer", False)]
  for b in test_list:
    if b[1]:
      yobj.container.t7.append(b[0])

  for b in test_list:
    passed = False
    try:
      yobj.reference.t7_ptr.append(b[0])
      passed = True
    except:
      pass

    assert passed == b[1], "A reference to a leaf-list of leafrefs was not correctly set (%s -> %s, expected %s)" % (b[0], passed, b[1])

if __name__ == '__main__':
  import_path = os.path.realpath(os.path.dirname(os.path.realpath(__file__)) + "/../../../")
  sys.path.insert(0, import_path)
  from lib.xpathhelper import YANGPathHelper, XPathError
  main()
