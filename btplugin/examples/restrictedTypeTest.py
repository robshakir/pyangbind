from operator import attrgetter
import numpy as np

import collections
import re

def RestrictedClassError(Exception):
  pass

def RestrictedClassType(*args, **kwargs):
  base_type = kwargs.pop("base_type", str)
  restriction_type = kwargs.pop("restriction_type", None)
  restriction_arg = kwargs.pop("restriction_arg", None)

  class RestrictedClass(base_type):
    _restriction_type = restriction_type
    _restriction_arg = restriction_arg
    _restriction_test = None

    def __init__(self, *args, **kwargs):
      if self._restriction_type == "pattern":
        p = re.compile(self._restriction_arg)
        self._restriction_test = p.match
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
        x = [base_type(i) for i in re.sub("(?P<low>[0-9]+)([ ]+)?\.\.([ ]+)?(?P<high>[0-9]+)", "\g<low>,\g<high>", restriction_arg).split(",")]
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
    def __getitem__(self, i): return self._list[i]
    def __delitem__(self, i): del self._list[i]
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
        obj._default = base_type(default)
      return obj

  return YANGDynClass(*args,**kwargs)
class yc_string_container__string_container(object):
  """
     This class was auto-generated by the PythonClass plugin for PYANG
     from YANG module string - based on the path /string-container.
     Each member element of the container is represented as a class
     variable - with a specific YANG type.
    """
  __slots__ = ('__string_leaf','__string_default_leaf',)

  __string_leaf = defineYANGDynClass(base=RestrictedClassType(base_type=str, restriction_type="pattern", restriction_arg="^a"),default="aardvark")
  __string_default_leaf = defineYANGDynClass(base=RestrictedClassType(base_type=int, restriction_type="range", restriction_arg="0..63"))

  def _get_string_leaf(self):
    """
      Getter method for string_leaf, mapped from YANG variable /string_container/string_leaf (string)
    """
    return self.__string_leaf
      
  def _set_string_leaf(self,v):
    """
      Setter method for string_leaf, mapped from YANG variable /string_container/string_leaf (string)
      If this variable is read-only (config: false) in the
      source YANG file, then _set_string_leaf is considered as a private
      method. Backends looking to populate this variable should
      do so via calling thisObj._set_string_leaf() directly.
    """
    try:
      t = defineYANGDynClass(v,base=RestrictedClassType(base_type=str, restriction_type="pattern", restriction_arg="^a"))
      print t
    except (TypeError, ValueError):
      raise TypeError("string_leaf must be of a type compatible with str")
    self.__string_leaf = t
    self.set()

  def _get_string_default_leaf(self):
    """
      Getter method for string_default_leaf, mapped from YANG variable /string_container/string_default_leaf (string)
    """
    return self.__string_default_leaf
      
  def _set_string_default_leaf(self,v):
    """
      Setter method for string_default_leaf, mapped from YANG variable /string_container/string_default_leaf (string)
      If this variable is read-only (config: false) in the
      source YANG file, then _set_string_default_leaf is considered as a private
      method. Backends looking to populate this variable should
      do so via calling thisObj._set_string_default_leaf() directly.
    """
    #print v
    #t = defineYANGDynClass(v,base=RestrictedClassType(base_type=int, restriction_type="range", restriction_arg="0..63"))
    #print t
    try:
      t = defineYANGDynClass(v,base=RestrictedClassType(base_type=int, restriction_type="range", restriction_arg="0..63"))
    except (TypeError, ValueError):
      raise TypeError("string_default_leaf must be of a type compatible with str")
    self.__string_default_leaf = t
    self.set()

  string_leaf = property(_get_string_leaf, _set_string_leaf)
  string_default_leaf = property(_get_string_default_leaf, _set_string_default_leaf)


  __elements = {'string_leaf': string_leaf, 'string_default_leaf': string_default_leaf, }


  def elements(self):
    return self.__elements

  def __str__(self):
    return str(self.elements())

  def get(self, filter=False):
    def error():
      return NameError, "element does not exist"
    d = {}
    for i in self.__elements.keys():
      f = getattr(self, i, error)
      if hasattr(f, "get"):
        d[i] = f.get()
        if filter == True and not f.changed():
          del d[i]
      else:
        if filter == False and not f.changed():
          if not f._default == None:
            d[i] = f._default
          else:
            d[i] = f
        elif f.changed():
          d[i] = f
        else:
          # changed = False, and filter = True
          pass
    return d
  

class string(object):
  """
     This class was auto-generated by the PythonClass plugin for PYANG
     from YANG module string - based on the path /.
     Each member element of the container is represented as a class
     variable - with a specific YANG type.
    """
  __slots__ = ('__string_container',)

  __string_container = defineYANGDynClass(base=yc_string_container__string_container, )

  def _get_string_container(self):
    """
      Getter method for string_container, mapped from YANG variable /string_container (container)
    """
    return self.__string_container
      
  def _set_string_container(self,v):
    """
      Setter method for string_container, mapped from YANG variable /string_container (container)
      If this variable is read-only (config: false) in the
      source YANG file, then _set_string_container is considered as a private
      method. Backends looking to populate this variable should
      do so via calling thisObj._set_string_container() directly.
    """
    try:
      t = defineYANGDynClass(v,base=yc_string_container__string_container)
    except (TypeError, ValueError):
      raise TypeError("string_container must be of a type compatible with yc_string_container__string_container")
    self.__string_container = t
    self.set()

  string_container = property(_get_string_container, _set_string_container)


  __elements = {'string_container': string_container, }


  def elements(self):
    return self.__elements

  def __str__(self):
    return str(self.elements())

  def get(self, filter=False):
    def error():
      return NameError, "element does not exist"
    d = {}
    for i in self.__elements.keys():
      f = getattr(self, i, error)
      if hasattr(f, "get"):
        d[i] = f.get()
        if filter == True and not f.changed():
          del d[i]
      else:
        if filter == False and not f.changed():
          if not f._default == None:
            d[i] = f._default
          else:
            d[i] = f
        elif f.changed():
          d[i] = f
        else:
          # changed = False, and filter = True
          pass
    return d
  

#RestrictedClassType  
integerdefault = defineYANGDynClass(base=RestrictedClassType(base_type=np.uint16, restriction_type="range",restriction_arg="0..64"), default=np.uint16("10"))

import sys
sys.exit(127)

s = string()
print dir(s)
print s.string_container.string_leaf
print s.string_container.string_leaf._default
print 'setting to valid value'
s.string_container.string_leaf = "aardwolf"
print 'setting to invalid value'
succeed = False
try:
  s.string_container.string_leaf = "badger"
  succeed = True
except:
  pass
if succeed:
  raise ValueError, "set wrong value"

q = False
try:
  s.string_container.string_default_leaf = "hello"
  q = True
except:
  pass
if q:
  raise ValueError, "set wrong value"
s.string_container.string_default_leaf = 1
for i in range(1,65):
  s.string_container.string_default_leaf += 1
  print "%d, %d" % (i, s.string_container.string_default_leaf)


