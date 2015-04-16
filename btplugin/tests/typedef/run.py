#!/usr/bin/env python

import os, sys, getopt

TESTNAME="typedef"

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

  this_dir = os.path.dirname(os.path.realpath(__file__))
  os.system("/Users/rjs/Code/pyang/bin/pyang \
            --plugindir /Users/rjs/Code/pyangbind/btplugin \
            -p %s -f bt \
            -o %s/bindings.py %s/%s.yang" % (this_dir, this_dir, this_dir, TESTNAME))

  from bindings import typedef
  t = typedef()

  for element in ["string", "integer", "stringdefault", "integerdefault", "new_string", "remote_new_type"]:
    assert hasattr(t.container, element), "element %s did not exist within the container" % element

  t.container.string = "hello"
  assert t.container.string == "hello", \
    "incorrect value set for the string container (value: %s)" \
    % t.container.string

  assert t.container.stringdefault._default == "aDefaultValue", \
    "incorrect default value for derived string type with a default (value: %s)" % \
    t.container.stringdefault._default

  assert t.container.new_string._default == "defaultValue", \
    "incorrect default value where derived from typedef (value: %s)" % \
    t.container.new_string._default

  t.container.integer = 1
  assert t.container.integer == 1, \
    "integer value not correctly updated"

  passed = False
  try:
    t.container.integer = 65 # outside of range
  except:
    passed = True

  assert passed == True, "restricted int from typedef was set to invalid value"

  t.container.remote_new_type = "testString"
  assert t.container.remote_new_type == "testString", \
    "incorrect value for the remote definition (%s)" % \
      t.container.remote_new_type


  if not k:
    os.system("/bin/rm %s/bindings.py" % this_dir)
    os.system("/bin/rm %s/bindings.pyc" % this_dir)

if __name__ == '__main__':
  main()