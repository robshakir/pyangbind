#def YANGEnumType(*args, **kwargs):
class YANGEnum(str):
  _enum_dict = {}

  def __new__(self, *args, **kwargs):
    enum_spec = kwargs.pop("enum_spec")
    initial = kwargs.pop("initial")
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
      c += 1
    if len(args) and not self.__check(args[0]):
      raise AttributeError, "invalid string"
    obj = str.__init__(self, *args, **kwargs)
    return obj

  def __check(self, value):
    if not value in self._enum_dict.keys():
      return False
    return True

  def __set__(self, instance, value):
    print "hit here"

#  return type(YANGEnum(*args, **kwargs))

class foo:
  ip_version = YANGEnum(initial=None, enum_spec={"unknown": {"value": 0}, "ipv4": {"value": 1,}, "ipv6": {"value": 2}})

print foo.ip_version
foo.ip_version = "unknown"
print foo.ip_version
foo.ip_version = "twentyseven"
print foo.ip_version