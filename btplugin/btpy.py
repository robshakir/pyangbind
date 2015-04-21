"""Generate YANG Python Bindings from a YANG model.

(c) Rob Shakir (rob.shakir@bt.com, rjs@rob.sh) - 2015.

This module is tentatively licensed under the Apache licence.

"""

import optparse
import sys
import re
import string
import numpy as np
import decimal
import copy

from pyang import plugin
from pyang import statements

USED_TYPES = []

DEBUG = True

if DEBUG:
  import pprint
  pp = pprint.PrettyPrinter(indent=2)

# TODO, move this to a header file
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


reserved_name = ["list", "str", "int", "global", "decimal", "float", "as"]

class_bool_map = {
  'false':  False,
  'False':  False,
  'true':    True,
  'True':    True,
}

class_map = {
  'boolean':          {"native_type": "YANGBool", "map": class_bool_map, "base_type": True, "quote_arg": True, "pytype": YANGBool},
  'uint8':            {"native_type": "np.uint8", "base_type": True, "pytype": np.uint8},
  'uint16':           {"native_type": "np.uint16", "base_type": True, "pytype": np.uint16},
  'uint32':           {"native_type": "np.uint32", "base_type": True, "pytype": np.uint32},
  'uint64':           {"native_type": "np.uint64", "base_type": True, "pytype": np.uint64},
  'string':           {"native_type": "str", "base_type": True, "quote_arg": True, "pytype": str},
  'decimal64':        {"native_type": "Decimal", "base_type": True, "pytype": decimal.Decimal},
  'empty':            {"native_type": "YANGBool", "map": class_bool_map, "base_type": True, "quote_arg": True, "pytype": YANGBool},
  'int8':             {"native_type": "np.int8", "base_type": True, "pytype": np.int8},
  'int16':            {"native_type": "np.int16", "base_type": True, "pytype": np.int16},
  'int32':            {"native_type": "np.int32", "base_type": True, "pytype": np.int32},
  'int64':            {"native_type": "np.int64", "base_type": True, "pytype": np.int64},
  # we need to look at how to parse typedefs
  #'inet:as-number':     ("int", False),
  #'inet:ipv4-address':   ("str", False),
  #'decimal64':       ("float", False),
  # more types to be added here
}

# all types that support range substmts
INT_RANGE_TYPES = ["uint8", "uint16", "uint32", "uint64", "int8", "int16", "int32", "int64"]

def safe_name(arg):
  """
    Make a leaf or container name safe for use in Python.
  """
  arg = arg.replace("-", "_")
  if arg in reserved_name:
    arg += "_"
  return arg

def pyang_plugin_init():
    plugin.register_plugin(BTPyClass())

class BTPyClass(plugin.PyangPlugin):
    def add_output_format(self, fmts):
        self.multiple_modules = True
        fmts['bt'] = self

    def emit(self, ctx, modules, fd):
        build_btclass(ctx, modules, fd)


