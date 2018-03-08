#!/usr/bin/env python


import os
import sys
import getopt

TESTNAME = "boolean-empty"


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

  from bindings import boolean_empty as b

  t = b()

  for i in ["b1", "b2", "e1"]:
    assert hasattr(t.container, i), "element did not exist in container (%s)" \
        % i

  for value in [(0, False), ("0", False), (False, False), ("false", False),
                ("False", False), (1, True), ("1", True), (True, True),
                ("true", True), ("True", True)]:
    passed = True
    try:
      t.container.b1 = value[0]
    except Exception:
      passed = False

    assert passed is True, "value of b1 was not correctly set to %s" % value
    assert t.container.b1 == value[1], "value of b1 was not correctly set " + \
        "when compared (%s - set to %s)" % (t.container.b1, value)

  for value in [(0, False), ("0", False), (False, False), ("false", False),
                ("False", False), (1, True), ("1", True), (True, True),
                ("true", True), ("True", True)]:
    passed = True
    try:
      t.container.e1 = value[0]
    except Exception:
      passed = False

    assert passed is True, "value of e1 was not correctly set to %s" % value
    assert t.container.e1 == value[1], "value of e1 was not correctly set " + \
        "when compared (%s - set to %s)" % (t.container.e1, value)

  assert t.container.b2._default is False, "value default was not " + \
      "correctly set (%s)" % t.container.b2._default

  assert t.container.b2._changed() is False, "value was marked as changed " + \
      "incorrectly (%s)" % t.container.b2._changed()

  t.container.b2 = True
  assert t.container.b2._changed() is True, "value was not marked as " + \
      "when it was (%s)" % t.container.b2._changed()

  t.container.b2 = False
  assert t.get() == {'container': {'e1': True, 'b1': True, 'b2': False}}, \
    "wrong get() result returned %s" % t.get()

  if not k:
    os.system("/bin/rm %s/bindings.py" % this_dir)
    os.system("/bin/rm %s/bindings.pyc" % this_dir)


if __name__ == '__main__':
  main()
