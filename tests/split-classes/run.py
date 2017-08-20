#!/usr/bin/env python

import os
import sys
import getopt

TESTNAME = "split-classes"


# generate bindings in this folder
def main():
  try:
    opts, args = getopt.getopt(sys.argv[1:], "k", ["keepfiles"])
  except getopt.GetoptError as e:
    print(str(e))
    sys.exit(127)

  keepfiles = False
  for o, a in opts:
    if o in ["-k", "--keepfiles"]:
      keepfiles = True

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
  cmd += " -f pybind "
  cmd += " --split-class-dir=%s/bindings" % this_dir
  cmd += " -p %s" % this_dir
  cmd += " %s/%s.yang" % (this_dir, TESTNAME)
  os.system(cmd)

  from bindings import split_classes

  s = split_classes()

  passed = None
  try:
    s.split_classes.test = "CheckModNameSameAsFirstContainerName"
    passed = True
  except ValueError:
    passed = False

  assert passed is True, "Module name matching first level container name " + \
      "resulted in invalid file"

  passed = None
  try:
    s.remote.remote.remote.remote = "hi"
    passed = True
  except ValueError:
    passed = False

  assert passed is True, "Hiearchy of same named containers " + \
      "resulted in an invalid file"

  s.choices.case_one_container.user.add('first')
  assert list(s.choices.case_one_container.user.keys()) == ['first'], \
    "Could not add an entry to the case one container correctly " + \
      "%s != ['first']" % s.choices.case_one_container.user.keys()

  s.choices.case_two_container.user.add('second')
  assert list(s.choices.case_one_container.user.keys()) == [], \
    "Setting case two leaf did not clear case-one branch " + \
      "%s != ['']" % s.choices.case_one_container.user.keys()
  assert list(s.choices.case_two_container.user.keys()) == ['second'], \
    "Did not correctly add to the case two container " + \
      "%s != ['second']" % s.choices.case_two_container.user.keys()

  if not keepfiles:
    os.system("/bin/rm -rf %s/bindings" % this_dir)

if __name__ == '__main__':
  main()
