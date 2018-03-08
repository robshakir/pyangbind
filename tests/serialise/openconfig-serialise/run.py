#!/usr/bin/env python

import os
import sys
import getopt
import json
import requests
import time
import re
import difflib

from pyangbind.lib.xpathhelper import YANGPathHelper
from pyangbind.lib.pybindJSON import dumps
from pyangbind.lib.serialise import pybindIETFJSONEncoder, pybindJSONEncoder
from pyangbind.lib.yangtypes import YANGBool

TESTNAME = "json-serialise"


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

  pythonpath = os.environ.get("PATH_TO_PYBIND_TEST_PYTHON") if \
                os.environ.get('PATH_TO_PYBIND_TEST_PYTHON') is not None \
                  else sys.executable
  pyangpath = os.environ.get('PYANGPATH') if \
                os.environ.get('PYANGPATH') is not None else False
  pyangbindpath = os.environ.get('PYANGBINDPATH') if \
                os.environ.get('PYANGBINDPATH') is not None else False
  assert pyangpath is not False, "could not find path to pyang"
  assert pyangbindpath is not False, "could not resolve pyangbind directory"

  OC = "https://raw.githubusercontent.com/openconfig/" + \
            "public/master/release/models/"
  RFC = "https://raw.githubusercontent.com/robshakir/" + \
            "yang/master/standard/ietf/RFC/"
  FETCH_FILES = [
                  (OC + "openconfig-extensions.yang", "include"),
                  (OC + "types/openconfig-types.yang", "include"),
                  (OC + "types/openconfig-yang-types.yang", "include"),
                  (OC + "types/openconfig-inet-types.yang", "include"),
                  (OC + "interfaces/openconfig-interfaces.yang", "openconfig"),
                  (RFC + "ietf-inet-types.yang", "include"),
                  (RFC + "ietf-yang-types.yang", "include"),
                ]

  this_dir = os.path.dirname(os.path.realpath(__file__))
  del_dirs = []
  for fn in FETCH_FILES:
    wrdir = os.path.join(this_dir, fn[1])
    if not os.path.exists(wrdir):
      os.mkdir(wrdir)
    if wrdir not in del_dirs:
      del_dirs.append(wrdir)
    wrpath = os.path.join(this_dir, fn[1], fn[0].split("/")[-1])
    if not os.path.exists(wrpath):
      got = False
      for i in range(0, 4):
        response = requests.get(fn[0])
        if response.status_code != 200:
          time.sleep(2)
        else:
          got = True
          f = open(wrpath, 'w')
          f.write(response.content)
          f.close()
          break
      assert got is True, "Could not get file %s from GitHub (response: %s)" \
                % (response.status_code, fn[0])

  files_str = " ".join([os.path.join(this_dir, "openconfig", i) for i in
                        os.listdir(os.path.join(this_dir, "openconfig"))])

  cmd = "%s " % pythonpath
  cmd += "%s --plugindir %s/pyangbind/plugin" % (pyangpath, pyangbindpath)
  cmd += " -f pybind --split-class-dir %s/ocbind" % this_dir
  cmd += " -p %s" % this_dir
  cmd += " -p %s" % os.path.join(this_dir, "include")
  cmd += " --use-xpathhelper "
  cmd += files_str
  os.system(cmd)

  from ocbind import openconfig_interfaces

  for fn in os.listdir(os.path.join(this_dir, "json")):
    jobj = json.load(open(os.path.join(this_dir, "json", fn), 'r'))
    parameters = re.sub(
      'interfaces\_ph:(?P<pathhelper>[a-zA-Z]+)\-flt:(?P<filter>[a-zA-Z]+)\-m:(?P<mode>[a-zA-Z]+)\.json',
      '\g<pathhelper>||\g<filter>||\g<mode>', fn).split("||")
    path_helper, config_filter, mode = YANGBool(parameters[0]), YANGBool(parameters[1]), parameters[2]

    if path_helper:
      ph = YANGPathHelper()
      i = openconfig_interfaces(path_helper=ph)
    else:
      i = openconfig_interfaces()

    i.interfaces.interface.add("eth0")

    jstr = json.loads(dumps(i, filter=bool(config_filter), mode=mode))
    sys.stdout.flush()

    assert jstr == jobj, "Generated JSON did not match expected object for %s" % fn \
            + " diff:\n%s" % (diff(jstr, jobj))

    passed = True
    try:
      jstr = json.loads(json.dumps(pybindIETFJSONEncoder.generate_element(i), cls=pybindIETFJSONEncoder))
    except Exception as e:
      passed = False

    assert passed, "Serialisation test for object with pybindIETFJSONEncoder threw an error"

    jstr = json.loads(json.dumps(i, cls=pybindJSONEncoder))

  if not k:
    del_dirs.append(os.path.join(this_dir, "ocbind"))
    for dirname in del_dirs:
      for root, dirs, files in os.walk(os.path.join(dirname), topdown=False):
        for name in files:
          os.remove(os.path.join(root, name))
        for name in dirs:
          os.rmdir(os.path.join(root, name))
      os.rmdir(dirname)


def diff(a, b):
    ja = json.dumps(a, indent=4, sort_keys=True).split("\n")
    jb = json.dumps(b, indent=4, sort_keys=True).split("\n")
    return '\n'.join(difflib.unified_diff(ja, jb))


if __name__ == '__main__':
  main()
