#!/usr/bin/env python

import os
import sys
import getopt

TESTNAME = "notification"


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

  cmd = "%s " % pythonpath
  cmd += "%s --plugindir %s/pyangbind/plugin" % (pyangpath, pyangbindpath)
  cmd += " -f pybind "
  cmd += " --split-class-dir=%s/bindings" % this_dir
  cmd += " -p %s" % this_dir
  cmd += " --use-xpathhelper --build-notifications"
  cmd += " %s/%s.yang" % (this_dir, TESTNAME)
  os.system(cmd)

  from pyangbind.lib.xpathhelper import YANGPathHelper
  ph = YANGPathHelper()

  import_error = None
  set_argument_error = None
  try:
    from bindings.notification_notification import alert_one
    ch = alert_one.alert_one(path_helper=ph)
    ch.argument = "test"
  except ImportError, m:
    import_error = m
  except ValueError, m:
    set_argument_error = m

  assert import_error is None, "Could not import alert_one notification: %s" \
            % (import_error)
  assert set_argument_error is None, "Could not set argument to string: %s" \
            % (set_argument_error)

  import_error = None
  instantiation_error = None
  try:
    from bindings.notification_notification import alert_two
    ch = alert_two.alert_two(path_helper=ph)
  except ImportError, m:
    import_error = m
  except TypeError, m:
    instantiation_error = m

  assert import_error is None, "Could not import alert_two notification: %s" \
            % (import_error)
  assert instantiation_error is None, "Could not instantiate alert_two: %s" \
            % (instantiation_error)

  val_set = True
  try:
    ch.arg_one = 10
    ch.arg_two = 20
  except ValueError, m:
    val_set = False

  assert val_set is True, "Could not set leaf arguments directly" + \
          + ": %s" % (m)

  from bindings.notification_notification import alert_three, alert_four, alert_five

  ch3 = alert_three.alert_three(path_helper=ph)
  ch4 = alert_four.alert_four(path_helper=ph)
  ch5 = alert_five.alert_five(path_helper=ph)

  attribute_err = None
  value_err = None
  try:
    ch3.arguments.arg_one = "test string"
  except AttributeError, m:
    attribute_err = m
  except ValueError, m:
    value_err = m

  assert attribute_err is None, "Expected attribute for ch3 did not exist" \
          + " (arg-one): %s" % attribute_err
  assert value_err is None, "Expected value could not be set for ch3" \
          + " (arg-one): %s" % value_err

  attribute_err = None
  value_err = None
  try:
    ch3.arguments.arg_two = "test string"
  except AttributeError, m:
    attribute_err = m
  except ValueError, m:
    value_err = m

  assert attribute_err is None, "Expected attribute for ch3 did not exist" \
          + " (arg-two): %s" % attribute_err
  assert value_err is None, "Expected value could not be set for ch3" \
          + " (arg-two): %s" % value_err

  attribute_err = None
  value_err = None
  try:
    ch4.arguments_one.arg_one = "test string"
  except AttributeError, m:
    attribute_err = m
  except ValueError, m:
    value_err = m

  assert attribute_err is None, "Expected attribute for ch4 did not exist" \
          + " (arg-one): %s" % attribute_err
  assert value_err is None, "Expected value could not be set for ch4" \
          + " (arg-one): %s" % value_err

  attribute_err = None
  value_err = None
  try:
    ch4.arguments_two.arg_two = "test string"
  except AttributeError, m:
    attribute_err = m
  except ValueError, m:
    value_err = m

  assert attribute_err is None, "Expected attribute for ch4 did not exist" \
          + " (arg-two): %s" % attribute_err
  assert value_err is None, "Expected value could not be set for ch4" \
          + " (arg-two): %s" % value_err

  from bindings import notification

  r = notification(path_helper=ph)
  r.test.reference_target.append('five')

  set_v = True
  try:
    ch5.argument = 'five'
  except ValueError, m:
    set_v = False

  assert set_v is True, "Could not set value of a leafref in a notification to a" + \
          "known good value: %s != True (ch.argument -> five)" % (set_v)

  set_v = True
  try:
    ch5.argument = 'fish'
  except ValueError, m:
    set_v = False

  assert set_v is False, "Set value of a leafref in a notification to a" + \
          "known bad value: %s != False (ch.argument -> fish)" % (set_v)

  if not k:
    os.system("/bin/rm -rf %s/bindings" % this_dir)

if __name__ == '__main__':
  main()
