from operator import attrgetter
import numpy as np
from decimal import Decimal
import collections, re

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

    def __init__(self, *args, **kwargs):
      self._keyval = keyname
      if not type(listclass) == type(int):
        raise ValueError, "contained class of a YANGList must be a class"
      self._contained_class = listclass

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

    def __iter__(self):
      return iter(self._members.keys())

    def __contains__(self,k):
      if k in self._members.keys():
        return True
      return False

    def __getitem__(self, k):
      return self._members[k]

    def __setitem__(self, k, v):
      if self.__check__(v):
        try:
          self._members[k] = YANGDynClass(v,base=self._contained_class)
        except TypeError, m:
          raise ValueError, "key value must be valid, %s" % m
      else:
        raise ValueError, "value must be set to an instance of %s" %           (self._contained_class)

    def __delitem__(self, k):
      del self._members[k]

    def __len__(self): return len(self._members)

    def add(self, k):
      try:
        self._members[k] = YANGDynClass(base=self._contained_class)
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
class yc_global___juniper_config_bgp_global(object):
  """
     This class was auto-generated by the PythonClass plugin for PYANG
     from YANG module openconfig-bgp-juniper - based on the path /juniper-config/bgp/global. Each member element of
     the container is represented as a class variable - with a specific 
     YANG type.

     YANG Description: Global options
    """
  __slots__ = ('__as_',)


  def __init__(self, *args, **kwargs):
    self.__as_ = YANGDynClass(base=str, )

  def _get_as_(self):
    """
      Getter method for as_, mapped from YANG variable /juniper_config/bgp/global/as (string)

      YANG Description: Autonomous system number
    """
    return self.__as_
      
  def _set_as_(self,v):
    """
      Setter method for as_, mapped from YANG variable /juniper_config/bgp/global/as (string)
      If this variable is read-only (config: false) in the
      source YANG file, then _set_as_ is considered as a private
      method. Backends looking to populate this variable should
      do so via calling thisObj._set_as_() directly.

      YANG Description: Autonomous system number
    """
    try:
      t = YANGDynClass(v,base=str)
    except (TypeError, ValueError):
      raise TypeError("""as_ must be of a type compatible with str""")
    self.__as_ = t
    self.set()

  as_ = property(_get_as_, _set_as_)


  __elements = {'as_': as_, }


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
  

class yc_neighbor__juniper_config_bgp_peer_group_neighbor(object):
  """
     This class was auto-generated by the PythonClass plugin for PYANG
     from YANG module openconfig-bgp-juniper - based on the path /juniper-config/bgp/peer-group/neighbor. Each member element of
     the container is represented as a class variable - with a specific 
     YANG type.

     YANG Description: Neighbor configuration
    """
  __slots__ = ('__neighbor_name','__peer_as',)


  def __init__(self, *args, **kwargs):
    self.__neighbor_name = YANGDynClass(base=str, )
    self.__peer_as = YANGDynClass(base=str, )

  def _get_neighbor_name(self):
    """
      Getter method for neighbor_name, mapped from YANG variable /juniper_config/bgp/peer_group/neighbor/neighbor_name (string)

      YANG Description: Neighbor name
    """
    return self.__neighbor_name
      
  def _set_neighbor_name(self,v):
    """
      Setter method for neighbor_name, mapped from YANG variable /juniper_config/bgp/peer_group/neighbor/neighbor_name (string)
      If this variable is read-only (config: false) in the
      source YANG file, then _set_neighbor_name is considered as a private
      method. Backends looking to populate this variable should
      do so via calling thisObj._set_neighbor_name() directly.

      YANG Description: Neighbor name
    """
    try:
      t = YANGDynClass(v,base=str)
    except (TypeError, ValueError):
      raise TypeError("""neighbor_name must be of a type compatible with str""")
    self.__neighbor_name = t
    self.set()

  def _get_peer_as(self):
    """
      Getter method for peer_as, mapped from YANG variable /juniper_config/bgp/peer_group/neighbor/peer_as (string)

      YANG Description: Neighbor autonomous system number
    """
    return self.__peer_as
      
  def _set_peer_as(self,v):
    """
      Setter method for peer_as, mapped from YANG variable /juniper_config/bgp/peer_group/neighbor/peer_as (string)
      If this variable is read-only (config: false) in the
      source YANG file, then _set_peer_as is considered as a private
      method. Backends looking to populate this variable should
      do so via calling thisObj._set_peer_as() directly.

      YANG Description: Neighbor autonomous system number
    """
    try:
      t = YANGDynClass(v,base=str)
    except (TypeError, ValueError):
      raise TypeError("""peer_as must be of a type compatible with str""")
    self.__peer_as = t
    self.set()

  neighbor_name = property(_get_neighbor_name, _set_neighbor_name)
  peer_as = property(_get_peer_as, _set_peer_as)


  __elements = {'neighbor_name': neighbor_name, 'peer_as': peer_as, }


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
  