def build_btclass(ctx, modules, fd):
  # numpy provides some elements of the classes datatypes
  fd.write("from operator import attrgetter\n")
  fd.write("import numpy as np\n")
  fd.write("from decimal import Decimal\n")

  fd.write("""import collections, re

def RestrictedPrecisionDecimalType(*args, **kwargs):
  \"\"\"
    Function to return a new type that is based on decimal.Decimal with
    an arbitrary restricted precision.
  \"\"\"
  precision = kwargs.pop("precision", False)
  class RestrictedPrecisionDecimal(Decimal):
    \"\"\"
      Class extending decimal.Decimal to restrict the precision that is
      stored, supporting the fraction-digits argument of the YANG decimal64
      type.
    \"\"\"
    _precision = 10.0**(-1.0*int(precision))
    def __new__(self, *args, **kwargs):
      \"\"\"
        Overloads the decimal __new__ function in order to round the input
        value to the new value.
      \"\"\"
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
  \"\"\"
    Function to return a new type that restricts an arbitrary base_type with
    a specified restriction. The restriction_type specified determines the
    type of restriction placed on the class, and the restriction_arg gives
    any input data that this function needs.
  \"\"\"
  base_type = kwargs.pop("base_type", str)
  restriction_type = kwargs.pop("restriction_type", None)
  restriction_arg = kwargs.pop("restriction_arg", None)

  class RestrictedClass(base_type):
    \"\"\"
      A class that restricts the base_type class with a new function that the
      input value is validated against before being applied. The function is
      a static method which is assigned to _restricted_test.
    \"\"\"
    _restriction_type = restriction_type
    _restriction_arg = restriction_arg
    _restriction_test = None

    def __init__(self, *args, **kwargs):
      \"\"\"
        Overloads the base_class __init__ method to check the input argument
        against the validation function - returns on instance of the base_type
        class, which can be manipulated as per a usual Python object.
      \"\"\"
      try:
        self.__check(args[0])
      except IndexError:
        pass
      super(RestrictedClass, self).__init__(*args, **kwargs)

    def __new__(self, *args, **kwargs):
      \"\"\"
        Create a new class instance, and dynamically define the
        _restriction_test method so that it can be called by other functions.
      \"\"\"
      if restriction_type == "pattern":
        p = re.compile(restriction_arg)
        self._restriction_test = p.match
        self._restriction_arg = restriction_arg
        self._restriction_type = restriction_type
      elif restriction_type == "range":
        x = [base_type(i) for i in \
          re.sub("(?P<low>[0-9]+)([ ]+)?\.\.([ ]+)?(?P<high>[0-9]+)", "\g<low>,\g<high>", \
           restriction_arg).split(",")]
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
      \"\"\"
        Run the _restriction_test static method against the argument v,
        returning an error if the value does not validate.
      \"\"\"
      if self._restriction_type == "pattern":
        if not self._restriction_test(v):
          raise ValueError, "did not match restricted type"
        return True

    def getValue(self, *args, **kwargs):
      \"\"\"
        For types where there is a dict_key restriction (such as YANG
        enumeration), return the value of the dictionary key.
      \"\"\"
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
        raise TypeError("Cannot add %s to TypedList (accepts only %s)" % \
          (v, self._allowed_type))

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
        raise ValueError, "value must be set to an instance of %s" % \
          (self._contained_class)

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
  if type(base_type) == type([]):
    # this is a union, we need to infer type
    if not len(args):
      # we don't have an argument, so we just return the first
      # type that was specified
      base_type = base_type[0]
    else:
      type_test = False
      for t in base_type:
        try:
          type_test = t(args[0])
          break
        except:
          pass
      if not type_test:
        raise TypeError, "did not find a valid type using hint"
      base_type = t
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
""")

  r_typedefs = {}
  for module in modules:
    #typedefs = get_typedefs(ctx, module)
    mods = module.search('import')
    # we have to do this module last, since it may
    # have typedef dependencies elsewhere
    mods.append(module)
    for i in mods:
      prefix = i.search_one('prefix').arg
      if i == module:
        prefix = False
      if not get_typedefs(ctx, i, prefix=prefix):
        raise TypeError, "Invalid specification of typedefs"

  # build infrastructure, a tree of classes


  #pp.pprint(class_map)
  #assert False, "TODO"
  # we need to parse each module
  for module in modules:
    # we need to parse each sub-module
    mods = [module]
    for i in module.search('include'):
      subm = ctx.get_module(i.arg)
      if subm is not None:
        mods.append(subm)

    for m in mods:
      children = [ch for ch in module.i_children
            if ch.keyword in statements.data_definition_keywords]
      get_children(fd, children, m, m)

