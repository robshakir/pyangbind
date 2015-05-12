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

class_bool_map = {
  'false':  False,
  'False':  False,
  'true':    True,
  'True':    True,
}

# Words that could turn up in YANG definition files that are actually
# reserved names in Python, such as being builtin types. This list is
# not complete, but will probably continue to grow.
reserved_name = ["list", "str", "int", "global", "decimal", "float",
                  "as", "if", "else", "elsif", "map", "set", "class",
                  "from", "import", "pass", "return", "is"]

class_map = {
  # this map is dynamically built upon but defines how we take
  # a YANG type  and translate it into a native Python class
  # along with other attributes that are required for this mapping.
  #
  # key:                the name of the YANG type
  # native_type:        the Python class that is used to support this
  #                     YANG type natively.
  # map (optional):     a map to take input values and translate them
  #                     into valid values of the type.
  # base_type:          whether the class can be used as class(*args, **kwargs)
  #                     in Python, or whether it is a derived class (such as is
  #                     created based on a typedef, or for types that cannot be
  #                     supported natively, such as enumeration, or a string
  #                     with a restriction placed on it)
  # quote_arg (opt):    whether the argument to this class' __init__ needs to be
  #                     quoted (e.g., str("hello")) in the code that is output.
  # pytype (opt):       A reference to the actual type that is used, this is
  #                     used where we infer types, such as for an input value to
  #                     a union since we need to actually compare the value
  #                     against the __init__ method and see whether it works.
  # parent_type (opt):  for "derived" types, then we store what the enclosed
  #                     type is such that we can create instances where required
  #                     e.g., a restricted string will have a parent_type of a
  #                     string. this can be a list if the type is a union.
  # restriction ...:    where the type is a restricted type, then the class_map
  # (optional)          dict entry can store more information about the type of
  #                     restriction. this is generally used when we need to
  #                     re-initialise an instance of the class, such as in the
  #                     setter methods of containers.
  'boolean':          {"native_type": "YANGBool", "map": class_bool_map,
                          "base_type": True, "quote_arg": True,
                            "pytype": YANGBool},
  'uint8':            {"native_type": "np.uint8", "base_type": True,
                          "pytype": np.uint8},
  'uint16':           {"native_type": "np.uint16", "base_type": True,
                          "pytype": np.uint16},
  'uint32':           {"native_type": "np.uint32", "base_type": True,
                          "pytype": np.uint32},
  'uint64':           {"native_type": "np.uint64", "base_type": True,
                          "pytype": np.uint64},
  'string':           {"native_type": "str", "base_type": True,
                          "quote_arg": True, "pytype": str},
  'decimal64':        {"native_type": "Decimal", "base_type": True,
                          "pytype": decimal.Decimal},
  'empty':            {"native_type": "YANGBool", "map": class_bool_map,
                          "base_type": True, "quote_arg": True,
                            "pytype": YANGBool},
  'int8':             {"native_type": "np.int8", "base_type": True,
                          "pytype": np.int8},
  'int16':            {"native_type": "np.int16", "base_type": True,
                          "pytype": np.int16},
  'int32':            {"native_type": "np.int32", "base_type": True,
                          "pytype": np.int32},
  'int64':            {"native_type": "np.int64", "base_type": True,
                          "pytype": np.int64},
  # this is a temporary hack to support leafref, but it is still TODO
  'leafref':          {"native_type": "str", "base_type": True,
                          "pytype": str, "quote_arg": True,},
}

# all types that support range substmts
INT_RANGE_TYPES = ["uint8", "uint16", "uint32", "uint64",
                    "int8", "int16", "int32", "int64"]

