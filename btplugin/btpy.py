"""Generate YANG Python Bindings from a YANG model.

(c) Rob Shakir (rob.shakir@bt.com, rjs@rob.sh) - 2015.

This module is tentatively licensed under the Apache licence.

"""

import optparse
import sys
import re
import string

from pyang import plugin
from pyang import statements

USED_TYPES = []

#class YANGParent():
#  name = str()
#  def __init__(self, n):
#    self.name = n
#
#class YANGContainer(YANGParent):
#  pass

# this is a hack solution, we need to fix this to have
# dynamic learning of types

reserved_name = ["list", "str", "int", "global"]

class_bool_map = {
  'false':  False,
  'False':  False,
  'true':    True,
  'True':    True,
}

class_map = {
  'boolean':          {"native_type": "YANGBool", "map": class_bool_map, "base_type": True},
  'uint8':            {"native_type": "np.uint8", "base_type": True},
  'uint16':           {"native_type": "np.uint16", "base_type": True},
  'uint32':           {"native_type": "np.uint32", "base_type": True},
  'string':           {"native_type": "str", "base_type": True},
  'decimal64':        {"native_type": "float", "base_type": True},
  # we need to look at how to parse typedefs
  #'inet:as-number':     ("int", False),
  #'inet:ipv4-address':   ("str", False),
  #'decimal64':       ("float", False),
  # more types to be added here
}

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
  fd.write("import numpy as np\n\n")

  fd.write("""import collections, re

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
        x = [base_type(i) for i in \
          re.sub("(?P<low>[0-9]+)([ ]+)?\.\.([ ]+)?(?P<high>[0-9]+)", "\g<low>,\g<high>", \
           restriction_arg).split(",")]
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
""")
  r_typedefs = {}
  for module in modules:
    typedefs = get_typedefs(ctx, module)
    mods = module.search('import')
    for i in mods:
      prefix = i.search_one('prefix').arg
      for k,v in get_typedefs(ctx,i,prefix=prefix).iteritems():
        print "%s,%s" % (k,v)
        if not k in r_typedefs:
          r_typedefs[k] = v
        else:
          raise AttributeError, "Duplicate definition of a type (%s)" % k
  print r_typedefs

  for k,v in r_typedefs.iteritems():
    restricted = False
    if v[1]:
      m_name = """RestrictedClassType(base_type=%s, restriction_type="%s",restriction_arg="%s")""" % \
        (class_map[v[0]]["native_type"], v[1], v[2])
      restricted = True
    else:
      m_name = v[0]
    class_map[k] = {"native_type": m_name, "base_type": False, "parent_type": v[3],}
    if v[4]:
      class_map[k]["default"] = v[4]
    if restricted:
      class_map[k]["restriction_type"] = v[1]
      class_map[k]["restriction_argument"] = v[0]
      class_map[k]["base_type"] = False
      class_map[k]["parent_type"] = v[0]

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
  typedefs = mod.search('typedef')
  restricted_arg = False
  default = False
  for item in typedefs:
    mapped_type = False
    restricted_arg = False
    for x in item.substmts:
      if x.keyword == "type":
        type_type = x.arg
        if x.arg in ["uint8", "uint16", "uint32",]:
          restriction = x.search_one("range")
          if not restriction == None:
            mapped_type = "%s" % x.arg
            restricted_arg = restriction.arg
            restriction_k = restriction.keyword
          else:
            restriction_k = False
            mapped_type = class_map[type_type]["native_type"]
        elif x.arg in ["string"]:
          restriction = x.search_one("pattern")
          if not restriction == None:
            mapped_type = "string"
            restricted_arg = restriction.arg
            restriction_k = restriction.keyword
          else:
            restriction_k = False
            try:
              mapped_type = class_map[type_type]["native_type"]
            except KeyError:
              raise AttributeError, "tried to map to derived type" \
                + " which was unknown"
        else:
          restriction = False
          mapped_type = class_map[type_type]["native_type"]
      elif x.keyword == "default":
        default = x.arg
    r_typedefs[item.arg] = (mapped_type, restriction_k, restricted_arg, type_type, default)
  return r_typedefs

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
    fd.write("""  \"\"\"
     This class was auto-generated by the PythonClass plugin for PYANG
     from YANG module %s - based on the path %s.
     Each member element of the container is represented as a class
     variable - with a specific YANG type.
    \"\"\"\n"""  % (module.arg, (path if not path == "" else "/")))
  else:
    raise TypeError, "unhandled keyword with children %s" % parent.keyword

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
      if i["class"] == "leaf-list":
        class_str = "  __%s" % (i["name"])
        class_str += " = defineYANGDynClass(base="
        class_str += "%s(allowed_type=%s), " % i["type"]
        if "default" in i.keys() and not i["default"] == None:
          class_str += "default=%s(%s)" % (i["defaulttype"], i["default"])
        class_str += ")\n"
      elif i["class"] == "list":
        class_str = "  __%s" % (i["name"])
        class_str += " = defineYANGDynClass(base=YANGListType("
        class_str += "\"%s\",yc_%s_%s), " % (i["key"], safe_name(i["name"]), \
                        safe_name(path.replace("/","_"))+"_"+safe_name(i["name"]))
        class_str += ")\n"
      else:
        class_str = "  __%s" % (i["name"])
        class_str += " = defineYANGDynClass("
        class_str += "base=%s, " % i["type"]
        if "default" in i.keys() and not i["default"] == None:
          class_str += "default=%s(\"%s\")" % (i["defaulttype"], i["default"])
        class_str += ")\n"
      fd.write(class_str)

    node = {}
    for i in elements:
      fd.write("""
  def _get_%s(self):
    \"\"\"
      Getter method for %s, mapped from YANG variable %s (%s)
    \"\"\"
    return self.__%s
      """ % (i["name"], i["name"], i["path"], i["origtype"],
             i["name"]))
      if type(i["type"]) == type((1,1)):
        ntype = i["type"][0]
      else:
        ntype = i["type"]
      fd.write("""
  def _set_%s(self,v):
    \"\"\"
      Setter method for %s, mapped from YANG variable %s (%s)
      If this variable is read-only (config: false) in the
      source YANG file, then _set_%s is considered as a private
      method. Backends looking to populate this variable should
      do so via calling thisObj._set_%s() directly.
    \"\"\"
    try:
      t = defineYANGDynClass(v,base=%s)
    except (TypeError, ValueError):
      raise TypeError(\"\"\"%s must be of a type compatible with %s\"\"\")
    self.__%s = t\n""" % (i["name"], i["name"], i["path"],
                          i["origtype"], i["name"], i["name"], \
                          ntype, i["name"], ntype, i["name"]))
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

