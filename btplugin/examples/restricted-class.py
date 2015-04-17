
import re

class YANGEnum(object):
  _enum_dict = {}
  _enum_value = None

  def __init__(self, enum_spec, initial=False):
    # we use a dictionary as enum_spec because we may
    # (in the future) need to support some other elements
    # as well as value. Y25 may remove value, but 
    #  we support it here just in case.
    # enum_spec = {"ipv4-version": {"value": 0,}} 
    assigned_vals = []
    for k,v in enum_spec.iteritems():
      if v == None:
        continue
      elif "value" in v.keys():
        try:
          assigned_vals.append(int(v["value"]))
        except:
          raise AttributeError, "values assigned to YANG enum" \
            + " types must be an integer"
    c = 0
    for k,v in enum_spec.iteritems():
      if v == None or type(v) == type({}) and not "value" in v.keys():
        self._enum_dict[k] = {"value": c}
      else:
        self._enum_dict[k] = v

    if initial and self.__check(initial):
      self._enum_value = initial

  def __check(self, value):
    if value not in self._enum_dict.keys():
      return False
    return True

  def options(self,):
    return self._enum_dict.keys()

  def set(self,v):
    if self.__check(v):
      self._enum_value = v
    else:
      raise AttributeError, "value must be in enumeration"

  def get(self):
    return self._enum_value

  def getValue(self):
    return self._enum_dict[self._enum_value]["value"]


ip_version = YANGEnum({"unknown": {"value": 0}, "ipv4": {"value": 1,}, "ipv6": {"value": 2}})
print ip_version.options()

ip_version.set("ipv6")

flag = False
try:
  ip_version.set("ipv8")
except:
  flag = True

print flag

print ip_version.get()
print ip_version.getValue()





import sys
sys.exit(127)


def RestrictedClassType(*args, **kwargs):
  base_type = kwargs.pop("base_type", str)
  restriction_type = kwargs.pop("restriction_type", None)
  restriction_arg = kwargs.pop("restriction_arg", None)

  class RestrictedClass(base_type):
    _restriction_type = restriction_type
    _restriction_arg = restriction_arg
    _restriction_test = None

    def __init__(self, *args, **kwargs):
      try:
        self.__check(args[0])
      except IndexError:
        pass
      super(RestrictedClass, self).__init__(*args, **kwargs)

    def __new__(self, *args, **kwargs):
      if restriction_type == "pattern":
        p = re.compile(restriction_arg)
        self._restriction_test = p.match
        self._restriction_arg = restriction_arg
        self._restriction_type = restriction_type
      elif restriction_type == "range":
        x = [base_type(i) for i in \
          re.sub("(?P<low>[0-9]+)([ ]+)?\.\.([ ]+)?(?P<high>[0-9]+)", "\g<low>,\g<high>", \
           restriction_arg).split(",")]
        self._restriction_test = staticmethod(lambda i: i in range(x[0], x[1]))
        self._restriction_arg = restriction_arg
        self._restriction_type = restriction_type
      else:
        raise ValueError, "unsupported restriction type"
      try:
        if not self._restriction_test(args[0]):
          raise ValueError, "did not match restricted type"
      except IndexError:
        pass
      obj = base_type.__new__(self, *args, **kwargs)
      return obj

    def __check(self, v):
      if self._restriction_type == "pattern":
        if not self._restriction_test(v):
          raise ValueError, "did not match restricted type"
        return True

    def __setitem__(self, *args, **kwargs):
      self.__check(args[0])
      super(RestrictedClass, self).__setitem__(*args, **kwargs)

  return type(RestrictedClass(*args, **kwargs))


t = RestrictedClassType("aardvark", base_type=str, restriction_type="pattern", restriction_arg="^a")
print type(t)
print t
t="fish"
print type(t)