class yc_peer_group__juniper_config_bgp_peer_group(object):
  """
     This class was auto-generated by the PythonClass plugin for PYANG
     from YANG module openconfig-bgp-juniper - based on the path /juniper-config/bgp/peer-group. Each member element of
     the container is represented as a class variable - with a specific 
     YANG type.

     YANG Description: List of peer groups
    """
  __slots__ = ('__group_name','__peer_type','__neighbor',)


  def __init__(self, *args, **kwargs):
    self.__group_name = YANGDynClass(base=str, )
    self.__peer_type = YANGDynClass(base=RestrictedClassType(base_type=str, restriction_type="dict_key",                 restriction_arg={'internal': {}, 'external': {}},), )
    self.__neighbor = YANGDynClass(base=YANGListType("neighbor_name",yc_neighbor__juniper_config_bgp_peer_group_neighbor), )

  def _get_group_name(self):
    """
      Getter method for group_name, mapped from YANG variable /juniper_config/bgp/peer_group/group_name (string)

      YANG Description: Peer group name
    """
    return self.__group_name
      
  def _set_group_name(self,v):
    """
      Setter method for group_name, mapped from YANG variable /juniper_config/bgp/peer_group/group_name (string)
      If this variable is read-only (config: false) in the
      source YANG file, then _set_group_name is considered as a private
      method. Backends looking to populate this variable should
      do so via calling thisObj._set_group_name() directly.

      YANG Description: Peer group name
    """
    try:
      t = YANGDynClass(v,base=str)
    except (TypeError, ValueError):
      raise TypeError("""group_name must be of a type compatible with str""")
    self.__group_name = t
    self.set()

  def _get_peer_type(self):
    """
      Getter method for peer_type, mapped from YANG variable /juniper_config/bgp/peer_group/peer_type (enumeration)

      YANG Description: Select type of the peer
    """
    return self.__peer_type
      
  def _set_peer_type(self,v):
    """
      Setter method for peer_type, mapped from YANG variable /juniper_config/bgp/peer_group/peer_type (enumeration)
      If this variable is read-only (config: false) in the
      source YANG file, then _set_peer_type is considered as a private
      method. Backends looking to populate this variable should
      do so via calling thisObj._set_peer_type() directly.

      YANG Description: Select type of the peer
    """
    try:
      t = YANGDynClass(v,base=RestrictedClassType(base_type=str, restriction_type="dict_key",                 restriction_arg={'internal': {}, 'external': {}},))
    except (TypeError, ValueError):
      raise TypeError("""peer_type must be of a type compatible with RestrictedClassType(base_type=str, restriction_type="dict_key",                 restriction_arg={'internal': {}, 'external': {}},)""")
    self.__peer_type = t
    self.set()

  def _get_neighbor(self):
    """
      Getter method for neighbor, mapped from YANG variable /juniper_config/bgp/peer_group/neighbor (list)

      YANG Description: Neighbor configuration
    """
    return self.__neighbor
      
  def _set_neighbor(self,v):
    """
      Setter method for neighbor, mapped from YANG variable /juniper_config/bgp/peer_group/neighbor (list)
      If this variable is read-only (config: false) in the
      source YANG file, then _set_neighbor is considered as a private
      method. Backends looking to populate this variable should
      do so via calling thisObj._set_neighbor() directly.

      YANG Description: Neighbor configuration
    """
    try:
      t = YANGDynClass(v,base=yc_neighbor__juniper_config_bgp_peer_group_neighbor)
    except (TypeError, ValueError):
      raise TypeError("""neighbor must be of a type compatible with yc_neighbor__juniper_config_bgp_peer_group_neighbor""")
    self.__neighbor = t
    self.set()

  group_name = property(_get_group_name, _set_group_name)
  peer_type = property(_get_peer_type, _set_peer_type)
  neighbor = property(_get_neighbor, _set_neighbor)


  __elements = {'group_name': group_name, 'peer_type': peer_type, 'neighbor': neighbor, }


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
  

