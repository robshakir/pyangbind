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
          self._members[k] = defineYANGDynClass(v, base=self._contained_class)
        except TypeError, m:
          raise ValueError, "key value must be valid, %s" % m
      else:
        raise ValueError, "value must be set to an instance of %s" % (self._contained_class)


    def __delitem__(self, k):
      del self._members[k]

    def __len__(self): return len(self._members)

    def add(self, k):
      if k in self._members.keys():
        raise IndexError, "%s already contains a key with value %s" % (self, k)
      try:
        self._members[k] = defineYANGDynClass(base=self._contained_class)
        setattr(self._members[k], self._keyval, k)
      except TypeError, m:
        del self._members[k]
        raise ValueError, "key value must be valid, %s" % m

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
    _parent = None

    def yang_set(self):
      return self._changed

    def __setitem__(self, *args, **kwargs):
      self._changed = True
      super(YANGDynClass, self).__setitem__(*args, **kwargs)

    def append(self, *args, **kwargs):
      if not hasattr(super(YANGDynClass,self), "append"):
        raise AttributeError("%s object has no attribute append" % base_type)
      self._changed = True
      super(YANGDynClass, self).append(*args,**kwargs)

    def pop(self, *args, **kwargs):
      if not hasattr(super(YANGDynClass, self), "pop"):
        raise AttributeError("%s object has no attribute pop" % base_type)
      self._changed = True
      super(YANGDynClass, self).pop(*args, **kwargs)

    def remove(self, *args, **kwargs):
      if not hasattr(super(YANGDynClass, self), "remove"):
        raise AttributeError("%s object has no attribute remove" % base_type)
      self._changed = True
      super(YANGDynClass, self).remove(*args, **kwargs)

    def extend(self, *args, **kwargs):
      if not hasattr(super(YANGDynClass, self), "extend"):
        raise AttributeError("%s object has no attribute extend" % base_type)
      self._changed = True
      super(YANGDynClass, self).extend(*args, **kwargs)

    def insert(self, *args, **kwargs):
      if not hasattr(super(YANGDynClass,self), "insert"):
        raise AttributeError("%s object has no attribute insert" % base_type)
      self._changed = True
      super(YANGDynClass, self).insert(*args, **kwargs)

    def __repr__(self, *args, **kwargs):
      if self._default and not self._changed:
        return repr(self._default)
      else:
        return super(YANGDynClass, self).__repr__()

    def __init__(self, *args, **kwargs):
      pass

    def __new__(self, *args, **kwargs):
      default = kwargs.pop("default", None)
      self._parent = kwargs.pop("parent", None)
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
          obj._changed = True
      else:
        # there is a default - if the value is not the same as that default
        # then we have changed the object.
        if value == None:
          # if the value is none, then we have not changed it
          obj._changed = False
        elif not value == default:
          obj._changed = True
        else:
          obj._changed = False

      obj._default = default
      return obj

  return YANGDynClass(*args,**kwargs)
class yc_list_element__list_container_list_element(object):
  """
     This class was auto-generated by the PythonClass plugin for PYANG
     from YANG module list - based on the path /list-container/list-element.
     Each member element of the container is represented as a class
     variable - with a specific YANG type.
    """
  __keyval = defineYANGDynClass(base=np.uint8)
  __another_value = defineYANGDynClass(base=str, default="defaultValue")

  def _get_keyval(self):
    """
      Getter method for keyval, mapped from YANG variable /list_container/list_element/keyval (uint8)
    """
    return self.__keyval
      
  def _set_keyval(self,v):
    """
      Setter method for keyval, mapped from YANG variable /list_container/list_element/keyval (uint8)
      If this variable is read-only (config: false) in the
      source YANG file, then _set_keyval is considered as a private
      method. Backends looking to populate this variable should
      do so via calling thisObj._set_keyval() directly.
    """
    try:
      t = defineYANGDynClass(v,base=np.uint8)
    except (TypeError, ValueError):
      raise TypeError("keyval must be of a type compatible with np.uint8")
    self.__keyval = t

  def _get_another_value(self):
    """
      Getter method for another_value, mapped from YANG variable /list_container/list_element/another_value (string)
    """
    return self.__another_value
      
  def _set_another_value(self,v):
    """
      Setter method for another_value, mapped from YANG variable /list_container/list_element/another_value (string)
      If this variable is read-only (config: false) in the
      source YANG file, then _set_another_value is considered as a private
      method. Backends looking to populate this variable should
      do so via calling thisObj._set_another_value() directly.
    """
    try:
      t = defineYANGDynClass(v,base=str)
    except (TypeError, ValueError):
      raise TypeError("another_value must be of a type compatible with str")
    self.__another_value = t

  keyval = property(_get_keyval, _set_keyval)
  another_value = property(_get_another_value, _set_another_value)

class yc_list_container__list_container(object):
  """
     This class was auto-generated by the PythonClass plugin for PYANG
     from YANG module list - based on the path /list-container.
     Each member element of the container is represented as a class
     variable - with a specific YANG type.
    """
  __list_element = defineYANGDynClass(base=YANGListType("keyval",yc_list_element__list_container_list_element))
  def _get_list_element(self):
    """
      Getter method for list_element, mapped from YANG variable /list_container/list_element (list)
    """
    return self.__list_element
      
  def _set_list_element(self,v):
    """
      Setter method for list_element, mapped from YANG variable /list_container/list_element (list)
      If this variable is read-only (config: false) in the
      source YANG file, then _set_list_element is considered as a private
      method. Backends looking to populate this variable should
      do so via calling thisObj._set_list_element() directly.
    """
    try:
      t = defineYANGDynClass(v,base=yc_list_element__list_container_list_element)
    except (TypeError, ValueError):
      raise TypeError("list_element must be of a type compatible with yc_list_element__list_container_list_element")
    self.__list_element = t

  list_element = property(_get_list_element, _set_list_element)

class list_(object):
  """
     This class was auto-generated by the PythonClass plugin for PYANG
     from YANG module list - based on the path /.
     Each member element of the container is represented as a class
     variable - with a specific YANG type.
    """
  def __init__(self, *args, **kwargs):
    self.__list_container = defineYANGDynClass(base=yc_list_container__list_container,parent=self)
    object.__init__(self)

  def _get_list_container(self):
    """
      Getter method for list_container, mapped from YANG variable /list_container (container)
    """
    return self.__list_container
      
  def _set_list_container(self,v):
    """
      Setter method for list_container, mapped from YANG variable /list_container (container)
      If this variable is read-only (config: false) in the
      source YANG file, then _set_list_container is considered as a private
      method. Backends looking to populate this variable should
      do so via calling thisObj._set_list_container() directly.
    """
    try:
      t = defineYANGDynClass(v,base=yc_list_container__list_container)
    except (TypeError, ValueError):
      raise TypeError("list_container must be of a type compatible with yc_list_container__list_container")
    self.__list_container = t

  list_container = property(_get_list_container, _set_list_container)