def get_typedefs(ctx, module, prefix=False):
  r_typedefs = {}
  mod = ctx.get_module(module.arg)
  print "%s!" % module.arg
  if mod == None:
    raise AttributeError, "unmapped types, please specify path to %s!" % (module.arg)
  typedefs = mod.search('typedef')
  restricted_arg = False
  default = False

  # we need to check whether there are any dependencies between
  # the typedefs that we have within the module.
  process_typedefs_ordered = []
  known_typedefs = class_map.keys()
  remaining_typedefs = []
  definition_dict = {}
  for i in typedefs:
    if not i.arg == "%s:%s" % (prefix, i.arg) and prefix:
      name = "%s:%s" % (prefix, i.arg)
    else:
      name = i.arg
    definition_dict[name] = i
    remaining_typedefs.append(name)

  #remaining_typedefs = typedefs

  print "starting processing typedef for %s..." % (module.arg)
  # for each remaining typedef definition that we
  # do not know about - retrieve the definition
  # check whether it references a type that we now
  # know about, and if not, re-queue it. if so
  # add it to the queue
  while remaining_typedefs:
    i_name = remaining_typedefs.pop(0)
    item = definition_dict[i_name]

    print "processing item %s..." % i_name
    this_type = item.search_one('type').arg
    if this_type == "union":
      subtypes = [i.arg for i in item.search_one('type').search('type')]
    else:
      subtypes = [this_type,]
    print " subtypes...%s" % subtypes
    any_unknown = False
    for i in subtypes:
      if not i in known_typedefs:
        any_unknown = True
    if not any_unknown:
      process_typedefs_ordered.append(item)
      known_typedefs.append(i_name)
    else:
      if not name in remaining_typedefs:
         remaining_typedefs.append(i_name)

  for item in process_typedefs_ordered:
    print "building %s..." % item.arg
    mapped_type = False
    restricted_arg = False
    cls,elemtype = copy.deepcopy(build_elemtype(item.search_one('type')))
    #pp.pprint(elemtype)
    type_name = "%s%s" % ("%s:" % prefix if prefix else "", item.arg)
    if type_name in class_map.keys():
      raise TypeError, "Duplicate definition of %s" % type_name
    default_stmt = item.search_one('default')
    #pp.pprint(elemtype)
    if not type(elemtype) == type(list()):
      restricted = False
      class_map[type_name] = {"native_type": elemtype["native_type"], "base_type": False,}
      if "parent_type" in elemtype.keys():
        class_map[type_name]["parent_type"] = elemtype["parent_type"]
      else:
        yang_type = item.search_one('type').arg
        if not yang_type in class_map.keys():
          raise TypeError, "typedef specified a native type that was not supported"
        class_map[type_name]["parent_type"] = yang_type
      if not default_stmt == None:
        class_map[type_name]["default"] = default_stmt.arg
      if "restriction_type" in elemtype.keys():
        #print elemtype
        class_map[type_name]["restriction_type"] = elemtype["restriction_type"]
        class_map[type_name]["restriction_argument"] = elemtype["restriction_argument"]
      if "quote_arg" in elemtype.keys():
        class_map[type_name]["quote_arg"] = elemtype["quote_arg"]
    else:
      native_type = []
      parent_type = []
      default = False if default_stmt == None else default_stmt.arg
      for i in elemtype:
        # CHANGE - 13:30
        #print i
        native_type.append(i[1]["native_type"])
        #if "parent_type" in i[1].keys():
        #  parent_type.append(i[1]["parent_type"])
        #else:
        if i[1]["yang_type"] in class_map.keys():
          parent_type.append(i[1]["yang_type"])
        else:
          raise TypeError, "typedef in a union specified a native type that was not supported"
        if "default" in i[1].keys() and not default:
          # we do strict ordering, so only the first default wins
          q = True if "quote_arg" in i[1].keys() else False
          default = (i[1]["default"], q)
      class_map[type_name] = {"native_type": native_type, "base_type": False,
                              "parent_type": parent_type,}
      if default:
        class_map[type_name]["default"] = default[0]
        class_map[type_name]["quote_default"] = default[1]

  return True