class yc_bgp__juniper_config_bgp(object):
  """
     This class was auto-generated by the PythonClass plugin for PYANG
     from YANG module openconfig-bgp-juniper - based on the path /juniper-config/bgp. Each member element of
     the container is represented as a class variable - with a specific 
     YANG type.

     YANG Description: Openconfig BGP implementation
    """
  __slots__ = ('__global_','__peer_group',)


  def __init__(self, *args, **kwargs):
    self.__global_ = YANGDynClass(base=yc_global___juniper_config_bgp_global, )
    self.__peer_group = YANGDynClass(base=YANGListType("group_name",yc_peer_group__juniper_config_bgp_peer_group), )

  def _get_global_(self):
    """
      Getter method for global_, mapped from YANG variable /juniper_config/bgp/global (container)

      YANG Description: Global options
    """
    return self.__global_
      
  def _set_global_(self,v):
    """
      Setter method for global_, mapped from YANG variable /juniper_config/bgp/global (container)
      If this variable is read-only (config: false) in the
      source YANG file, then _set_global_ is considered as a private
      method. Backends looking to populate this variable should
      do so via calling thisObj._set_global_() directly.

      YANG Description: Global options
    """
    try:
      t = YANGDynClass(v,base=yc_global___juniper_config_bgp_global)
    except (TypeError, ValueError):
      raise TypeError("""global_ must be of a type compatible with yc_global___juniper_config_bgp_global""")
    self.__global_ = t
    self.set()

  def _get_peer_group(self):
    """
      Getter method for peer_group, mapped from YANG variable /juniper_config/bgp/peer_group (list)

      YANG Description: List of peer groups
    """
    return self.__peer_group
      
  def _set_peer_group(self,v):
    """
      Setter method for peer_group, mapped from YANG variable /juniper_config/bgp/peer_group (list)
      If this variable is read-only (config: false) in the
      source YANG file, then _set_peer_group is considered as a private
      method. Backends looking to populate this variable should
      do so via calling thisObj._set_peer_group() directly.

      YANG Description: List of peer groups
    """
    try:
      t = YANGDynClass(v,base=yc_peer_group__juniper_config_bgp_peer_group)
    except (TypeError, ValueError):
      raise TypeError("""peer_group must be of a type compatible with yc_peer_group__juniper_config_bgp_peer_group""")
    self.__peer_group = t
    self.set()

  global_ = property(_get_global_, _set_global_)
  peer_group = property(_get_peer_group, _set_peer_group)


  __elements = {'global_': global_, 'peer_group': peer_group, }


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
  

class yc_juniper_config__juniper_config(object):
  """
     This class was auto-generated by the PythonClass plugin for PYANG
     from YANG module openconfig-bgp-juniper - based on the path /juniper-config. Each member element of
     the container is represented as a class variable - with a specific 
     YANG type.
    """
  __slots__ = ('__bgp',)


  def __init__(self, *args, **kwargs):
    self.__bgp = YANGDynClass(base=yc_bgp__juniper_config_bgp, )

  def _get_bgp(self):
    """
      Getter method for bgp, mapped from YANG variable /juniper_config/bgp (container)

      YANG Description: Openconfig BGP implementation
    """
    return self.__bgp
      
  def _set_bgp(self,v):
    """
      Setter method for bgp, mapped from YANG variable /juniper_config/bgp (container)
      If this variable is read-only (config: false) in the
      source YANG file, then _set_bgp is considered as a private
      method. Backends looking to populate this variable should
      do so via calling thisObj._set_bgp() directly.

      YANG Description: Openconfig BGP implementation
    """
    try:
      t = YANGDynClass(v,base=yc_bgp__juniper_config_bgp)
    except (TypeError, ValueError):
      raise TypeError("""bgp must be of a type compatible with yc_bgp__juniper_config_bgp""")
    self.__bgp = t
    self.set()

  bgp = property(_get_bgp, _set_bgp)


  __elements = {'bgp': bgp, }


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
  

class openconfig_bgp_juniper(object):
  """
     This class was auto-generated by the PythonClass plugin for PYANG
     from YANG module openconfig-bgp-juniper - based on the path /. Each member element of
     the container is represented as a class variable - with a specific 
     YANG type.

     YANG Description: Example BGP.
    """
  __slots__ = ('__juniper_config',)


  def __init__(self, *args, **kwargs):
    self.__juniper_config = YANGDynClass(base=yc_juniper_config__juniper_config, )

  def _get_juniper_config(self):
    """
      Getter method for juniper_config, mapped from YANG variable /juniper_config (container)
    """
    return self.__juniper_config
      
  def _set_juniper_config(self,v):
    """
      Setter method for juniper_config, mapped from YANG variable /juniper_config (container)
      If this variable is read-only (config: false) in the
      source YANG file, then _set_juniper_config is considered as a private
      method. Backends looking to populate this variable should
      do so via calling thisObj._set_juniper_config() directly.
    """
    try:
      t = YANGDynClass(v,base=yc_juniper_config__juniper_config)
    except (TypeError, ValueError):
      raise TypeError("""juniper_config must be of a type compatible with yc_juniper_config__juniper_config""")
    self.__juniper_config = t
    self.set()

  juniper_config = property(_get_juniper_config, _set_juniper_config)


  __elements = {'juniper_config': juniper_config, }


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
  

