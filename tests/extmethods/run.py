#!/usr/bin/env python

import os
import sys
import getopt

TESTNAME = "extmethods"


class extmethodcls(object):
  def commit(self, *args, **kwargs):
    return "COMMIT_CALLED"

  def presave(self, *args, **kwargs):
    return "PRESAVE_CALLED"

  def postsave(self, *args, **kwargs):
    return "POSTSAVE_CALLED"

  def oam_check(self, *args, **kwargs):
    return "OAM_CHECK_CALLED"

  def echo(self, *args, **kwargs):
    return {'args': args, 'kwargs': kwargs}


# generate bindings in this folder
def main():
  try:
    opts, args = getopt.getopt(sys.argv[1:], "k", ["keepfiles"])
  except getopt.GetoptError:
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
  cmd += " --use-extmethods"
  cmd += " %s/%s.yang" % (this_dir, TESTNAME)
  os.system(cmd)

  extdict = {
    '/item/one': extmethodcls()
  }

  from bindings import extmethods
  x = extmethods(extmethods=extdict)

  results = [
                ("commit", True, "COMMIT_CALLED"),
                ("presave", True, "PRESAVE_CALLED"),
                ("postsave", True, "POSTSAVE_CALLED"),
                ("oam_check", True, "OAM_CHECK_CALLED"),
                ("doesnotexist", False, "")
            ]

  for chk in results:
    method = getattr(x.item.one, "_" + chk[0], None)
    assert (method is not None) == chk[1], \
              "Method %s retrieved incorrectly, method was: %s" % method
    if method is not None:
      result = method()
      assert result == chk[2], "Incorrect return from %s -> %s != %s" \
              % (chk[0], result, chk[2])

  expected_return = {'args': ('one',), 'kwargs': {'caller': ['item', 'one'],
                    'two': 2, 'path_helper': False}}
  assert x.item.one._echo('one', two=2) == expected_return, \
          "args+kwargs not echoed correctly"

  try:
    x.item.two = False
    assert False, \
        "incorrectly set an attribute that did not exist in extmethods"
  except AttributeError:
    pass

  if not k:
    os.system("/bin/rm %s/bindings.py" % this_dir)
    os.system("/bin/rm %s/bindings.pyc" % this_dir)


if __name__ == '__main__':
  main()