def safe_name(arg):
  """
    Make a leaf or container name safe for use in Python.
  """
  k = arg
  arg = arg.replace("-", "_")
  arg = arg.replace(".", "_")
  if arg in reserved_name:
    arg += "_"
  # store the unsafe->original version mapping
  # so that we can retrieve it when get() is called.
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
  # output the base code that we need to re-use with dynamically generated
  # objects.
  fd.write("from operator import attrgetter\n")
  fd.write("import numpy as np\n")
  fd.write("from decimal import Decimal\n")
  fd.write("""import collections, re

NUMPY_INTEGER_TYPES = [np.uint8, np.uint16, np.uint32, np.uint64,
                    np.int8, np.int16, np.int32, np.int64]

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
      if not self._precision is None:
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
          re.sub("(?P<low>[0-9]+)([ ]+)?\.\.([ ]+)?(?P<high>[0-9]+)", \
            "\g<low>,\g<high>", restriction_arg).split(",")]
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
        self._restriction_test = staticmethod(lambda i: i in \
                                              restriction_arg.keys())
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
  if not isinstance(allowed_type, list):
    allowed_type = [allowed_type,]
  # this was from collections.MutableSequence
  class TypedList(collections.MutableSequence):
    _list = list()
    _allowed_type = allowed_type

    def __init__(self, *args, **kwargs):
      if len(args):
        for i in args[0]:
          self.check(i)
        self._list.extend(args[0])

    def check(self,v):
      passed = False
      for i in self._allowed_type:
        if isinstance(v, i):
          passed = True
        try:
          tmp_t = RestrictedClassType(base_type=str, restriction_type="pattern", restriction_arg="^a")
          if i.__bases__ == tmp_t.__bases__:
            tmp = i(v)
            passed = True
        except:
            pass
      if not passed:
      #if not isinstance(v, self._allowed_type):
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

    def __iter__(self):
      return iter(self._list)

    def __eq__(self, other):
      if self._list == other:
        return True
      return False

    def get(self, filter=False):
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
      if self._contained_class is None:
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
        raise ValueError, "value must be set to an instance of %s" % \
          (self._contained_class)

    def __delitem__(self, k):
      del self._members[k]

    def __len__(self): return len(self._members)

    def keys(self): return self._members.keys()

    def add(self, k):
      try:
        self._members[k] = YANGDynClass(base=self._contained_class)
        setattr(self._members[k], self._keyval, k)
      except TypeError, m:
        try:
          del self._members[k]
        except:
          pass
        raise ValueError, "key value must be valid, %s" % m

    def delete(self, k):
      try:
        del self._members[k]
      except KeyError, m:
        raise KeyError, "key %s was not in list (%s)" % (k,m)

    def get(self, filter=False):
      d = {}
      for i in self._members:
        if hasattr(self._members[i], "get"):
          d[i] = self._members[i].get(filter=filter)
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
  yang_name = kwargs.pop("yang_name", False)
  parent_instance = kwargs.pop("parent", False)
  choice_member = kwargs.pop("choice", False)
  if not base_type:
    raise AttributeError, "must have a base type"
  print "check %s => %s" % (base_type, len(args))
  if base_type in NUMPY_INTEGER_TYPES and len(args):
    if isinstance(args[0], list):
      raise TypeError, "do not support creating numpy ndarrays!"
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
        raise TypeError, "did not find a valid type using the argument as a" + \
                            "hint"
      # otherwise, hop, skip and jump with the last candidate
      base_type = candidate_type

  class YANGBaseClass(base_type):
    __slots__ = ('_default', '_changed', '_yang_name', '_choice', '_parent')
    def __new__(self, *args, **kwargs):
      obj = base_type.__new__(self, *args, **kwargs)
      return obj

    def __init__(self, *args, **kwargs):
      self._default = False
      self._changed = False
      self._yang_name = yang_name
      self._parent = parent_instance
      self._choice = choice_member
      if default:
        self._default = default
      if len(args):
        if not args[0] == self._default:
          self._changed = True
      try:
        super(YANGBaseClass, self).__init__(*args, **kwargs)
      except:
        #print args
        #print kwargs
        #print base_type
        raise TypeError, "couldn't generate dynamic type"

    def changed(self):
      return self._changed

    def set(self,choice=False):
      print "deal with %s @ %s" % (repr(choice), self._yang_name)
      if hasattr(self, '__choices__') and choice:
        print "my choices: %s" % repr(self.__choices__)
        for ch in self.__choices__.keys():
          if ch == choice[0]:
            for case in self.__choices__[ch]:
              if not case == choice[1]:
                print case
                for elem in self.__choices__[ch][case]:
                  method = "_unset_%s" % elem
                  if not hasattr(self, method):
                    raise AttributeError, "unmapped choice!"
                  x = getattr(self, method)
                  x()
      print self._choice
      if self._choice and not choice:
        print self._choice
        choice=self._choice
      self._changed = True
      print "new choice: %s" % repr(choice)
      print "parent: %s" % repr(self._parent)
      if self._parent and hasattr(self._parent, "set"):
        print "my parent had a set!"
        self._parent.set(choice=choice)

    def yang_name(self):
      return self._yang_name

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
""")

  # we need to build a dependency map
  # foreach module:
  #   foreach import:
  #      record dependencies for the module - along with prefix
  dependency_d = {}
  #pp.pprint(modules)
  original_modules = [i.arg for i in modules]
  to_process = copy.deepcopy(modules)
  module_d = {}
  while len(to_process):
    module = to_process.pop(0)
    if not module.arg in dependency_d.keys():
      dependency_d[module.arg] = list()
    #print "searched %s for dependencies" % (module.arg)
    dependencies = module.search('import')
    #print "and got %s" % [i.arg for i in dependencies]
    #print dir(module)
    #try:
    #  print "import %s for %s" % (module.i_is_safe_import, module.arg)
    #except:
    #  pass
    #print "dependencies for %s are %s" % (module.arg, [i.arg for i in dependencies])
    if not module.arg in module_d.keys():
      module_d[module.arg] = module
    if not dependencies is None:
      for dep in dependencies:
        prefix = dep.search_one('prefix').arg
        dependency_d[module.arg].append((dep.arg, prefix))
        to_process.append(dep)
        if not dep.arg in module_d.keys():
          module_d[dep.arg] = dep

  for dependency in dependency_d:
    if len(dependency_d[dependency]) == 0:
      sys.stderr.write("WARNING: did not find module imports for %s, " % dependency)
      sys.stderr.write("you may need to specify the path to this module ")
      sys.stderr.write("for all dependencies to be resolved.\n")

  #print "dependency dictionary"
  #pp.pprint(dependency_d)
  #print "\n\n"
  known_modules = {}
  module_process_order = []
  to_process = dependency_d.keys()
  while len(to_process):
    module = to_process.pop(0)
    if len(dependency_d[module]) == 0:
      known_modules[module] = [None,]
      module_process_order.append(module)
      if module in original_modules:
        #known_modules[module].append('')
        known_modules[module].append(module_d[module].search_one('prefix').arg)
    else:
      unknown_dependencies = False
      #known_modules[module].append('')
      for dep in dependency_d[module]:
        #print "dependencies: "
        #print dep
        #print "known"
        #print known_modules.keys()
        #print "\n\n"
        if dep[0] in known_modules.keys():
          #print "adding %s as %s" % (dep[0], dep[1])
          if not dep[1] in known_modules[dep[0]]:
            known_modules[dep[0]].append(dep[1]) # add this module to process with
                                               # the local prefix
        else:
          unknown_dependencies = True
      if not unknown_dependencies:
        module_process_order.append(module)
        known_modules[module] = [None,]
        if module in original_modules:
          known_modules[module].append(module_d[module].search_one('prefix').arg)
          #print "Asked to process %s with no prefix" % (module)
      else:
        to_process.append(module)

  #print known_modules
  #print module_process_order
  #pp.pprint(dependency_d)
  #pp.pprint(known_modules)
  #pp.pprint(module_process_order)
  #assert False, "TODO"

  #print "got to building %s" % module_process_order
  #print known_modules
  built = []
  for module in module_process_order:
    chkd_build = []
    for prefix in known_modules[module]:
      if not "%s%s" % ("%s:" % prefix if prefix else "", module) in built:
        chkd_build.append(prefix)
    get_typedefs(ctx, module_d[module], prefix_list=chkd_build)
    get_identityrefs(ctx, module_d[module], prefix_list=chkd_build)
    # TODO: same for identityrefs
    for pfx in chkd_build:
      built.append("%s%s" % ("%s:" % prefix if prefix else "", module))
    #for prefix in known_modules[module]:
    #  print "processing %s:%s" % (prefix, module)
    #  if not "%s:%s" % (prefix, module) in built:
    #    get_typedefs(ctx, module_d[module], prefix=prefix)
    #    get_identityrefs(ctx, module_d[module], prefix=prefix)
    #    built.append("%s:%s" % (prefix,module))
  #print "got out of building"
  #processed_modules = []
  #for module in modules:
    #typedefs = get_typedefs(ctx, module)
    #mods = module.search('import')
    # we have to do this module last, since it may
    # have typedef dependencies elsewhere
    #mods.append(module)
    #for i in mods:
    #  if i.arg in processed_modules:
    #    continue
    #  prefix = i.search_one('prefix').arg
    #  if i == module:
    #    get_typedefs(ctx, i, prefix=False)
    #    get_identityrefs(ctx, i, prefix=False)
    #  if not get_typedefs(ctx, i, prefix=prefix):
    #    raise TypeError, "Invalid specification of typedefs"
    #  if not get_identityrefs(ctx, i, prefix=prefix):
    #    raise TypeError, "Invalid specification of identityrefs"
    #  processed_modules.append(i.arg)
  #print [i.arg for i in modules]
  # we need to parse each module
  for module in modules:
    #print "processing %s...." % module.arg
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