def get_children(fd, i_children, module, parent, path=str()):
  used_types,elements = [],[]
  for ch in i_children:
    elements += get_element(fd, ch, module, parent, path+"/"+ch.arg)

  if parent.keyword in ["container", "module", "list"]:
    if not path == "":
      fd.write("class yc_%s_%s(object):\n" % (safe_name(parent.arg), \
        safe_name(path.replace("/", "_"))))
    else:
      fd.write("class %s(object):\n" % safe_name(parent.arg))

    parent_descr = parent.search_one('description')
    if not parent_descr == None:
      parent_descr = "\n\n     YANG Description: %s" % parent_descr.arg
    else:
      parent_descr = ""

    fd.write("""  \"\"\"
     This class was auto-generated by the PythonClass plugin for PYANG
     from YANG module %s - based on the path %s. Each member element of
     the container is represented as a class variable - with a specific 
     YANG type.%s
    \"\"\"\n"""  % (module.arg, (path if not path == "" else "/"), parent_descr))
  else:
    raise TypeError, "unhandled keyword with children %s" % parent.keyword

  e_str = ""
  if len(elements) == 0:
    fd.write("  pass\n")
  else:
    # we want to prevent a user from creating new attributes on a class that
    # are not allowed within the data model
    e_str = "__elements = {"
    slots_str = "  __slots__ = ("
    for i in elements:
      slots_str += "'__%s'," % i["name"]
      e_str +=  "'%s': %s, " % (i["name"], i["name"])
    slots_str += ")\n"
    e_str += "}\n"
    fd.write(slots_str)
    fd.write("\n")
    for i in elements:
      #rint "looping elements"
      if "default" in i.keys() and not i["default"] == None:
        default_arg = "\"%s\"" % i["default"] if i["quote_arg"] else "%s" % i["default"]

      if i["class"] == "leaf-list":
        class_str = "  __%s" % (i["name"])
        class_str += " = defineYANGDynClass(base="
        class_str += "%s(allowed_type=%s), " % i["type"]["native_type"]
        if "default" in i.keys() and not i["default"] == None:
          class_str += "default=%s(%s)" % (i["defaulttype"], default_arg)
        class_str += ")\n"
      elif i["class"] == "list":
        class_str = "  __%s" % (i["name"])
        class_str += " = defineYANGDynClass(base=YANGListType("
        class_str += "\"%s\",yc_%s_%s), " % (i["key"], safe_name(i["name"]), \
                        safe_name(path.replace("/","_"))+"_"+safe_name(i["name"]))
        class_str += ")\n"
      elif i["class"] == "union":
        class_str = "  __%s" % (i["name"])
        class_str += " = defineYANGDynClass(base=["
        for u in i["type"][1]:
          class_str += "%s," % u[1]["native_type"]
        class_str += "]"
        if "default" in i.keys() and not i["default"] == None:
          class_str += ", default=%s(%s)" % (i["defaulttype"], default_arg)
        class_str += ")\n"
      elif i["class"] == "leaf-union":
        class_str = "  __%s" % (i["name"])
        class_str += " = defineYANGDynClass(base=["
        for u in i["type"]:
          class_str += "%s," % u
        class_str += "]"
        if "default" in i.keys() and not i["default"] == None:
          class_str += ", default=%s(%s)" % (i["defaulttype"], default_arg)
        class_str += ")\n"
      else:
        class_str = "  __%s" % (i["name"])
        class_str += " = defineYANGDynClass("
        class_str += "base=%s, " % i["type"]
        if "default" in i.keys() and not i["default"] == None:
          class_str += "default=%s(%s)" % (i["defaulttype"], default_arg)
        class_str += ")\n"
      fd.write(class_str)

    node = {}
    for i in elements:
      description_str = ""
      if i["description"]:
        description_str = "\n\n      YANG Description: %s" % i["description"]
      fd.write("""
  def _get_%s(self):
    \"\"\"
      Getter method for %s, mapped from YANG variable %s (%s)%s
    \"\"\"
    return self.__%s
      """ % (i["name"], i["name"], i["path"], i["origtype"],
             description_str, i["name"]))

      if i["class"] == "leaf-list":
        native_type = i["type"]["native_type"]
      elif i["class"] == "union":
        native_type = "["
        for u in i["type"][1]:
          native_type += "%s," % u[1]["native_type"]
        native_type += "]"
      elif i["class"] == "leaf-union":
        native_type = "["
        for u in i["type"]:
          native_type += "%s," % u
        native_type += "]"
      else:
        native_type = i["type"]

      if "default" in i.keys() and not i["default"] == None:
        if i["quote_arg"]:
          default_arg = "\"%s\"" % i["default"]
        else:
          default_arg = i["default"]
        if not i["class"] == "union":
          default_s = ",default=%s(%s)," % (i["defaulttype"], default_arg)
        else:
          default_s = ",default=%s(%s)," % (i["defaulttype"], default_arg)
      else:
        default_s = ""
      fd.write("""
  def _set_%s(self,v):
    \"\"\"
      Setter method for %s, mapped from YANG variable %s (%s)
      If this variable is read-only (config: false) in the
      source YANG file, then _set_%s is considered as a private
      method. Backends looking to populate this variable should
      do so via calling thisObj._set_%s() directly.%s
    \"\"\"
    try:
      t = defineYANGDynClass(v,base=%s%s)
    except (TypeError, ValueError):
      raise TypeError(\"\"\"%s must be of a type compatible with %s\"\"\")
    self.__%s = t\n""" % (i["name"], i["name"], i["path"],
                          i["origtype"], i["name"], i["name"], description_str, \
                          native_type, default_s, i["name"], native_type, i["name"]))
      fd.write("    self.set()\n")
    fd.write("\n")
    for i in elements:
      if i["config"]:
        fd.write("""  %s = property(_get_%s, _set_%s)\n""" % \
                          (i["name"], i["name"], i["name"]))
      else:
        fd.write("""  %s = property(_get_%s)\n""" % (i["name"], i["name"]))
  fd.write("""

  %s

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
  \n""" % e_str)
  fd.write("\n")
  return True

