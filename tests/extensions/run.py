#!/usr/bin/env python

import os
import sys
import getopt

TESTNAME = "extensions"


# generate bindings in this folder
def main():
  try:
    opts, args = getopt.getopt(sys.argv[1:], "k", ["keepfiles"])
  except getopt.GetoptError as e:
    print(str(e))
    sys.exit(127)

  keep = False
  for o, a in opts:
    if o in ["-k", "--keepfiles"]:
      keep = True

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
  cmd += " --interesting-extension=extdef"
  cmd += " --interesting-extension=extdef-two"
  cmd += " %s/%s.yang" % (this_dir, TESTNAME)
  os.system(cmd)

  from bindings import extensions as e

  ext = e()

  assert ext.test._extensions() == {'extdef': {'extension-one': 'version'}}, \
    "Did not extract extensions correctly from container object " + \
      "was: %s" % ext.test._extensions()

  assert ext.test.one._extensions() is None, \
    "Incorrectly found extensions for a leaf with none specified " + \
      "was %s" % ext.test.one._extensions()

  assert ext.test_two._extensions() is None, \
    "Incorrectly found extensions for a container with none specified " + \
      "was: %s" % ext.test_two.extensions()

  assert ext.test_two.two._extensions() == {'extdef': {'extension-two': 'value'}}, \
    "Did not extract extensions correctly for a leaf (was: %s)" % \
      ext.test_two.two._extensions()

  assert ext.l._extensions() == {'extdef': {'extension-two': 'from-list'}}, \
    "Did not extract extensions correctly for a list, was: %s" % \
      ext.l._extensions()

  x = ext.l.add(1)
  assert x._extensions() == {'extdef': {'extension-two': 'from-list'}}, \
    "Did not extract extensions correctly for list member, was: %s" % \
      x._extensions()

  for k in [('extdef', True, 'extension-one', 'from-leaf'),
            ('extdef', True, 'extension-two', 'from-leaf'),
            ('extdef-two', False, None, None),
            ('extdef-irr', False, None, None)]:
    assert (k[0] in x.k._extensions()) is k[1], \
      "Extension module %s in leaf k was expected to be %s was %s" % \
        (k[0], k[1], k[0] in x.k._extensions())

    if k[1] is True:
      assert k[2] in x.k._extensions()[k[0]], \
        "Extension %s was not defined for module %s" % \
          (k[2], k[0])

      assert x.k._extensions()[k[0]][k[2]] == k[3], \
        "Extension %s:%s was expected to be %s was %s" % \
          (k[0], k[2], k[3], x.k._extensions()[k[0]][k[2]])

  for k in [('extdef', True, 'extension-two', 'from-q'),
            ('extdef-two', True, 'extension-three', 'from-q'),
            ('extdef-irr', False, None, None)]:

    assert (k[0] in x.q._extensions()) is k[1], \
      "Extension module %s in leaf k was expected to be %s was %s" % \
        (k[0], k[1], k[0] in x.q._extensions())

    if k[1] is True:
      assert k[2] in x.q._extensions()[k[0]], \
        "Extension %s was not defined for module %s" % \
          (k[2], k[0])

      assert x.q._extensions()[k[0]][k[2]] == k[3], \
        "Extension %s:%s was expected to be %s was %s" % \
          (k[0], k[2], k[3], x.q._extensions()[k[0]][k[2]])

  if not keep:
    os.system("/bin/rm %s/bindings.py" % this_dir)
    os.system("/bin/rm %s/bindings.pyc" % this_dir)


if __name__ == '__main__':
  main()