def get_identityrefs(ctx, module, prefix=False, prefix_list=False):

  mod = ctx.get_module(module.arg)
  if mod is None:
    raise AttributeError, "unmapped identities, please specify path to %s!" \
                                % (module.arg)

  pfx = []
  if prefix:
    pfx.append(prefix)
  if prefix_list:
    pfx.extend(prefix_list)
  if not None in pfx:
    pfx.append(None)

  identities = mod.search('identity')
  definition_dict = {}
  remaining_identities = []
  for i in identities:
    for p in pfx:
      name = "%s%s" % ("%s:" % p if p is not None else "", i.arg)
      definition_dict[name] = i
      remaining_identities.append(name)

  known_identities = []
  identity_d = {}
  while remaining_identities:
    item = remaining_identities.pop(0)
    definition = definition_dict[item]
    base = definition.search_one('base')
    if base is None:
      identity_d[item] = {}
      known_identities.append(item)
    else:
      for p in pfx:
        base_name = "%s%s" % ("%s:" % p if p is not None else "", base.arg)
        if base_name in known_identities:
          val = item.split(":")[1] if ":" in item else item
          identity_d[base_name][val] = {}
        else:
          remaining_identities.append(item)


  for i in identity_d.keys():
    id_type = {"native_type": """RestrictedClassType(base_type=str, \
                    restriction_type="dict_key", \
                    restriction_arg=%s,)""" % identity_d[i], \
                "restriction_argument": identity_d[i], \
                "restriction_type": "dict_key",
                "parent_type": "string",
                "base_type": False,}
    class_map[i] = id_type

  return True


