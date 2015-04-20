from operator import attrgetter
import numpy as np
from decimal import Decimal
import collections, re

def UnionType(*args, **kwargs):
  expected_types = kwargs.pop("expected_types", False)
  data_hint = kwargs.pop("data_hint", False)
  print data_hint
  if not expected_types or not type(expected_types) == type([]):
    raise AttributeError, "could not initialise union"
  print expected_types
  print args
  print "fish?"
  if not len(args) and not data_hint:
    print "returning without challenge"
    return expected_types[0]
  else:
    if len(args):
      a = args[0]
    else:
      a = data_hint
    print "using hint %s" % a
    for t in expected_types:
      try:
        return t(a)
      except ValueError:
        pass
    raise AttributeError, "specified argument did not match any union type"

def RestrictedPrecisionDecimalType(*args, **kwargs):
  """
    Function to return a new type that is based on decimal.Decimal with
    an arbitrary restricted precision.
  """
  precision = kwargs.pop("precision", False)
  class RestrictedPrecisionDecimal(Decimal):
    """
      Class extending decimal.Decimal to restrict the precision that is
      stored, supporting the fraction-digits argument of the YANG decimal64
      type.
    """
    _precision = 10.0**(-1.0*int(precision))
    def __new__(self, *args, **kwargs):
      """
        Overloads the decimal __new__ function in order to round the input
        value to the new value.
      """
      if not self._precision == None:
        if len(args):
          value = Decimal(args[0]).quantize(Decimal(str(self._precision)))
        else:
          value = Decimal(0)
      elif len(args):
        value = Decimal(args[0])
      else:
        value = Decimal(0)
      obj = Decimal.__new__(self, value, **kwargs)
      return obj
  return type(RestrictedPrecisionDecimal(*args, **kwargs))

