#!/usr/bin/env python

import os
import sys
import getopt

TESTNAME = "rpc"


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
  cmd += " -f pybind "
  cmd += " --split-class-dir=%s/bindings" % this_dir
  cmd += " -p %s" % this_dir
  cmd += " --use-xpathhelper --build-rpc"
  cmd += " %s/%s.yang" % (this_dir, TESTNAME)
  os.system(cmd)

  from pyangbind.lib.xpathhelper import YANGPathHelper
  ph = YANGPathHelper()

  import_error = None
  set_argument_error = None
  try:
    from bindings.rpc_rpc import check
    ch = check.check(path_helper=ph)
    ch.input.argument = "test"
  except ImportError as m:
    import_error = m
  except ValueError as m:
    set_argument_error = m

  assert import_error is None, "Could not import check RPC: %s" \
            % (import_error)
  assert set_argument_error is None, "Could not set argument to string: %s" \
            % (set_argument_error)

  import_error = None
  instantiation_error = None
  try:
    from bindings.rpc_rpc.check_two import output as chktwo_output
    ch = chktwo_output.output(path_helper=ph)
  except ImportError as m:
    import_error = m
  except TypeError as m:
    instantiation_error = m

  assert import_error is None, "Could not import check_two RPC output: %s" \
            % (import_error)
  assert instantiation_error is None, "Could not instantiate check_two " + \
            + "output: %s" % (instantiation_error)

  try:
    ch.arg_one = 10
    ch.arg_two = 20
  except ValueError as m:
    raise AssertionError("Could not set output leaf arguments directly: %s" % (m))

  from bindings.rpc_rpc import check_three, check_four, check_five, check_six

  ch3 = check_three.check_three(path_helper=ph)
  ch4 = check_four.check_four(path_helper=ph)
  ch5 = check_five.check_five(path_helper=ph)
  ch6 = check_six.check_six(path_helper=ph)

  attribute_err = None
  value_err = None
  try:
    ch3.input.arguments.arg_one = "test string"
  except AttributeError as m:
    attribute_err = m
  except ValueError as m:
    value_err = m

  assert attribute_err is None, "Expected attribute for ch3 did not exist" \
          + " (arg-one): %s" % attribute_err
  assert value_err is None, "Expected value could not be set for ch3" \
          + " (arg-one): %s" % value_err

  attribute_err = None
  value_err = None
  try:
    ch3.input.arguments.arg_two = "test string"
  except AttributeError as m:
    attribute_err = m
  except ValueError as m:
    value_err = m

  assert attribute_err is None, "Expected attribute for ch3 did not exist" \
          + " (arg-two): %s" % attribute_err
  assert value_err is None, "Expected value could not be set for ch3" \
          + " (arg-two): %s" % value_err

  attribute_err = None
  value_err = None
  try:
    ch4.output.arguments.arg_one = "test string"
  except AttributeError as m:
    attribute_err = m
  except ValueError as m:
    value_err = m

  assert attribute_err is None, "Expected attribute for ch4 did not exist" \
          + " (arg-one): %s" % attribute_err
  assert value_err is None, "Expected value could not be set for ch4" \
          + " (arg-one): %s" % value_err

  attribute_err = None
  value_err = None
  try:
    ch4.output.arguments_two.arg_two = "test string"
  except AttributeError as m:
    attribute_err = m
  except ValueError as m:
    value_err = m

  assert attribute_err is None, "Expected attribute for ch4 did not exist" \
          + " (arg-two): %s" % attribute_err
  assert value_err is None, "Expected value could not be set for ch4" \
          + " (arg-two): %s" % value_err

  attribute_err = None
  value_err = None
  try:
    ch5.input.arguments.arg_one = "test string"
  except AttributeError as m:
    attribute_err = m
  except ValueError as m:
    value_err = m

  assert attribute_err is None, "Expected attribute for ch5 did not exist" \
          + " (arg-one): %s" % attribute_err
  assert value_err is None, "Expected value could not be set for ch5" \
          + " (arg-one): %s" % value_err

  attribute_err = None
  value_err = None
  try:
    ch5.output.return_values.return_val = 10
  except AttributeError as m:
    attribute_err = m
  except ValueError as m:
    value_err = m

  assert attribute_err is None, "Expected attribute for ch4 did not exist" \
          + " (arg-two): %s" % attribute_err
  assert value_err is None, "Expected value could not be set for ch5" \
          + " (arg-two): %s" % value_err

  assert ph.get_unique("/").get() == {}, "Attributes within an RPC registered" + \
        " in the path helper erroneously"

  from bindings import rpc

  r = rpc(path_helper=ph)
  r.test.reference_target.append('six')

  set_v = True
  try:
    ch6.input.argument = 'six'
  except ValueError as m:
    set_v = False

  assert set_v is True, "Could not set value of a leafref in an RPC to a" + \
          "known good value: %s != True (ch.input.argument -> six)" % (set_v)

  set_v = True
  try:
    ch6.input.argument = 'fish'
  except ValueError as m:
    set_v = False

  assert set_v is False, "Set value of a leafref in an RPC to a" + \
          "known bad value: %s != False (ch.input.argument -> fish)" % (set_v)

  if not k:
    os.system("/bin/rm -rf %s/bindings" % this_dir)


if __name__ == '__main__':
  main()