def get_typedefs(ctx, module, prefix=False, prefix_list=False):
  mod = ctx.get_module(module.arg)
  if mod is None:
    raise AttributeError, "unmapped types, please specify path to %s!" \
                                % (module.arg)
  typedefs = mod.search('typedef')
  restricted_arg = False
  default = False

  # we need to check whether there are any dependencies between
  # the typedefs that we have within the module.
  process_typedefs_ordered = []
  known_typedefs = class_map.keys()
  # we always know enumerations even though they are non-native
  # because they cannot have subtypes
  known_typedefs.append("enumeration")
  remaining_typedefs = []
  definition_dict = {}

  pfx = []
  if prefix:
    pfx.append(prefix)
  if prefix_list:
    pfx.extend(prefix_list)
  if not None in pfx:
    pfx.append(None)


  for i in typedefs:
    for p in pfx:
      name = "%s%s" % ("%s:" % p if p is not None else "", i.arg)
      definition_dict[name] = i
      remaining_typedefs.append(name)
    #if not i.arg == "%s:%s" % (prefix, i.arg) and prefix:
    #  name = "%s:%s" % (prefix, i.arg)
    #else:
    #  name = i.arg
    #definition_dict[name] = i
    #print "added %s as %s" % (i.arg, name)
    #remaining_typedefs.append(name)


  #pp.pprint(definition_dict.keys())
  #assert False, "TODO"
  # for each remaining typedef definition that we
  # do not know about - retrieve the definition
  # check whether it references a type that we now
  # know about, and if not, re-queue it. if so
  # add it to the queue
  c = 0
  while remaining_typedefs:
    if c > 500:
      # this is a safety net, we have unresolved
      # dependencies, and it is not possible to
      # fix it -- one of the warnings we gave
      # earlier needs to be listened to.
      sys.stderr.write("UNRESOLVED DEPENCIES: %s" % remaining_typedefs)
      sys.stderr.write("%s \n" % subtypes)
      sys.stderr.write("\nCHECK WARNINGS!\n")
      sys.exit(127)
    i_name = remaining_typedefs.pop(0)
    #print "handling %s" % i_name
    item = definition_dict[i_name]

    this_type = item.search_one('type').arg
    if this_type == "union":
      subtypes = [i.arg for i in item.search_one('type').search('type')]
    else:
      subtypes = [this_type,]
    #print "and it had ... %s" % subtypes
    #print known_typedefs
    any_unknown = False
    for i in subtypes:
      if not i in known_typedefs:
        # check whether this type was actually local to the module that
        # we are looking at too
        tmp_name = "%s:%s" % (prefix, i)
        #print prefix
        #print tmp_name
        #print known_typedefs
        if not tmp_name in known_typedefs:
          any_unknown = True
    if not any_unknown:
      process_typedefs_ordered.append((i_name,item))
      known_typedefs.append(i_name)
    else:
      if not i_name in remaining_typedefs:
        remaining_typedefs.append(i_name)
    c += 1

  for i_tuple in process_typedefs_ordered:
    item = i_tuple[1]
    type_name = i_tuple[0]
    #print "building %s..." % item.arg
    mapped_type = False
    restricted_arg = False
    cls,elemtype = copy.deepcopy(build_elemtype(item.search_one('type'), \
                                    prefix=prefix))
    #pp.pprint(elemtype)
    known_types = class_map.keys()
    # Enumeration is a native type, but is not natively supported
    # in the class_map, and hence we append it here.
    known_types.append("enumeration")

    #type_name = "%s%s" % ("%s:" % prefix if prefix else "", item.arg)
    if type_name in known_types:
      raise TypeError, "Duplicate definition of %s" % type_name
    default_stmt = item.search_one('default')
    if not type(elemtype) == type(list()):
      restricted = False
      class_map[type_name] = {"native_type": elemtype["native_type"], \
                                "base_type": False,}
      if "parent_type" in elemtype.keys():
        class_map[type_name]["parent_type"] = elemtype["parent_type"]
      else:
        yang_type = item.search_one('type').arg
        if not yang_type in known_types:
          raise TypeError, "typedef specified a native type that was not \
                            supported"
        class_map[type_name]["parent_type"] = yang_type
      if default_stmt is not None:
        class_map[type_name]["default"] = default_stmt.arg
      if "restriction_type" in elemtype.keys():
        class_map[type_name]["restriction_type"] = \
                                              elemtype["restriction_type"]
        class_map[type_name]["restriction_argument"] = \
                                              elemtype["restriction_argument"]
      if "quote_arg" in elemtype.keys():
        class_map[type_name]["quote_arg"] = elemtype["quote_arg"]
    else:
      native_type = []
      parent_type = []
      default = False if default_stmt is None else default_stmt.arg
      for i in elemtype:
        native_type.append(i[1]["native_type"])
        if i[1]["yang_type"] in known_types:
          parent_type.append(i[1]["yang_type"])
        else:
          msg = "typedef in a union specified a native type that was not"
          msg += "supported (%s in %s)" % (i[1]["yang_type"], item.arg)
          raise TypeError, msg
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

