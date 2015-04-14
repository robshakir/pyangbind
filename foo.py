from operator import attrgetter
import numpy as np

import collections

def TypedListType(*args, **kwargs):
  allowed_type = kwargs.pop("allowed_type", str)
  # this was from collections.MutableSequence
  class TypedList(collections.MutableSequence):
    _list = list()
    _allowed_type = allowed_type

    def __init__(self, *args, **kwargs):
      self._list.extend(list(args))

    def check(self,v):
      if not isinstance(v, self._allowed_type):
        raise TypeError("Cannot add %s to TypedList (accepts only %s)" % (v, self._allowed_type))

    def __len__(self): return len(self._list)
    def __getitem__(self,i): return self._list[i]
    def __delitem__(self): del self._list[i]
    def __setitem__(self, i, v):
      self.check(v)
      self._list.insert(i,v)

    def insert(self, i, v):
      self.check(v)
      self._list.insert(i,v)

    def __str__(self):
      return str(self._list)

    def get(self):
      return self._list
  return type(TypedList(*args,**kwargs))

def YANGListType(*args,**kwargs):
  keyname = args[0]
  listclass = args[1]
  class YANGList(object):
    _keyval = keyname
    _members = {}
    _contained_class = listclass

    def __init__(self, keyname, contained_class):
      self._keyval = keyname
      if not type(contained_class) == type(int):
        raise ValueError, "contained class of a YANGList must be a class"
      self._contained_class = contained_class

    def __str__(self):
      return self._members.__str__()

    def __repr__(self):
      return self._members.__repr__()

    def __check__(self, v):
      if self._contained_class == None:
        return False
      if not type(v) == type(self._contained_class):
        return False
      return True

    def __getitem__(self, k):
      return self._members[k]

    def __setitem__(self, k, v):
      if self.__check__(v):
        try:
          self._members[k] = defineYANGDynClass(v,base=self._contained_class)
        except TypeError, m:
          raise ValueError, "key value must be valid, %s" % m
      else:
        raise ValueError, "value must be set to an instance of %s" % (self._contained_class)

    def __delitem__(self, k):
      del self._members[k]

    def __len__(self): return len(self._members)

    def add(self, k):
      try:
        self._members[k] = defineYANGDynClass(base=self._contained_class)
        setattr(self._members[k], self._keyval, k)
      except TypeError, m:
        del self._members[k]
        raise ValueError, "key value must be valid, %s" % m

    def get(self):
      d = {}
      for i in self._members:
        if hasattr(self._members[i], "get"):
          d[i] = self._members[i].get()
        else:
          d[i] = self._members[i]
      return d

  return type(YANGList(*args,**kwargs))

class YANGBool(int):
  __v = 0
  def __init__(self,v=False):
    if v in [0, False, "false", "False"]:
      self.__v = 0
    else:
      self.__v = 1
  def __repr__(self):
    return str(True if self.__v else False)


def defineYANGDynClass(*args, **kwargs):
  base_type = kwargs.pop("base",int)
  class YANGDynClass(base_type):
    _changed = False
    _default = False

    def changed(self):
      return self._changed

    def set(self):
      self._changed = True
      # DEBUG

    def child_set(self):
      self.set()

    def __setitem__(self, *args, **kwargs):
      self._changed = True
      super(YANGDynClass, self).__setitem__(*args, **kwargs)

    def append(self, *args, **kwargs):
      if not hasattr(super(YANGDynClass,self), "append"):
        raise AttributeError("%s object has no attribute append" % base_type)
      self.set()
      super(YANGDynClass, self).append(*args,**kwargs)

    def pop(self, *args, **kwargs):
      if not hasattr(super(YANGDynClass, self), "pop"):
        raise AttributeError("%s object has no attribute pop" % base_type)
      self.set()
      super(YANGDynClass, self).pop(*args, **kwargs)

    def remove(self, *args, **kwargs):
      if not hasattr(super(YANGDynClass, self), "remove"):
        raise AttributeError("%s object has no attribute remove" % base_type)
      self.set()
      super(YANGDynClass, self).remove(*args, **kwargs)

    def extend(self, *args, **kwargs):
      if not hasattr(super(YANGDynClass, self), "extend"):
        raise AttributeError("%s object has no attribute extend" % base_type)
      self.set()
      super(YANGDynClass, self).extend(*args, **kwargs)

    def insert(self, *args, **kwargs):
      if not hasattr(super(YANGDynClass,self), "insert"):
        raise AttributeError("%s object has no attribute insert" % base_type)
      self.set()
      super(YANGDynClass, self).insert(*args, **kwargs)

    def __init__(self, *args, **kwargs):
      pass

    def __repr__(self, *args, **kwargs):
      if self._default and not self._changed:
        return repr(self._default)
      else:
        return super(YANGDynClass, self).__repr__()

    def __new__(self, *args, **kwargs):
      default = kwargs.pop("default", None)
      try:
        value = args[0]
      except IndexError:
        value = None

      obj = base_type.__new__(self, *args, **kwargs)
      if default == None:
        if value == None or value == base_type():
          # there was no default, and the value was not set, or was
          # set to the default of the base type
          obj._changed = False
        else:
          # there was no default, and the value was something other
          # than a default - the object has changed
          obj.set()
          # was obj._changed = True
      else:
        # there is a default - if the value is not the same as that default
        # then we have changed the object.
        if value == None:
          # if the value is none, then we have not changed it
          obj._changed = False
        elif not value == default:
          #obj._changed = True
          obj.set()
        else:
          obj._changed = False
      obj._default = default
      return obj

  return YANGDynClass(*args,**kwargs)
