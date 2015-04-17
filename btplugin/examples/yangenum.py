

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

class foo:
  ip_version = YANGEnum({"unknown": {"value": 0}, "ipv4": {"value": 1,}, "ipv6": {"value": 2}})

f = foo()
print "hello"

print type(f.ip_version)
print f.ip_version.get()
f.ip_version.set("ipv4")
print f.ip_version.get()
f.ip_version.set("ipv8")