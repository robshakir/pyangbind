#!/usr/bin/env python

import os, sys, getopt

TESTNAME="config-false"

# generate bindings in this folder

def main():
  try:
    opts, args = getopt.getopt(sys.argv[1:], "k", ["keepfiles"])
  except getopt.GetoptError as e:
    print str(e)
    sys.exit(127)

  keepfiles = False
  for o, a in opts:
    if o in ["-k", "--keepfiles"]:
      keepfiles = True

  pyangpath = os.environ.get('PYANGPATH') if os.environ.get('PYANGPATH') is not None else False
  pyangbindpath = os.environ.get('PYANGBINDPATH') if os.environ.get('PYANGBINDPATH') is not None else False
  assert not pyangpath == False, "could not find path to pyang"
  assert not pyangbindpath == False, "could not resolve pyangbind directory"

  this_dir = os.path.dirname(os.path.realpath(__file__))
  os.system("%s --plugindir %s -f pybind -o %s/bindings.py %s/%s.yang" % (pyangpath, pyangbindpath, this_dir, this_dir, TESTNAME))

  from bindings import config_false

  test_instance = config_false()

  structure_dict = {
                      "container": {
                                      "subone": {
                                                  "a_leaf": True,
                                                  "d_leaf": False,
                                                },
                                      "subtwo": {
                                                  "b_leaf": False,
                                                  "subsubtwo": {
                                                                  "c_leaf": False,
                                                                }
                                                }
                                    }
                    }

  for i in structure_dict.keys():
    assert hasattr(test_instance, i), "top level %s does not exist" % i
    if hasattr(test_instance, i):
      c = getattr(test_instance, i)
      if isinstance(structure_dict[i], dict):
        for j in structure_dict[i].keys():
          assert hasattr(c, j), "second level %s does not exist" % j
          d = getattr(c, j)
          if isinstance(structure_dict[i][j], dict):
            for k in structure_dict[i][j].keys():
              assert hasattr(d, k), "third-level %s does not exist" % k
              e = getattr(d, k)
              if isinstance(structure_dict[i][j][k], dict):
                for l in structure_dict[i][j][k].keys():
                  assert hasattr(e, l), "fourth level %s does not exist" % l

  # tests
  passed = True
  try:
    test_instance.container.subone.a_leaf = 1
  except AttributeError:
    passed = False

  assert passed == structure_dict["container"]["subone"]["a_leaf"], "setting a_leaf did not result in expected outcome (%s != %s)" \
        % (structure_dict["container"]["subone"]["a_leaf"], passed)

  passed = True
  try:
    test_instance.container.subone.d_leaf = 1
  except AttributeError:
    passed = False

  assert passed == structure_dict["container"]["subone"]["d_leaf"], "setting d_leaf did not result in expected outcome (%s != %s)" \
        % (structure_dict["container"]["subone"]["d_leaf"], passed)

  passed = True
  try:
    test_instance.container.subtwo.b_leaf = 1
  except AttributeError:
    passed = False

  assert passed == structure_dict["container"]["subtwo"]["b_leaf"], "setting b_leaf did not result in expected outcome (%s != %s)" \
        % (structure_dict["container"]["subtwo"]["b_leaf"], passed)

  passed = True
  try:
    test_instance.container.subtwo.subsubtwo.c_leaf = 1
  except AttributeError:
    passed = False

  assert passed == structure_dict["container"]["subtwo"]["subsubtwo"]["c_leaf"], "setting c_leaf did not result in expected outcome (%s != %s)" \
        % (structure_dict["container"]["subtwo"]["subsubtwo"]["c_leaf"], passed)

  if not keepfiles:
    os.system("/bin/rm %s/bindings.py" % this_dir)
    os.system("/bin/rm %s/bindings.pyc" % this_dir)

if __name__ == '__main__':
  main()