class yc_condiments__bar_condiments(object):
  """
     This class was auto-generated by the PythonClass plugin for PYANG
     from YANG module test - based on the path /bar/condiments.
     Each member element of the container is represented as a class
     variable - with a specific YANG type.
    """
  __slots__ = ('__ketchup','__other',)

  __ketchup = defineYANGDynClass(base=str, )
  __other = defineYANGDynClass(base=TypedListType(allowed_type=str), )

  def _get_ketchup(self):
    """
      Getter method for ketchup, mapped from YANG variable /bar/condiments/ketchup (string)
    """
    return self.__ketchup
      
  def _set_ketchup(self,v):
    """
      Setter method for ketchup, mapped from YANG variable /bar/condiments/ketchup (string)
      If this variable is read-only (config: false) in the
      source YANG file, then _set_ketchup is considered as a private
      method. Backends looking to populate this variable should
      do so via calling thisObj._set_ketchup() directly.
    """
    try:
      t = defineYANGDynClass(v,base=str)
    except (TypeError, ValueError):
      raise TypeError("ketchup must be of a type compatible with str")
    self.__ketchup = t

  def _get_other(self):
    """
      Getter method for other, mapped from YANG variable /bar/condiments/other (string)
    """
    return self.__other
      
  def _set_other(self,v):
    """
      Setter method for other, mapped from YANG variable /bar/condiments/other (string)
      If this variable is read-only (config: false) in the
      source YANG file, then _set_other is considered as a private
      method. Backends looking to populate this variable should
      do so via calling thisObj._set_other() directly.
    """
    try:
      t = defineYANGDynClass(v,base=TypedListType)
    except (TypeError, ValueError):
      raise TypeError("other must be of a type compatible with TypedListType")
    self.__other = t

  ketchup = property(_get_ketchup, _set_ketchup)
  other = property(_get_other, _set_other)


  __elements = {'ketchup': ketchup, 'other': other, }


  def elements(self):
    return self.__elements

  def __str__(self):
    return str(self.elements())

  def get(self):
    def error():
      return NameError, "element does not exist"
    d = {}
    for i in self.__elements.keys():
      f = getattr(self, i, error)
      if hasattr(f, "get"):
        d[i] = f.get()
      else:
        if not f.changed() and not f._default == None:
          d[i] = f._default
        else:
          d[i] = f
    return d
  

