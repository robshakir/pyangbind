#!/usr/bin/env python

import os
import sys
import getopt
import json
import pyangbind.lib.serialise as pbS
import pyangbind.lib.pybindJSON as pbJ
from bitarray import bitarray
from pyangbind.lib.xpathhelper import YANGPathHelper

TESTNAME = "json-deserialise"


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

  this_dir = os.path.dirname(os.path.realpath(__file__))

  cmd = "%s "% pythonpath
  cmd += "%s --plugindir %s/pyangbind/plugin" % (pyangpath, pyangbindpath)
  cmd += " -f pybind -o %s/bindings.py" % this_dir
  cmd += " -p %s" % this_dir
  cmd += " %s/%s.yang" % (this_dir, TESTNAME)
  os.system(cmd)

  import bindings

  y = YANGPathHelper()

  # For developers looking for examples, note that the arguments here are:
  #   - the file that we're trying to read
  #   - the bindings module that we generated
  #   - the name of the class within that module
  #   kwargs (path_helper, overwrite, etc.)
  whole_obj = pbJ.load(os.path.join(this_dir, "json", "list.json"), bindings,
                "json_deserialise", path_helper=y)

  expected_whole_obj = {'load-list': {u'1': {'index': 1, 'value': u'one'}, u'3': {'index': 3, 'value': u'three'}, u'2': {'index': 2, 'value': u'two'}}}
  assert expected_whole_obj == whole_obj.get(filter=True), "Whole object load did not return the correct list"
  del whole_obj

  js = bindings.json_deserialise(path_helper=y)
  # Load into an existing class
  pbS.pybindJSONDecoder.load_json(json.load(open(os.path.join(this_dir, "json", "list-items.json"), 'r')), None, None, obj=js)
  expected_get = {'load-list': {u'5': {'index': 5, 'value': u'five'}, u'4': {'index': 4, 'value': u'four'}}}
  assert expected_get == js.get(filter=True), "Existing object load did not return the correct list"
  del expected_get

  all_items = pbJ.load(os.path.join(this_dir, "json", "alltypes.json"), bindings,
                "json_deserialise", path_helper=y)
  expected_get = {
      'c1': {
        'l1': {
          u'1': {
            'one-leaf': u'hi',
            'typedef-one': u'test',
            'boolean': True,
            'binary': bitarray('111111'),
            'union': u'16',
            'identityref': u'idone',
            'enumeration': u'one',
            'k1': 1,
            'uint16': 1,
            'union-list': [16, u'chicken'],
            'uint32': 1,
            'int32': 1,
            'int16': 1,
            'string': u'bear',
            'typedef-two': 8,
            'uint8': 1,
            'restricted-integer': 6,
            'leafref': u'16',
            'int8': 1,
            'uint64': 1,
            'int64': 1,
            'restricted-string': u'aardvark'
          }
        },
        't1': {
          u'32': {'target': u'32'},
          u'16': {'target': u'16'}
        }
      }
    }
  assert all_items.get(filter=True) == expected_get, "Load of object with all items not correct"

  del js
  js = pbJ.load(os.path.join(this_dir, "json", "orderedlist-order.json"), bindings,
                "json_deserialise", path_helper=y)
  assert js.ordered.keys() == ["two", "one"], "Did not correctly load a user ordered list"

  del js
  js = pbJ.load(os.path.join(this_dir, "json", "orderedlist-no-order.json"), bindings,
                "json_deserialise", path_helper=y)
  assert js.ordered.keys() == ["one", "two"], "Did not correctly follow ordering in JSON file"


  if not k:
    os.system("/bin/rm %s/bindings.py" % this_dir)
    os.system("/bin/rm %s/bindings.pyc" % this_dir)

if __name__ == '__main__':
  main()
