def YANGDynClass(*args,**kwargs):
  base_type = kwargs.pop("base", False)
  default = kwargs.pop("default", False)
  if not base_type:
    raise AttributeError, "must have a base type"
  if isinstance(base_type, list):
    # this is a union, we must infer type
    if not len(args):
      # there is no argument to infer the type from
      # so use the first type (default)
      base_type = base_type[0]
    else:
      type_test = False
      for candidate_type in base_type:
        try:
          type_test = candidate_type(args[0]) # does the slipper fit?
          break
        except:
          pass # don't worry, move on, plenty more fish (types) in the sea...
      if not type_test:
        # we're left alone at midnight -- no types fit the arguments
        raise TypeError, "did not find a valid type using the argument as a hint"
      base_type = candidate_type # otherwise, hop, skip and jump with the last candidate
  class YANGBaseClass(base_type):
    def __new__(self, *args, **kwargs):
      obj = base_type.__new__(self, *args, **kwargs)
      return obj

    def __init__(self, *args, **kwargs):
      self._default = False
      self._changed = False
      if default:
        self._default = default
      if len(args):
        if not args[0] == self._default:
          self._changed = True
      try:
        super(YANGBaseClass, self).__init__(*args, **kwargs)
      except:
        print args
        print kwargs
        print base_type
        raise TypeError, "couldn't generate dynamic type"

    def changed(self):
      return self._changed
    def set(self):
      self._changed = True

    # we need to overload the set methods
    def __setitem__(self, *args, **kwargs):
      self._changed = True
      super(YANGBaseClass, self).__setitem__(*args, **kwargs)

    def append(self, *args, **kwargs):
      if not hasattr(super(YANGBaseClass,self), "append"):
        raise AttributeError("%s object has no attribute append" % base_type)
      self.set()
      super(YANGBaseClass, self).append(*args,**kwargs)

    def pop(self, *args, **kwargs):
      if not hasattr(super(YANGBaseClass, self), "pop"):
        raise AttributeError("%s object has no attribute pop" % base_type)
      self.set()
      super(YANGBaseClass, self).pop(*args, **kwargs)

    def remove(self, *args, **kwargs):
      if not hasattr(super(YANGBaseClass, self), "remove"):
        raise AttributeError("%s object has no attribute remove" % base_type)
      self.set()
      super(YANGBaseClass, self).remove(*args, **kwargs)

    def extend(self, *args, **kwargs):
      if not hasattr(super(YANGBaseClass, self), "extend"):
        raise AttributeError("%s object has no attribute extend" % base_type)
      self.set()
      super(YANGBaseClass, self).extend(*args, **kwargs)

    def insert(self, *args, **kwargs):
      if not hasattr(super(YANGBaseClass,self), "insert"):
        raise AttributeError("%s object has no attribute insert" % base_type)
      self.set()
      super(YANGBaseClass, self).insert(*args, **kwargs)

  return YANGBaseClass(*args, **kwargs)

class classTwo(object):
  def __init__(self, *args, **kwargs):
    self.__fish = args[0]

  def get_fish(self):
    return self.__fish

f = YANGDynClass("chips", base=classTwo, default="chips")
g = YANGDynClass("chips", base=str, default="peas")
h = YANGDynClass([],base=list)
i = YANGDynClass(0, base=int)

print f.get_fish()
print f.changed()
print g
print g.changed()
print h
print h.changed()
print i
print i.changed()