class yc_bar__bar(object):
  """
     This class was auto-generated by the PythonClass plugin for PYANG
     from YANG module test - based on the path /bar.
     Each member element of the container is represented as a class
     variable - with a specific YANG type.
    """
  __slots__ = ('__fish','__chips','__elephant','__condiments',)

  __fish = defineYANGDynClass(base=YANGBool, )
  __chips = defineYANGDynClass(base=YANGBool, default="False", )
  __elephant = defineYANGDynClass(base=np.uint8, )
  __condiments = defineYANGDynClass(base=yc_condiments__bar_condiments, )

  def _get_fish(self):
    """
      Getter method for fish, mapped from YANG variable /bar/fish (boolean)
    """
    return self.__fish
      
  def _set_fish(self,v):
    """
      Setter method for fish, mapped from YANG variable /bar/fish (boolean)
      If this variable is read-only (config: false) in the
      source YANG file, then _set_fish is considered as a private
      method. Backends looking to populate this variable should
      do so via calling thisObj._set_fish() directly.
    """
    try:
      t = defineYANGDynClass(v,base=YANGBool)
    except (TypeError, ValueError):
      raise TypeError("fish must be of a type compatible with YANGBool")
    self.__fish = t

  def _get_chips(self):
    """
      Getter method for chips, mapped from YANG variable /bar/chips (boolean)
    """
    return self.__chips
      
  def _set_chips(self,v):
    """
      Setter method for chips, mapped from YANG variable /bar/chips (boolean)
      If this variable is read-only (config: false) in the
      source YANG file, then _set_chips is considered as a private
      method. Backends looking to populate this variable should
      do so via calling thisObj._set_chips() directly.
    """
    try:
      t = defineYANGDynClass(v,base=YANGBool)
    except (TypeError, ValueError):
      raise TypeError("chips must be of a type compatible with YANGBool")
    self.__chips = t

  def _get_elephant(self):
    """
      Getter method for elephant, mapped from YANG variable /bar/elephant (uint8)
    """
    return self.__elephant
      
  def _set_elephant(self,v):
    """
      Setter method for elephant, mapped from YANG variable /bar/elephant (uint8)
      If this variable is read-only (config: false) in the
      source YANG file, then _set_elephant is considered as a private
      method. Backends looking to populate this variable should
      do so via calling thisObj._set_elephant() directly.
    """
    try:
      t = defineYANGDynClass(v,base=np.uint8)
    except (TypeError, ValueError):
      raise TypeError("elephant must be of a type compatible with np.uint8")
    self.__elephant = t

  def _get_condiments(self):
    """
      Getter method for condiments, mapped from YANG variable /bar/condiments (container)
    """
    return self.__condiments
      
  def _set_condiments(self,v):
    """
      Setter method for condiments, mapped from YANG variable /bar/condiments (container)
      If this variable is read-only (config: false) in the
      source YANG file, then _set_condiments is considered as a private
      method. Backends looking to populate this variable should
      do so via calling thisObj._set_condiments() directly.
    """
    try:
      t = defineYANGDynClass(v,base=yc_condiments__bar_condiments)
    except (TypeError, ValueError):
      raise TypeError("condiments must be of a type compatible with yc_condiments__bar_condiments")
    self.__condiments = t

  fish = property(_get_fish, _set_fish)
  chips = property(_get_chips, _set_chips)
  elephant = property(_get_elephant, _set_elephant)
  condiments = property(_get_condiments, _set_condiments)


  __elements = {'fish': fish, 'chips': chips, 'elephant': elephant, 'condiments': condiments, }


  def elements(self):
    return self.__elements

  def __str__(self):
    return str(self.elements())

  def get(self):
    def error():
      return NameError, "element does not exist"
    d = {}
    for i in self.__elements.keys():
      f = getattr(self, i, error)
      if hasattr(f, "get"):
        d[i] = f.get()
      else:
        if not f.changed() and not f._default == None:
          d[i] = f._default
        else:
          d[i] = f
    return d
  

class yc_fishhat__state_fishhat(object):
  """
     This class was auto-generated by the PythonClass plugin for PYANG
     from YANG module test - based on the path /state/fishhat.
     Each member element of the container is represented as a class
     variable - with a specific YANG type.
    """
  __slots__ = ('__hats_for_fish',)

  __hats_for_fish = defineYANGDynClass(base=np.uint8, default="10", )

  def _get_hats_for_fish(self):
    """
      Getter method for hats_for_fish, mapped from YANG variable /state/fishhat/hats_for_fish (uint8)
    """
    return self.__hats_for_fish
      
  def _set_hats_for_fish(self,v):
    """
      Setter method for hats_for_fish, mapped from YANG variable /state/fishhat/hats_for_fish (uint8)
      If this variable is read-only (config: false) in the
      source YANG file, then _set_hats_for_fish is considered as a private
      method. Backends looking to populate this variable should
      do so via calling thisObj._set_hats_for_fish() directly.
    """
    try:
      t = defineYANGDynClass(v,base=np.uint8)
    except (TypeError, ValueError):
      raise TypeError("hats_for_fish must be of a type compatible with np.uint8")
    self.__hats_for_fish = t

  hats_for_fish = property(_get_hats_for_fish)


  __elements = {'hats_for_fish': hats_for_fish, }


  def elements(self):
    return self.__elements

  def __str__(self):
    return str(self.elements())

  def get(self):
    def error():
      return NameError, "element does not exist"
    d = {}
    for i in self.__elements.keys():
      f = getattr(self, i, error)
      if hasattr(f, "get"):
        d[i] = f.get()
      else:
        if not f.changed() and not f._default == None:
          d[i] = f._default
        else:
          d[i] = f
    return d
  