def get_children(fd, i_children, module, parent, path=str(), parent_cfg=True, choice=False):
  used_types,elements = [],[]

  if parent_cfg:
    # the first time we find a container that has config false set on it
    # then we need to hand this down the tree - we don't need to look if
    # parent_cfg has already been set to False as we need to inherit.
    parent_config = parent.search_one('config')
    if parent_config is not None:
      parent_config = parent_config.arg
      if parent_config.upper() == "FALSE":
        # this container is config false
        parent_cfg = False

  #choices = {}
  for ch in i_children:
    print "calling get_element for %s" % ch.arg
    if ch.keyword == "choice":
      #print "processing %s..." % ch.arg
      #choices[ch.arg] = []
      for choice_ch in ch.i_children:
        #print "processing %s..." % choice_ch.arg
        #choices[ch.arg].append(choice_ch.arg)
        # these are case statements
        for case_ch in choice_ch.i_children:
          print "calling get_element for %s" % case_ch.arg
          elements += get_element(fd, case_ch, module, parent, path+"/"+ch.arg, parent_cfg=parent_cfg, choice=(ch.arg,choice_ch.arg))
    else:
      elements += get_element(fd, ch, module, parent, path+"/"+ch.arg, parent_cfg=parent_cfg, choice=choice)

  #pp.pprint(choices)

  if parent.keyword in ["container", "module", "list"]:
    if not path == "":
      fd.write("class yc_%s_%s(object):\n" % (safe_name(parent.arg), \
        safe_name(path.replace("/", "_"))))
    else:
      fd.write("class %s(object):\n" % safe_name(parent.arg))

    parent_descr = parent.search_one('description')
    if parent_descr is not None:
      parent_descr = "\n\n     YANG Description: %s" % parent_descr.arg
    else:
      parent_descr = ""

    fd.write("""  \"\"\"
     This class was auto-generated by the PythonClass plugin for PYANG
     from YANG module %s - based on the path %s. Each member element of
     the container is represented as a class variable - with a specific
     YANG type.%s
    \"\"\"\n"""  % (module.arg, (path if not path == "" else "/"), \
                    parent_descr))
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

    #if len(choices.keys()):
    #  choices_str = "  __choices__ = "
    #  choices_str += repr(choices)
    #  fd.write(choices_str)
    #  fd.write("\n")

    choices = {}
    choice_attrs = []
    classes = []
    for i in elements:
      class_str = False
      #rint "looping elements"
      if "default" in i.keys() and not i["default"] is None:
        default_arg = repr(i["default"]) if i["quote_arg"] else "%s" \
                                    % i["default"]

      if i["class"] == "leaf-list":
        class_str = "__%s" % (i["name"])
        class_str += " = YANGDynClass(base="
        class_str += "%s(allowed_type=%s)" % i["type"]["native_type"]
        if "default" in i.keys() and not i["default"] is None:
          class_str += ", default=%s(%s)" % (i["defaulttype"], default_arg)
      elif i["class"] == "list":
        class_str = "__%s" % (i["name"])
        class_str += " = YANGDynClass(base=YANGListType("
        class_str += "\"%s\",%s)" % (i["key"], i["type"])
      elif i["class"] == "union":
        class_str = "__%s" % (i["name"])
        class_str += " = YANGDynClass(base=["
        for u in i["type"][1]:
          class_str += "%s," % u[1]["native_type"]
        class_str += "]"
        if "default" in i.keys() and not i["default"] is None:
          class_str += ", default=%s(%s)" % (i["defaulttype"], default_arg)
      elif i["class"] == "leaf-union":
        class_str = "__%s" % (i["name"])
        class_str += " = YANGDynClass(base=["
        for u in i["type"]:
          class_str += "%s," % u
        class_str += "]"
        if "default" in i.keys() and not i["default"] is None:
          class_str += ", default=%s(%s)" % (i["defaulttype"], default_arg)
      else:
        class_str = "__%s" % (i["name"])
        class_str += " = YANGDynClass("
        class_str += "base=%s" % i["type"]
        if "default" in i.keys() and not i["default"] is None:
          class_str += ", default=%s(%s)" % (i["defaulttype"], default_arg)
      if class_str:
        class_str += ", yang_name=\"%s\"" % i["yang_name"]
        class_str += ", parent=self"
        if i["choice"]:
          class_str += ", choice=%s" % repr(i["choice"])
          choice_attrs.append(i["name"])
          if not i["choice"][0] in choices.keys():
            choices[i["choice"][0]] = {}
          if not i["choice"][1] in choices[i["choice"][0]].keys():
            choices[i["choice"][0]][i["choice"][1]] = []
          choices[i["choice"][0]][i["choice"][1]].append(i["name"])
        class_str += ")\n"
        classes.append(class_str)
    print "my choice attrs: %s" % choice_attrs
    fd.write("""
  def __init__(self, *args, **kwargs):\n""")
    for c in classes:
      fd.write("    self.%s" % c)
    fd.write("""
    if args:
      # we do not support creating a new instance of a container
      # object with an argument.
      raise TypeError, "YANG containers cannot be initiated with an argument"
""")

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
        #native_type = i["type"]["native_type"]
        native_type = "%s(allowed_type=%s)" % i["type"]["native_type"]
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

      if "default" in i.keys() and not i["default"] is None:
        if i["quote_arg"]:
          default_arg = repr(i["default"])
        else:
          default_arg = i["default"]
        if not i["class"] == "union":
          default_s = ",default=%s(%s)" % (i["defaulttype"], default_arg)
        else:
          default_s = ",default=%s(%s)" % (i["defaulttype"], default_arg)
      else:
        default_s = ""

      set_str = "base=%s" % native_type
      set_str += default_s
      set_str += ", yang_name=\"%s\"" % i["yang_name"]
      set_str += ", parent=self"
      if i["choice"]:
        set_str += ", choice=%s" % repr(i["choice"])
      fd.write("""
  def _set_%s(self,v):
    \"\"\"
      Setter method for %s, mapped from YANG variable %s (%s)
      If this variable is read-only (config: false) in the
      source YANG file, then _set_%s is considered as a private
      method. Backends looking to populate this variable should
      do so via calling thisObj._set_%s() directly.%s
    \"\"\"""" % (i["name"], i["name"], i["path"], \
                          i["origtype"], i["name"], i["name"], description_str,))
      fd.write("""
    try:
      t = YANGDynClass(v,%s)
    except (TypeError, ValueError):
      raise TypeError(\"\"\"%s must be of a type compatible with %s\"\"\")
    self.__%s = t\n""" % (set_str, i["name"], \
                          native_type, i["name"]))
      fd.write("    self.set()\n")

      if i["name"] in choice_attrs:
        fd.write("""
  def _unset_%s(self):
    self.__%s = YANGDynClass(%s)
    print "this dude was unset! %s"\n\n""" % (i["name"], i["name"], set_str, i["name"]))
    for i in elements:
      if i["config"] and parent_cfg:
        fd.write("""  %s = property(_get_%s, _set_%s)\n""" % \
                          (i["name"], i["name"], i["name"]))
      else:
        fd.write("""  %s = property(_get_%s)\n""" % (i["name"], i["name"]))

  fd.write("\n")
  fd.write("  __choices__ = %s" % repr(choices))
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
    # for each YANG element within this container.
    for element_name in self.__elements.keys():
      element = getattr(self, element_name, error)
      if hasattr(element, "yang_name"):
        # retrieve the YANG name method
        yang_name = getattr(element, "yang_name", error)
        element_id = yang_name()
      else:
        element_id = element_name
      if hasattr(element, "get"):
        # this is a YANG container that has its own
        # get method
        d[element_id] = element.get(filter=filter)
        if filter == True:
          # if the element hadn't changed but we were
          # filtering unchanged elements, remove it
          # from the dictionary
          if isinstance(d[element_id], dict):
            for entry in d[element_id].keys():
              if hasattr(d[element_id][entry], "changed"):
                if not d[element_id][entry].changed():
                  del d[element_id][entry]
            if len(d[element_id].keys()) == 0:
              del d[element_id]
          elif isinstance(d[element_id], list):
            for list_entry in d[element_id]:
              if hasattr(list_entry, "changed"):
                if not list_entry.changed():
                  d[element_id].remove(list_entry)
            if len(d[element_id]) == 0:
              del d[element_id]
      else:
        # this is an attribute that does not have get()
        # method

        if filter == False and not element.changed():
          if not element._default == False and element._default:
            d[element_id] = element._default
          else:
            d[element_id] = element
        elif element.changed():
          d[element_id] = element
        else:
          # changed = False, and filter = True
          pass
    return d
  \n""" % e_str)
  fd.write("\n")
  return None

def build_elemtype(et, prefix=False):
  cls = "leaf"
  #et = element.search_one('type')
  restricted = False

  if et.arg == "string":
    pattern = et.search_one('pattern')
    if not pattern is None:
      cls = "restricted-string"
      elemtype = {"native_type": """RestrictedClassType(base_type=%s, \
                                    restriction_type="pattern",
                                    restriction_arg="%s")""" % \
                                    (class_map[et.arg]["native_type"], \
                                     pattern.arg), \
                                     "restriction_argument": pattern.arg, \
                                     "restriction_type": "pattern", \
                                     "parent_type": et.arg, \
                                     "base_type": False,}
      restricted = True
      #default_type = class_map["string"][0]
    else:
      elemtype = class_map[et.arg]
      #default_type = et.arg
  elif et.arg in INT_RANGE_TYPES:
    range_stmt = et.search_one('range')
    if not range_stmt is None:
      cls = "restricted-%s" % et.arg
      elemtype = {"native_type":  """RestrictedClassType(base_type=%s, \
                                     restriction_type="range", \
                                     restriction_arg="%s")"""  % \
                                     (class_map[et.arg]["native_type"], \
                                      range_stmt.arg), \
                                      "restriction_argument": range_stmt.arg, \
                                      "restriction_type": "range", \
                                      "parent_type": et.arg, \
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
      if val is not None:
        enumeration_dict[enum.arg]["value"] = int(val.arg)
    elemtype = {"native_type": """RestrictedClassType(base_type=str, \
                                  restriction_type="dict_key", \
                                  restriction_arg=%s,)""" % \
                                  (enumeration_dict), \
                                  "restriction_argument": \
                                  enumeration_dict, \
                                  "restriction_type": "dict_key", \
                                  "parent_type": "string", \
                                  "base_type": False,}
    restricted = True
  elif et.arg == "decimal64":
    fd_stmt = et.search_one('fraction-digits')
    if not fd_stmt is None:
      cls = "restricted-decimal64"
      elemtype = {"native_type": \
                    """RestrictedPrecisionDecimalType(precision=%s)""" % \
                    fd_stmt.arg, "base_type": False, \
                    "parent_type": "decimal64",}
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
  elif et.arg == "identityref":
    base_stmt = et.search_one('base')
    if base_stmt is None:
      raise ValueError, "identityref specified with no base statement"
    try:
      elemtype = class_map[base_stmt.arg]
    except KeyError:
      sys.stderr.write("FATAL: identityref with an unknown base\n")
      if DEBUG:
        pp.pprint(class_map.keys())
        pp.pprint(et.arg)
        pp.pprint(base_stmt.arg)
      sys.exit(127)
  else:
    try:
      elemtype = class_map[et.arg]
    except KeyError:
      passed = False
      if prefix:
        try:
          #print "trying %s:%s..." % (prefix, et.arg)
          tmp_name = "%s:%s" % (prefix, et.arg)
          elemtype = class_map[tmp_name]
          passed = True
        except:
          pass
      if passed == False:
        sys.stderr.write("FATAL: unmapped type (%s)\n" % (et.arg))
        if DEBUG:
          pp.pprint(class_map.keys())
          pp.pprint(et.arg)
          pp.pprint(prefix)
        sys.exit(127)
    if type(elemtype["native_type"]) == type(list()):
      cls = "leaf-union"
  return (cls,elemtype)


def get_element(fd, element, module, parent, path, parent_cfg=True,choice=False):
  this_object = []
  default = False
  p = False
  create_list = False

  elemdescr = element.search_one('description')
  if elemdescr is None:
    elemdescr = False
  else:
    elemdescr = elemdescr.arg

  if hasattr(element, 'i_children'):
    if element.keyword in ["container", "list"]:
      p = True
    elif element.keyword in ["leaf-list"]:
      create_list = True

    if element.keyword in ["choice"]:
      path_parts = path.split("/")
      npath = ""
      for i in range(0,len(path_parts)-1):
        npath += "%s/" % path_parts[i]
      npath.rstrip("/")
      #print "MONKEY new path was %s from %s" % (npath,path)
    else:
      npath=path
    if element.i_children:
      chs = element.i_children
      print "calling get_children for %s" %  [i.arg for i in chs]
      get_children(fd, chs, module, element, npath, parent_cfg=parent_cfg, choice=choice)
      elemdict = {"name": safe_name(element.arg), "origtype": element.keyword,
                          "type": "yc_%s_%s" % (safe_name(element.arg),
                          safe_name(path.replace("/", "_"))),
                          "class": element.keyword,
                          "path": safe_name(npath), "config": True,
                          "description": elemdescr,
                          "yang_name": element.arg,
                          "choice": choice,
                 }
      if element.keyword == "list":
        elemdict["key"] = safe_name(element.search_one("key").arg)
      this_object.append(elemdict)
      p = True
  if not p:
    if element.keyword in ["leaf-list"]:
      create_list = True
    #print "element: %s %s" % (element.keyword, element.arg)
    #print "was building %s" % element.arg
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
    if not elemdefault is None:
      elemdefault = elemdefault.arg
      default_type = elemtype
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
      # this
      elemdefault = elemtype["default"]
      default_type = elemtype


    # we need to indicate that the default type for the class_map
    # is str
    tmp_class_map = copy.deepcopy(class_map)
    tmp_class_map["enumeration"] = {"parent_type": "string"}

    if not default_type:
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
          if check not in checked:
            checked.append(check)
            if "parent_type" in tmp_class_map[check].keys():
              if isinstance(tmp_class_map[check]["parent_type"], list):
                to_visit.extend(tmp_class_map[check]["parent_type"])
              else:
                to_visit.append(tmp_class_map[check]["parent_type"])

        # checked now has the breadth-first search result
        if elemdefault is None:
          for option in checked:
            if "default" in tmp_class_map[option].keys():
              elemdefault = tmp_class_map[option]["default"]
              default_type = tmp_class_map[option]
              break

    if elemdefault is not None:
      # we now need to check whether there's a need to
      # find out what the base type is for this type
      # we really expect a linear chain here.

      # if we have a tuple as the type here, this means that
      # the default was set at a level where there was not
      # a single option for the type. check the default
      # against each option, to get a to a single default_type
      if isinstance(default_type, list):
        # "first valid wins" as per rfc6020
        for i in default_type:
          try:
            disposible = i[1]["pytype"](elemdefault)
            default_type = i[1]
            break
          except:
            pass

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
            if "parent_type" in tmp_class_map[check].keys():
              if isinstance(tmp_class_map[check]["parent_type"], list):
                to_visit.expand(tmp_class_map[check]["parent_type"])
              else:
                to_visit.append(tmp_class_map[check]["parent_type"])
        default_type = tmp_class_map[checked.pop()]
        #print default_type
        if not default_type["base_type"]:
          raise TypeError, "default type was not a base type"

    if default_type:
      quote_arg = default_type["quote_arg"] if "quote_arg" in \
                    default_type.keys() else False
      default_type = default_type["native_type"]

    elemconfig = class_bool_map[element.search_one('config').arg] if \
                                  element.search_one('config') else True

    elemname = safe_name(element.arg)

    if create_list:
      cls = "leaf-list"
      if isinstance(elemtype, list):
        c = 0
        allowed_types = []
        for subtype in elemtype:
          # nested union within a leaf-list type
          if isinstance(subtype, tuple):
            #print subtype[0]
            #print subtype[1]
            if subtype[0] == "leaf-union":
              for subelemtype in subtype[1]["native_type"]:
                allowed_types.append(subelemtype)
            else:
              allowed_types.append(subtype[1]["native_type"])
          else:
            allowed_types.append(subtype["native_type"])
      else:
        allowed_types = elemtype["native_type"]

      #print "%s: %s" % (elemname, elemtype)
      #pp.pprint(elemtype)
      elemtype = {"class": cls, "native_type": ("TypedListType", \
                  allowed_types)}
    else:
      if cls == "union":
        elemtype = {"class": cls, "native_type": ("UnionType", elemtype)}
      elemtype = elemtype["native_type"]
    elemdict = {"name": elemname, "type": elemtype,
                        "origtype": element.search_one('type').arg, "path": \
                        safe_name(path),
                        "class": cls, "default": elemdefault, \
                        "config": elemconfig, "defaulttype": default_type, \
                        "quote_arg": quote_arg, \
                        "description": elemdescr, "yang_name": element.arg,
                        "choice": choice,
               }
    this_object.append(elemdict)
  return this_object