def build_elemtype(et):
  cls = "leaf"
  #et = element.search_one('type')
  restricted = False

  if et.arg == "string":
    pattern = et.search_one('pattern')
    if not pattern == None:
      cls = "restricted-string"
      elemtype = {"native_type": """RestrictedClassType(base_type=%s, restriction_type="pattern",
                      restriction_arg="%s")""" % (class_map[et.arg]["native_type"], pattern.arg), \
                  "restriction_argument": pattern.arg, "restriction_type": "pattern", "parent_type": et.arg, \
                  "base_type": False,}
      restricted = True
      #default_type = class_map["string"][0]
    else:
      elemtype = class_map[et.arg]
      #default_type = et.arg
  elif et.arg in INT_RANGE_TYPES:
    range_stmt = et.search_one('range')
    if not range_stmt == None:
      cls = "restricted-%s" % et.arg
      elemtype = {"native_type":  """RestrictedClassType(base_type=%s, restriction_type="range",
                    restriction_arg="%s")"""  % (class_map[et.arg]["native_type"], range_stmt.arg), \
                  "restriction_argument": range_stmt.arg, "restriction_type": "range", "parent_type": et.arg, \
                  "base_type": False,}
      #default_type = class_map[et.arg][0]
      restricted = True
    else:
      elemtype = class_map[et.arg]
  elif et.arg == "enumeration":
    enumeration_dict = {}
    for enum in et.search('enum'):
      enumeration_dict[enum.arg] = {}
      val = enum.search_one('value')
      if not val == None:
        enumeration_dict[enum.arg]["value"] = int(val.arg)
    #elemtype = {"native_type": """YANGEnumType(initial=None,enum_spec=%s)""" % enumeration_dict, "base_type": False, "parent_type": "string",}
    elemtype = {"native_type": """RestrictedClassType(base_type=str, restriction_type="dict_key", \
                restriction_arg=%s,)""" % (enumeration_dict), "restruction_arg": enumeration_dict, \
                "restriction_type": "dict_key", "parent_type": "string", \
                "base_type": False,}
    restricted = True
  elif et.arg == "decimal64":
    fd_stmt = et.search_one('fraction-digits')
    if not fd_stmt == None:
      cls = "restricted-decimal64"
      elemtype = {"native_type": """RestrictedPrecisionDecimalType(precision=%s)""" % fd_stmt.arg, \
                  "base_type": False, "parent_type": "decimal64",}
      restricted = True
    else:
      elemtype = class_map[et.arg]
  elif et.arg == "union":
    elemtype = []
    for uniontype in et.search('type'):
      elemtype_s = copy.deepcopy(build_elemtype(uniontype))
      elemtype_s[1]["yang_type"] = uniontype.arg
      elemtype.append(elemtype_s)
    cls = "union"
  else:
    try:
      elemtype = class_map[et.arg]
    except KeyError:
      print "FATAL: unmapped type (%s)" % et.arg
      if DEBUG:
        pp.pprint(class_map)
        pp.pprint(et)
      sys.exit(127)
    if type(elemtype["native_type"]) == type(list()):
      cls = "leaf-union"
  return (cls,elemtype)