def get_element(fd, element, module, parent, path):
  this_object = []
  default = False
  p = False
  create_list = False
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
                          "path": safe_name(path), "config": True}
      if element.keyword == "list":
        elemdict["key"] = safe_name(element.search_one("key").arg)
      this_object.append(elemdict)
      p = True
  if not p:
    if element.keyword in ["leaf-list"]:
      create_list = True
    cls = "leaf"

    et = element.search_one('type')
    restricted = False

    if et.arg == "string":
      pattern = et.search_one('pattern')
      if not pattern == None:
        cls = "restricted-string"
        elemtype = {"native_type": """RestrictedClassType(base_type=%s, restriction_type="pattern",
                        restriction_arg="%s")""" % (class_map[et.arg]["native_type"], pattern.arg), \
                    "restriction_arg": pattern.arg, "restriction_type": "pattern", "parent_type": et.arg, \
                    "base_type": False}
        restricted = elemtype
        #default_type = class_map["string"][0]
      else:
        elemtype = class_map[et.arg]
        #default_type = et.arg
    elif et.arg in ["uint8", "uint16", "uint32"]:
      range_stmt = et.search_one('range')
      if not range_stmt == None:
        cls = "restricted-%s" % et.arg
        elemtype = {"native_type":  """RestrictedClassType(base_type=%s, restriction_type="range", 
                      restriction_arg="%s")"""  % (class_map[et.arg]["native_type"], range_stmt.arg), \
                    "restriction_arg": range_stmt.arg, "restriction_type": "range", "parent_type": et.arg, \
                    "base_type": False}
        #default_type = class_map[et.arg][0]
        restricted = elemtype
      else:
        elemtype = class_map[et.arg]
    else:
      try:
        elemtype = class_map[et.arg]
      except KeyError:
        print "FATAL: unmapped type (%s)" % et.arg
        import pprint
        pp = pprint.PrettyPrinter(indent=2)
        pp.pprint(class_map)
        sys.exit(127)

    elemdefault = element.search_one('default').arg if \
                                        element.search_one('default') else None
    found_native = False
    nested_default = False
    tmp_default = restricted if restricted else elemtype
    while not found_native:
      if not nested_default and "default" in tmp_default.keys():
        nested_default = tmp_default["default"]
      if not tmp_default["base_type"]:
        tmp_default = class_map[tmp_default["parent_type"]]
      else:
        tmp_default = tmp_default["native_type"]
        found_native = True
        break

    default_type = tmp_default
    if nested_default:
      elemdefault = nested_default

    elemconfig = class_bool_map[element.search_one('config').arg] if \
                                  element.search_one('config') else True

    elemname = safe_name(element.arg)
    if create_list:
      cls = "leaf-list"
      elemtype = ("TypedListType", elemtype["native_type"])
    else:
      elemtype = elemtype["native_type"]
    elemdict = {"name": elemname, "type": elemtype,
                        "origtype": element.search_one('type').arg, "path": safe_name(path),
                        "class": cls, "default": elemdefault,
                        "config": elemconfig, "defaulttype": default_type}
    this_object.append(elemdict)
  return this_object