class yc_state__state(object):
  """
     This class was auto-generated by the PythonClass plugin for PYANG
     from YANG module test - based on the path /state.
     Each member element of the container is represented as a class
     variable - with a specific YANG type.
    """
  __slots__ = ('__fishhat',)

  __fishhat = defineYANGDynClass(base=yc_fishhat__state_fishhat, )

  def _get_fishhat(self):
    """
      Getter method for fishhat, mapped from YANG variable /state/fishhat (container)
    """
    return self.__fishhat
      
  def _set_fishhat(self,v):
    """
      Setter method for fishhat, mapped from YANG variable /state/fishhat (container)
      If this variable is read-only (config: false) in the
      source YANG file, then _set_fishhat is considered as a private
      method. Backends looking to populate this variable should
      do so via calling thisObj._set_fishhat() directly.
    """
    try:
      t = defineYANGDynClass(v,base=yc_fishhat__state_fishhat)
    except (TypeError, ValueError):
      raise TypeError("fishhat must be of a type compatible with yc_fishhat__state_fishhat")
    self.__fishhat = t

  fishhat = property(_get_fishhat, _set_fishhat)


  __elements = {'fishhat': fishhat, }


  def elements(self):
    return self.__elements

  def __str__(self):
    return str(self.elements())

  def get(self):
    def error():
      return NameError, "element does not exist"
    d = {}
    for i in self.__elements.keys():
      f = getattr(self, i, error)
      if hasattr(f, "get"):
        d[i] = f.get()
      else:
        if not f.changed() and not f._default == None:
          d[i] = f._default
        else:
          d[i] = f
    return d
  

class test(object):
  """
     This class was auto-generated by the PythonClass plugin for PYANG
     from YANG module test - based on the path /.
     Each member element of the container is represented as a class
     variable - with a specific YANG type.
    """
  __slots__ = ('__bar','__state',)

  __bar = defineYANGDynClass(base=yc_bar__bar, )
  __state = defineYANGDynClass(base=yc_state__state, )

  def _get_bar(self):
    """
      Getter method for bar, mapped from YANG variable /bar (container)
    """
    return self.__bar
      
  def _set_bar(self,v):
    """
      Setter method for bar, mapped from YANG variable /bar (container)
      If this variable is read-only (config: false) in the
      source YANG file, then _set_bar is considered as a private
      method. Backends looking to populate this variable should
      do so via calling thisObj._set_bar() directly.
    """
    try:
      t = defineYANGDynClass(v,base=yc_bar__bar)
    except (TypeError, ValueError):
      raise TypeError("bar must be of a type compatible with yc_bar__bar")
    self.__bar = t

  def _get_state(self):
    """
      Getter method for state, mapped from YANG variable /state (container)
    """
    return self.__state
      
  def _set_state(self,v):
    """
      Setter method for state, mapped from YANG variable /state (container)
      If this variable is read-only (config: false) in the
      source YANG file, then _set_state is considered as a private
      method. Backends looking to populate this variable should
      do so via calling thisObj._set_state() directly.
    """
    try:
      t = defineYANGDynClass(v,base=yc_state__state)
    except (TypeError, ValueError):
      raise TypeError("state must be of a type compatible with yc_state__state")
    self.__state = t

  bar = property(_get_bar, _set_bar)
  state = property(_get_state, _set_state)


  __elements = {'bar': bar, 'state': state, }


  def elements(self):
    return self.__elements

  def __str__(self):
    return str(self.elements())

  def get(self):
    def error():
      return NameError, "element does not exist"
    d = {}
    for i in self.__elements.keys():
      f = getattr(self, i, error)
      if hasattr(f, "get"):
        d[i] = f.get()
      else:
        if not f.changed() and not f._default == None:
          d[i] = f._default
        else:
          d[i] = f
    return d
  