def get_element(fd, element, module, parent, path):
  this_object = []
  default = False
  p = False
  create_list = False

  elemdescr = element.search_one('description')
  if elemdescr == None:
    elemdescr = False
  else:
    elemdescr = elemdescr.arg

  if hasattr(element, 'i_children'):
    if element.keyword in ["container", "list"]:
      p = True
    elif element.keyword in ["leaf-list"]:
      create_list = True
    if element.i_children:
      chs = element.i_children
      get_children(fd, chs, module, element, path)
      elemdict = {"name": safe_name(element.arg), "origtype": element.keyword,
                          "type": "yc_%s_%s" % (safe_name(element.arg),
                          safe_name(path.replace("/", "_"))), "class": element.keyword,
                          "path": safe_name(path), "config": True, "description": elemdescr,}
      if element.keyword == "list":
        elemdict["key"] = safe_name(element.search_one("key").arg)
      this_object.append(elemdict)
      p = True
  if not p:
    if element.keyword in ["leaf-list"]:
      create_list = True
    cls,elemtype = copy.deepcopy(build_elemtype(element.search_one('type')))

    # build a tree that is rooted on this class.
    # perform a breadth-first search - the first node found
    # that has the "default" leaf set, then we take this
    # as the value for the default

    # then starting at the selected default node, traverse
    # until we find a node that is declared to be a base_type

    elemdefault = element.search_one('default')
    default_type = False
    quote_arg = False
    if not elemdefault == None:
      elemdefault = elemdefault.arg
      default_type = elemtype
      #print "   (basetype,basedefault) default was %s" % elemdefault
      #print "   (basetype,basedefault) type was %s" % default_type

    #print "\t\t%s" % element.arg
    #print "\t\t\t%s" % elemtype
    #mapped_elemtype = elemtype
    if isinstance(elemtype, list):
      # this is a union, we should check whether any of the types
      # immediately has a default
      for i in elemtype:
        if "default" in i[1].keys():
          elemdefault = i[1]["default"]
          default_type = i[1]
          #default_type = i[1]
          #mapped_elemtype = i[1]
    elif "default" in elemtype.keys():
      # if the actual type defines the default, then we need to maintain
      # thi
      elemdefault = elemtype["default"]
      default_type = elemtype

    #quote_arg = elemtype["quote_arg"] if "quote_arg" in elemtype.keys() else False
    #default_stmt = element.search_one('default')
    #default_dict = {element.arg: {"default": default_stmt.arg if not default_stmt == None else None,
    #                              "type":elemtype,},
    #
    if not default_type:
      #print "(pre-bfs) type: %s" % elemtype
      #print "(pre-bfs) elem: %s" % element.arg
      #print "(pre-bfs) default: %s" % elemdefault

      if isinstance(elemtype, list):
        # this type has multiple parents
        for i in elemtype:
          if "parent_type" in i[1].keys():
            if isinstance(i[1]["parent_type"], list):
              to_visit = [j for j in i[1]["parent_type"]]
            else:
              to_visit = [i[1]["parent_type"],]
      elif "parent_type" in elemtype.keys():
        if isinstance(elemtype["parent_type"], list):
          to_visit = [i for i in elemtype["parent_type"]]
        else:
          to_visit = [elemtype["parent_type"],]

        checked = list()
        while to_visit:
          check = to_visit.pop(0)
          #print "(bfs) checking %s" %  check
          if check not in checked:
            checked.append(check)
            #print "(bfs) check was %s" % check
            if "parent_type" in class_map[check].keys():
              #print "(bfs) adding %s" % class_map[check]["parent_type"]
              if isinstance(class_map[check]["parent_type"], list):
                to_visit.extend(class_map[check]["parent_type"])
              else:
                to_visit.append(class_map[check]["parent_type"])

        # checked now has the breadth-first search result
        if elemdefault == None:
          for option in checked:
            if "default" in class_map[option].keys():
              elemdefault = class_map[option]["default"]
              default_type = class_map[option]
              break

      #print "(post bfs) default: %s, type: %s" % (elemdefault, elemtype)


    if not elemdefault == None:
      # we now need to check whether there's a need to
      # find out what the base type is for this type
      # we really expect a linear chain here.
      #print "(pre-dfs) defaulttype: %s " % default_type
      #print "(pre-dfs) default: %s" % elemdefault
      #print "(pre-dfs) type: %s" % elemtype

      # if we have a tuple as the type here, this means that
      # the default was set at a level where there was not
      # a single option for the type. check the default
      # against each option, to get a to a single default_type
      if isinstance(default_type, list):
        #print "started a bake-off"
        # "first valid wins" as per rfc6020
        for i in default_type:
          try:
            disposible = i[1]["pytype"](elemdefault)
            default_type = i[1]
            break
          except:
            pass
        #print "(post bake-off) type: %s" % default_type

      if not default_type["base_type"]:
        if "parent_type" in default_type.keys():
          if isinstance(default_type["parent_type"], list):
            to_visit = [i for i in default_type["parent_type"]]
          else:
            to_visit = [default_type["parent_type"],]
        checked = list()
        while to_visit:
          check = to_visit.pop(0) # remove from the top of stack - depth first
          if not check in checked:
            checked.append(check)
            #print "(dfs) check was %s" % check
            if "parent_type" in class_map[check].keys():
              #print "adding %s" % class_map[check]["parent_type"]
              if isinstance(class_map[check]["parent_type"], list):
                to_visit.expand(class_map[check]["parent_type"])
              else:
                to_visit.append(class_map[check]["parent_type"])
        #print "what have we checked for %s? %s " % (elemtype, checked)
        default_type = class_map[checked.pop()]
        #print default_type
        if not default_type["base_type"]:
          raise TypeError, "default type was not a base type"
        #default_type = default_type
        #quote_arg = default_type["quote_arg"] if "quote_arg" in default_type_d.keys() else False

    # else:
    #   if not elemtype["base_type"]:
    #     raise TypeError, "default type was not a base type"
    #   default_type = elemtype["native_type"]

    #print "   (processend) default was %s" % elemdefault
    #print "   (processend) type was %s" % default_type
    if default_type:
      quote_arg = default_type["quote_arg"] if "quote_arg" in default_type.keys() else False
      default_type = default_type["native_type"]

    #assert False, "foo"
    elemconfig = class_bool_map[element.search_one('config').arg] if \
                                  element.search_one('config') else True

    elemname = safe_name(element.arg)

    if create_list:
      cls = "leaf-list"
      elemtype = {"class": cls, "native_type": ("TypedListType", elemtype["native_type"])}
    else:
      if cls == "union":
        elemtype = {"class": cls, "native_type": ("UnionType", elemtype)}
      elemtype = elemtype["native_type"]
    #print "built dictionary -- %s %s %s" % (elemdefault, default_type, cls)
    elemdict = {"name": elemname, "type": elemtype,
                        "origtype": element.search_one('type').arg, "path": safe_name(path),
                        "class": cls, "default": elemdefault,
                        "config": elemconfig, "defaulttype": default_type, "quote_arg": quote_arg,
                        "description": elemdescr,}
    this_object.append(elemdict)
  return this_object

