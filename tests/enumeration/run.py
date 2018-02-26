#!/usr/bin/env python

import os
import sys
import getopt

TESTNAME = "enumeration"


# generate bindings in this folder
def main():
  try:
    opts, args = getopt.getopt(sys.argv[1:], "k", ["keepfiles"])
  except getopt.GetoptError as e:
    print(str(e))
    sys.exit(127)

  k = False
  for o, a in opts:
    if o in ["-k", "--keepfiles"]:
      k = True

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
  os.system(cmd)

  from bindings import enumeration
  t = enumeration()

  for e in ["e", "f"]:
    assert hasattr(t.container, e), \
        "container does not contain enumeration %s" % e

  t.container.e = "one"
  assert t.container.e == "one", \
      "enumeration value was not correctly set (%s)" % \
          t.container.e

  catch = False
  try:
    t.container.e = "twentyseven"
  except Exception:
    catch = True
  assert catch is True, \
      "erroneous value was not caught by restriction handler (%s)" % \
        t.container.e

  assert t.container.f._default == "c", \
      "erroneous default value for 'f' (%s)" % \
          t.container.f._default

  t.container.e = "two"
  assert t.container.e.getValue(mapped=True) == 42, \
      "erroneously statically defined value returned (%s)" % \
          t.container.e.getValue(mapped=True)

  if not k:
    os.system("/bin/rm %s/bindings.py" % this_dir)
    os.system("/bin/rm %s/bindings.pyc" % this_dir)


if __name__ == '__main__':
  main()
