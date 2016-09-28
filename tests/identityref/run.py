#!/usr/bin/env python

import os
import sys
import getopt

TESTNAME = "identityref"


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
  cmd += " -f pybind -o %s/bindings.py" % this_dir
  cmd += " -p %s" % this_dir
  cmd += " %s/%s.yang" % (this_dir, TESTNAME)
  cmd += " %s/remote-two.yang" % (this_dir)
  os.system(cmd)

  from bindings import identityref

  i = identityref()

  for j in ["id1", "idr1"]:
    assert hasattr(i.test_container, j), \
        "%s leaf does not exist in the container" % i

  assert i.test_container.id1 == "", \
      "id1 leaf had an unexpected value (%s)" % i.test_container.id1
  assert i.test_container.idr1 == "", \
      "idr1 leaf had an unexpected value (%s)" % i.test_container.idr1

  passed = True
  try:
    i.test_container.id1 = "hello"
  except ValueError:
    passed = False
  assert passed is False, "id1 leaf set to invalid value"

  for k in ["option-one", "option-two"]:
    passed = True
    i.test_container.id1 = k
    try:
      i.test_container.id1 = k
    except ValueError:
      passed = False
    assert passed is True, \
        "id1 leaf was set to an invalid value (%s, %s)" % (passed, k)

  # checks that the namespaces are right
  for k in ["remote-one", "remote-two"]:
    passed = True
    try:
      i.test_container.idr1 = k
    except ValueError:
      passed = False
    assert passed is True, "idr1 leaf was set to an invalid value (%s)" % k

  for k in [("father", True), ("son", True), ("foo:father", True),
              ("foo:son", True), ("elephant", False), ("hamster", False)]:
    passed = True
    try:
      i.test_container.id2 = k[0]
    except ValueError:
      passed = False
    assert passed is k[1], \
        "id2 leaf was set incorrectly (%s: %s != %s)" % \
            (k[0], k[1], passed)

  for k in [("grandmother", True), ("mother", True), ("niece", False),
              ("aunt", True), ("cousin", True), ("daughter", True),
                ("son", False), ("father", False), ("grandfather", False)]:
    passed = True
    try:
      i.test_container.id3 = k[0]
    except ValueError:
      passed = False

    assert passed is k[1], \
      "id3 leaf was set incorrectly (%s: %s != %s)" % \
          (k[0], k[1], passed)

  for k in [("daughter", True), ("cousin", False), ("aunt", False)]:
    passed = True
    try:
      i.test_container.id4 = k[0]
    except ValueError:
      passed = False

    assert passed is k[1], \
      "id4 leaf was set incorrectly (%s: %s != %s)" % \
        (k[0], k[1], passed)

  for k in [("daughter", True), ("cousin", True), ("mother", True),
            ("aunt", True), ("greatgrandmother", False)]:
    passed = True
    try:
      i.test_container.id5 = k[0]
    except ValueError:
      passed = False

    assert passed is k[1], \
      "id5 leaf was set incorrectly (%s: %S != %s)" % \
        (k[0], k[1], passed)

  for atype in [("source-dest", True), ("lcaf", True), ("unknown", False)]:
    passed = True
    try:
      i.ak.address_type = atype[0]
    except ValueError:
      passed = False
    assert passed is atype[1], "AK identity inheritance test failed - " + \
      "%s: %s != %s" % (atype[0], atype[1], passed)

  for k in [("remote:remote-one", True), ("nottherightmodulename:remote-one", False),
            ("remote:remote-two", True)]:
    passed = True
    try:
      i.test_container.idr1 = k[0]
    except ValueError:
      passed = False

    assert passed == k[1], "Did not set an identityref " + \
      "based on the module-name:value format correctly:" + \
      "  %s != %s for %s" % (k[1], passed, k[0])

  for tc in [("remote-id", True), ("remote-two:remote-id", True),
             ("invalid", False)]:
    passed = True
    try:
      i.ietfint.ref = tc[0]
    except ValueError:
      passed = False

    assert passed == tc[1], "setting ietfint.ref to %s incorrect " + \
      "%s != %s" % (tc[0], tc[1], passed)

  if not keepfiles:
    os.system("/bin/rm %s/bindings.py" % this_dir)
    os.system("/bin/rm %s/bindings.pyc" % this_dir)


if __name__ == '__main__':
  main()