def RestrictedClassType(*args, **kwargs):
  """
    Function to return a new type that restricts an arbitrary base_type with
    a specified restriction. The restriction_type specified determines the
    type of restriction placed on the class, and the restriction_arg gives
    any input data that this function needs.
  """
  base_type = kwargs.pop("base_type", str)
  restriction_type = kwargs.pop("restriction_type", None)
  restriction_arg = kwargs.pop("restriction_arg", None)

  class RestrictedClass(base_type):
    """
      A class that restricts the base_type class with a new function that the
      input value is validated against before being applied. The function is
      a static method which is assigned to _restricted_test.
    """
    _restriction_type = restriction_type
    _restriction_arg = restriction_arg
    _restriction_test = None

    def __init__(self, *args, **kwargs):
      """
        Overloads the base_class __init__ method to check the input argument
        against the validation function - returns on instance of the base_type
        class, which can be manipulated as per a usual Python object.
      """
      try:
        self.__check(args[0])
      except IndexError:
        pass
      super(RestrictedClass, self).__init__(*args, **kwargs)

    def __new__(self, *args, **kwargs):
      """
        Create a new class instance, and dynamically define the
        _restriction_test method so that it can be called by other functions.
      """
      if restriction_type == "pattern":
        p = re.compile(restriction_arg)
        self._restriction_test = p.match
        self._restriction_arg = restriction_arg
        self._restriction_type = restriction_type
      elif restriction_type == "range":
        x = [base_type(i) for i in           re.sub("(?P<low>[0-9]+)([ ]+)?\.\.([ ]+)?(?P<high>[0-9]+)", "\g<low>,\g<high>",            restriction_arg).split(",")]
        self._restriction_test = staticmethod(lambda i: i > x[0] and i < x[1])
        self._restriction_arg = restriction_arg
        self._restriction_type = restriction_type
      elif restriction_type == "dict_key":
        # populate enum values
        used_values = []
        for k in restriction_arg.keys():
          if "value" in restriction_arg[k].keys():
            used_values.append(int(restriction_arg[k]["value"]))
        c = 0
        for k in restriction_arg.keys():
          while c in used_values:
            c += 1
          if not "value" in restriction_arg[k].keys():
            restriction_arg[k]["value"] = c
          c += 1
        self._restriction_test = staticmethod(lambda i: i in restriction_arg.keys())
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
      """
        Run the _restriction_test static method against the argument v,
        returning an error if the value does not validate.
      """
      if self._restriction_type == "pattern":
        if not self._restriction_test(v):
          raise ValueError, "did not match restricted type"
        return True

    def getValue(self, *args, **kwargs):
      """
        For types where there is a dict_key restriction (such as YANG
        enumeration), return the value of the dictionary key.
      """
      if self._restriction_type == "dict_key":
        value = kwargs.pop("mapped", False)
        if value:
          return self._restriction_arg[self.__str__()]["value"]
      return self

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
        raise TypeError("Cannot add %s to TypedList (accepts only %s)" %           (v, self._allowed_type))

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
        raise ValueError, "value must be set to an instance of %s" %           (self._contained_class)

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
  def __new__(self, *args, **kwargs):
    false_args = ["false", "False", False, 0, "0"]
    true_args = ["true", "True", True, 1, "1"]
    if len(args):
      if not args[0] in false_args + true_args:
        raise ValueError, "%s is an invalid value for a YANGBool" % args[0]
      value = 0 if args[0] in false_args else 1
    else:
      value = 0
    return int.__new__(self, bool(value))

  def __repr__(self):
    return str([False, True][self])

  def __str__(self):
    return str(self.__repr__())

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

      print base_type
      print args
      print kwargs
      obj = base_type.__new__(self, *args, **kwargs)
      if default == None:
        base_type_default = True
        try:
          base_type_default = base_type()
        except:
          base_type_default = False

        if value == None:
          # there was no default, and the value was not set, or was
          # set to the default of the base type
          obj._changed = False
        elif base_type_default and value == base_type_default:
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
class yc_container__container(object):
  """
     This class was auto-generated by the PythonClass plugin for PYANG
     from YANG module union - based on the path /container. Each member element of
     the container is represented as a class variable - with a specific 
     YANG type.
    """
  __slots__ = ('__u4','__u1',)

  __u4 = defineYANGDynClass(base=UnionType(expected_types=[np.int8,str,]), default=str(1))
  __u1 = defineYANGDynClass(base=UnionType(expected_types=[str,np.int8,]))

  def _get_u4(self):
    """
      Getter method for u4, mapped from YANG variable /container/u4 (union)

      YANG Description: a test leaf that does not need to skip but is an int
    """
    return self.__u4
      
  def _set_u4(self,v):
    """
      Setter method for u4, mapped from YANG variable /container/u4 (union)
      If this variable is read-only (config: false) in the
      source YANG file, then _set_u4 is considered as a private
      method. Backends looking to populate this variable should
      do so via calling thisObj._set_u4() directly.

      YANG Description: a test leaf that does not need to skip but is an int
    """
    #try:
    t = defineYANGDynClass(v,base=UnionType(data_hint=v,expected_types=[np.int8,str,]),default=str(1),)
    #except (TypeError, ValueError):
    #  raise TypeError("""u4 must be of a type compatible with UnionType(expected_types=[np.int8,str,])""")
    self.__u4 = t
    self.set()

  def _get_u1(self):
    """
      Getter method for u1, mapped from YANG variable /container/u1 (union)

      YANG Description: A test leaf
    """
    return self.__u1
      
  def _set_u1(self,v):
    """
      Setter method for u1, mapped from YANG variable /container/u1 (union)
      If this variable is read-only (config: false) in the
      source YANG file, then _set_u1 is considered as a private
      method. Backends looking to populate this variable should
      do so via calling thisObj._set_u1() directly.

      YANG Description: A test leaf
    """
    try:
      t = defineYANGDynClass(v,base=UnionType(expected_types=[str,np.int8,]))
    except (TypeError, ValueError):
      raise TypeError("""u1 must be of a type compatible with UnionType(expected_types=[str,np.int8,])""")
    self.__u1 = t
    self.set()

  u4 = property(_get_u4, _set_u4)
  u1 = property(_get_u1, _set_u1)


  __elements = {'u4': u4, 'u1': u1, }


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
  

class union(object):
  """
     This class was auto-generated by the PythonClass plugin for PYANG
     from YANG module union - based on the path /. Each member element of
     the container is represented as a class variable - with a specific 
     YANG type.

     YANG Description: A test module
    """
  __slots__ = ('__container',)

  __container = defineYANGDynClass(base=yc_container__container, )

  def _get_container(self):
    """
      Getter method for container, mapped from YANG variable /container (container)
    """
    return self.__container
      
  def _set_container(self,v):
    """
      Setter method for container, mapped from YANG variable /container (container)
      If this variable is read-only (config: false) in the
      source YANG file, then _set_container is considered as a private
      method. Backends looking to populate this variable should
      do so via calling thisObj._set_container() directly.
    """
    try:
      t = defineYANGDynClass(v,base=yc_container__container)
    except (TypeError, ValueError):
      raise TypeError("""container must be of a type compatible with yc_container__container""")
    self.__container = t
    self.set()

  container = property(_get_container, _set_container)


  __elements = {'container': container, }


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
  

