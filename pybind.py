"""
Copyright 2015, Rob Shakir (rjs@rob.sh)

This project has been supported by:
          * BT plc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import optparse
import sys
import re
import string
import numpy as np
import decimal
import copy
from bitarray import bitarray
from lib.yangtypes import safe_name

from pyang import plugin
from pyang import statements

DEBUG = True
if DEBUG:
  import pprint
  pp = pprint.PrettyPrinter(indent=2)

class YANGBool(int):
  def __new__(self, *args, **kwargs):
    false_args = ["false", "False", False, 0, "0"]
    true_args = ["true", "True", True, 1, "1"]
    if len(args):
      if not args[0] in false_args + true_args:
        raise ValueError("%s is an invalid value for a YANGBool" % args[0])
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
  'binary':           {"native_type": "bitarray", "base_type": True,
                          "quote_arg": True, "pytype": bitarray},
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
}

# all types that support range substmts
INT_RANGE_TYPES = ["uint8", "uint16", "uint32", "uint64",
                    "int8", "int16", "int32", "int64"]

def pyang_plugin_init():
    plugin.register_plugin(BTPyClass())

class BTPyClass(plugin.PyangPlugin):
    def add_output_format(self, fmts):
        self.multiple_modules = True
        fmts['pybind'] = self

    def emit(self, ctx, modules, fd):
        build_pybind(ctx, modules, fd)

    def add_opts(self, optparser):
      optlist = [
                  optparse.make_option("--use-xpathhelper",
                                       dest="use_xpathhelper",
                                       action="store_true",
                                       help="""Use the xpathhelper module to
                                               resolve leafrefs"""),
                ]
      g = optparser.add_option_group("pyangbind output specific options")
      g.add_options(optlist)


def build_pybind(ctx, modules, fd):

  # output the base code that we need to re-use with dynamically generated
  # objects.
  fd.write("from operator import attrgetter\n")
  if ctx.opts.use_xpathhelper:
    fd.write("import lib.xpathhelper as xpathhelper\n")
  fd.write("""from lib.yangtypes import RestrictedPrecisionDecimalType, RestrictedClassType, TypedListType\n""")
  fd.write("""from lib.yangtypes import YANGBool, YANGListType, YANGDynClass, ReferenceType\n""")
  fd.write("""from decimal import Decimal\n""")
  fd.write("""import numpy as np\n""")
  fd.write("""from bitarray import bitarray\n""")

  all_mods = []
  for module in modules:
    local_module_prefix = module.search_one('prefix')
    if local_module_prefix is None:
      local_module_prefix = module.search_one('belongs-to').search_one('prefix')
      if local_module_prefix is None:
        raise AttributeError("A module (%s) must have a prefix or parent module")
      local_module_prefix = local_module_prefix.arg
    else:
      local_module_prefix = local_module_prefix.arg
    mods = [(local_module_prefix,module)]
    for i in module.search('include'):
      subm = ctx.get_module(i.arg)
      if subm is not None:
        mods.append((local_module_prefix, subm))
    for j in module.search('import'):
      mod = ctx.get_module(j.arg)
      if mod is not None:
        imported_module_prefix = j.search_one('prefix').arg
        mods.append((imported_module_prefix, mod))
        modules.append(mod)
    all_mods.extend(mods)

  defn = {}
  for defnt in ['typedef', 'identity']:
    defn[defnt] = {}
    for m in all_mods:
      t = find_definitions(defnt, ctx, m[1], m[0])
      for k in t:
        if not k in defn[defnt]:
          defn[defnt][k] = t[k]

  build_identities(ctx, defn['identity'])
  build_typedefs(ctx, defn['typedef'])

  for module in modules:
    mods = [module]
    for i in module.search('include'):
      subm = ctx.get_module(i.arg)
      if subm is not None:
        mods.append(subm)

    for m in mods:
      children = [ch for ch in module.i_children
            if ch.keyword in statements.data_definition_keywords]
      get_children(ctx, fd, children, m, m)

def build_identities(ctx, defnd):
  unresolved_idc = {}
  for i in defnd:
    unresolved_idc[i] = 0
  unresolved_ids = defnd.keys()
  error_ids = []
  identity_d = {}

  while len(unresolved_ids):
    ident = unresolved_ids.pop(0)
    base = defnd[ident].search_one('base')
    if base is None:
      identity_d[ident] = {}
    else:
      if base.arg in identity_d:
        val = ident
        if ":" in ident:
          parts = ident.split(":")
          val = parts[1]
          pfx = parts[0]
          if "%s:%s" % (pfx, base.arg) in identity_d:
            identity_d["%s:%s" % (pfx, base.arg)][val] = {}
        if ":" in base.arg and base.arg.split(":")[1] in identity_d:
          identity_d[base.arg.split(":")[1]][val] = {}
        identity_d[base.arg][val] = {}
        # everything that is a value can also be a base
        if not val in identity_d:
          identity_d[val] = {}
      else:
        if unresolved_idc[ident] > 1000:
          # looked at this id a lot, it's a problem
          sys.stderr.write("could not find a match for %s base: %s\n" % (ident, base.arg))
          error_ids.append(ident)
        else:
          unresolved_ids.append(ident)
          unresolved_idc[ident] += 1

  # use keys() as the dictionary will change size when we
  # del an item.
  for potential_identity in identity_d.keys():
    if len(identity_d[potential_identity]) == 0:
      del identity_d[potential_identity]

  if error_ids:
    raise TypeError("could not resolve identities %s" % error_ids)

  for i in identity_d:
    id_type = {"native_type": """RestrictedClassType(base_type=str, restriction_type="dict_key", restriction_arg=%s,)""" % identity_d[i], \
                "restriction_argument": identity_d[i], \
                "restriction_type": "dict_key",
                "parent_type": "string",
                "base_type": False,}
    class_map[i] = id_type

def build_typedefs(ctx, defnd):
  unresolved_tc = {}
  for i in defnd:
    unresolved_tc[i] = 0
  unresolved_t = defnd.keys()
  error_ids = []
  known_types = class_map.keys()
  known_types.append('enumeration')
  known_types.append('leafref')
  process_typedefs_ordered = []
  while len(unresolved_t):

    t = unresolved_t.pop(0)
    base_t = defnd[t].search_one('type')
    if base_t.arg == "union":
      subtypes = [i for i in base_t.search('type')]
    elif base_t.arg == "identityref":
      subtypes = [base_t.search_one('base'),]
    else:
      subtypes = [base_t,]

    any_unknown = False
    for i in subtypes:
      if not i.arg in known_types:
        any_unknown=True
    if not any_unknown:
      process_typedefs_ordered.append((t, defnd[t]))
      known_types.append(t)
    else:
      unresolved_tc[t] += 1
      if unresolved_tc[t] > 1000:
        error_ids.append(t)
        sys.stderr.write("could not find a match for %s type -> %s\n" % (t,[i.arg for i in subtypes]))
      else:
        unresolved_t.append(t)

  if error_ids:
    raise TypeError("could not resolve typedefs %s" % error_ids)

  for i_tuple in process_typedefs_ordered:
    item = i_tuple[1]
    type_name = i_tuple[0]
    mapped_type = False
    restricted_arg = False
    cls,elemtype = copy.deepcopy(build_elemtype(ctx, item.search_one('type')))
    known_types = class_map.keys()
    # Enumeration is a native type, but is not natively supported
    # in the class_map, and hence we append it here.
    known_types.append("enumeration")
    known_types.append("leafref")

    if type_name in known_types:
      raise TypeError("Duplicate definition of %s" % type_name)
    default_stmt = item.search_one('default')
    if not isinstance(elemtype,list):
      restricted = False
      class_map[type_name] = {"base_type": False,}
      class_map[type_name]["native_type"] = elemtype["native_type"]
      if "parent_type" in elemtype:
        class_map[type_name]["parent_type"] = elemtype["parent_type"]
      else:
        yang_type = item.search_one('type').arg
        if not yang_type in known_types:
          raise TypeError("typedef specified a native type that was not " +
                            "supported")
        class_map[type_name]["parent_type"] = yang_type
      if default_stmt is not None:
        class_map[type_name]["default"] = default_stmt.arg
      if "referenced_path" in elemtype:
        class_map[type_name]["referenced_path"] = elemtype["referenced_path"]
        class_map[type_name]["class_override"] = "leafref"
      if "require_instance" in elemtype:
        class_map[type_name]["require_instance"] = elemtype["require_instance"]
      if "restriction_type" in elemtype:
        class_map[type_name]["restriction_type"] = \
                                              elemtype["restriction_type"]
        class_map[type_name]["restriction_argument"] = \
                                              elemtype["restriction_argument"]
      if "quote_arg" in elemtype:
        class_map[type_name]["quote_arg"] = elemtype["quote_arg"]
    else:
      native_type = []
      parent_type = []
      default = False if default_stmt is None else default_stmt.arg
      for i in elemtype:
        if isinstance(i[1]["native_type"], list):
          native_type.extend(i[1]["native_type"])
        else:
          native_type.append(i[1]["native_type"])
        if i[1]["yang_type"] in known_types:
          parent_type.append(i[1]["yang_type"])
        else:
          msg = "typedef in a union specified a native type that was not"
          msg += "supported (%s in %s)" % (i[1]["yang_type"], item.arg)
          raise TypeError(msg)
        if "default" in i[1] and not default:
          # we do strict ordering, so only the first default wins
          q = True if "quote_arg" in i[1] else False
          default = (i[1]["default"], q)
      class_map[type_name] = {"native_type": native_type, "base_type": False,
                              "parent_type": parent_type,}
      if default:
        class_map[type_name]["default"] = default[0]
        class_map[type_name]["quote_default"] = default[1]


def find_definitions(defn, ctx, module, prefix):
  mod = ctx.get_module(module.arg)
  if mod is None:
    raise AttributeError("expected to be able to find module %s, "+
                         "but could not" % (module.arg))
  type_definitions = {}
  for i in mod.search(defn):
    if i.arg in type_definitions:
      sys.stderr.write("WARNING: duplicate definition of %s" % i.arg)
    else:
      type_definitions["%s:%s" % (prefix, i.arg)] = i
      type_definitions[i.arg] = i
  return type_definitions

def get_children(ctx, fd, i_children, module, parent, path=str(), parent_cfg=True, choice=False):
  used_types,elements = [],[]
  choices = False

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

  for ch in i_children:
    if ch.keyword == "choice":
      for choice_ch in ch.i_children:
        # these are case statements
        for case_ch in choice_ch.i_children:
          elements += get_element(ctx, fd, case_ch, module, parent, path+"/"+ch.arg, parent_cfg=parent_cfg, choice=(ch.arg,choice_ch.arg))
    else:
      elements += get_element(ctx, fd, ch, module, parent, path+"/"+ch.arg, parent_cfg=parent_cfg, choice=choice)

  if parent.keyword in ["container", "module", "list", "submodule"]:
    if not path == "":
      fd.write("class yc_%s_%s_%s(object):\n" % (safe_name(parent.arg), \
        safe_name(module.arg), safe_name(path.replace("/", "_"))))
    else:
      fd.write("class %s(object):\n" % safe_name(parent.arg))

    keyval = False
    if parent.keyword == "list":
      keyval = parent.search_one('key').arg if parent.search_one('key') is not None else False
      if keyval and " " in keyval:
        keyval = keyval.split(" ")
      else:
        keyval = [keyval,]

    parent_descr = parent.search_one('description')
    if parent_descr is not None:
      parent_descr = "\n\n     YANG Description: %s" % parent_descr.arg.decode('utf8').encode('ascii', 'ignore')
    else:
      parent_descr = ""

    fd.write("""  \"\"\"
     This class was auto-generated by the PythonClass plugin for PYANG
     from YANG module %s - based on the path %s. Each member element of
     the container is represented as a class variable - with a specific
     YANG type.%s
    \"\"\"\n"""  % (module.arg, (path if not path == "" else "/%s" % parent.arg), \
                    parent_descr))
  else:
    raise TypeError("unhandled keyword with children %s" % parent.keyword)

  e_str = ""
  if len(elements) == 0:
    fd.write("  pass\n")
  else:
    # we want to prevent a user from creating new attributes on a class that
    # are not allowed within the data model
    e_str = "__elements = {"
    slots_str = "  __slots__ = ('_path_helper', "
    for i in elements:
      slots_str += "'__%s'," % i["name"]
      e_str +=  "'%s': %s, " % (i["name"], i["name"])
    slots_str += ")\n"
    e_str += "}\n"
    fd.write(slots_str)
    fd.write("\n")

    choices = {}
    choice_attrs = []
    classes = {}
    for i in elements:
      class_str = {}
      if "default" in i and not i["default"] is None:
        default_arg = repr(i["default"]) if i["quote_arg"] else "%s" \
                                    % i["default"]

      if i["class"] == "leaf-list":
        class_str["name"] = "__%s" % (i["name"])
        class_str["type"] = "YANGDynClass"
        class_str["arg"] = "base="
        if isinstance(i["type"]["native_type"][1], list):
          allowed_type = "["
          for subtype in i["type"]["native_type"][1]:
            allowed_type += "%s," % subtype
          allowed_type += "]"
        else:
          allowed_type = "%s" % (i["type"]["native_type"][1])
        class_str["arg"] += "%s(allowed_type=%s)" % (i["type"]["native_type"][0],allowed_type)
        if "default" in i and not i["default"] is None:
          class_str["arg"] += ", default=%s(%s)" % (i["defaulttype"], default_arg)
      elif i["class"] == "list":
        class_str["name"] = "__%s" % (i["name"])
        class_str["type"] = "YANGDynClass"
        class_str["arg"] = "base=YANGListType("
        class_str["arg"] += "%s,%s" % ("\"%s\"" % i["key"] if i["key"] else False, i["type"])
        class_str["arg"] += ", yang_name=\"%s\", parent=self, is_container=True" % (i["yang_name"])
        class_str["arg"] += ", user_ordered=%s" % i["user_ordered"]
        class_str["arg"] += ", path_helper=self._path_helper"
        if i["choice"]:
          class_str["arg"] += ", choice=%s" % repr(choice)
        class_str["arg"] += ")"
      elif i["class"] == "union" or i["class"] == "leaf-union":
        class_str["name"] = "__%s" % (i["name"])
        class_str["type"] = "YANGDynClass"
        class_str["arg"] = "base=["
        for u in i["type"][1]:
          if isinstance(u[1]["native_type"], list):
            for su_native_type in u[1]["native_type"]:
              class_str["arg"] += "%s," % su_native_type
          else:
            class_str["arg"] += "%s," % u[1]["native_type"]
        class_str["arg"] += "]"
        if "default" in i and not i["default"] is None:
          class_str["arg"] += ", default=%s(%s)" % (i["defaulttype"], default_arg)
      elif i["class"] == "leafref":
        class_str["name"] = "__%s" % (i["name"])
        class_str["type"] = "YANGDynClass"
        class_str["arg"] = "base=%s" % i["type"]
        class_str["arg"] += "(referenced_path='%s', caller='%s', " % (i["referenced_path"], path+"/"+i["yang_name"])
        class_str["arg"] += "path_helper=self._path_helper, "
        class_str["arg"] += "require_instance=%s)" % (i["require_instance"])
      else:
        class_str["name"] = "__%s" % (i["name"])
        class_str["type"] = "YANGDynClass"
        if isinstance(i["type"],list):
          class_str["arg"] = "base=["
          for u in i["type"]:
            class_str["arg"] += "%s," % u
          class_str["arg"] += "]"
        else:
          class_str["arg"] = "base=%s" % i["type"]
        if "default" in i and not i["default"] is None:
          class_str["arg"] += ", default=%s(%s)" % (i["defaulttype"], default_arg)
        if i["class"] in ["container", "list"]:
          class_str["arg"] += ", is_container=True"
        else:
          class_str["arg"] += ", is_leaf=True"
      if class_str["arg"]:
        class_str["arg"] += ", yang_name=\"%s\"" % i["yang_name"]
        class_str["arg"] += ", parent=self"
        if i["choice"]:
          class_str["arg"] += ", choice=%s" % repr(i["choice"])
          choice_attrs.append(i["name"])
          if not i["choice"][0] in choices:
            choices[i["choice"][0]] = {}
          if not i["choice"][1] in choices[i["choice"][0]]:
            choices[i["choice"][0]][i["choice"][1]] = []
          choices[i["choice"][0]][i["choice"][1]].append(i["name"])
        class_str["arg"] += ", path_helper=self._path_helper"
        #class_str += ", path='%s'" % (path+"/"+i["yang_name"])
        #class_str["arg"] += ")\n"
        classes[i["name"]] = class_str
        # TODO: NEED TO CLEAN UP HOW BASE ERRORS ARE REPORTED
        # WILL BE FIXED LATER.
    fd.write("""
  def __init__(self, *args, **kwargs):\n""")
    if path == "":
      if ctx.opts.use_xpathhelper:
        fd.write("""
    helper = kwargs.pop("path_helper", False)
    if helper and isinstance(helper, xpathhelper.YANGPathHelper):
      self._path_helper = helper
    else:
      self._path_helper = False\n""")
      else:
        fd.write("""
    self._path_helper = False\n""")
    for c in classes:
      fd.write("    self.%s = %s(%s)\n" % (classes[c]["name"], classes[c]["type"], classes[c]["arg"]))
    fd.write("""
    if args:
      if len(args) > 1:
        raise TypeError("cannot create a YANG container with >1 argument")
      all_attr = True
      for e in self.__elements:
        if not hasattr(args[0], e):
          all_attr = False
          break
      if not all_attr:
        raise ValueError("Supplied object did not have the correct attributes")
      for e in self.__elements:
        setattr(self, getattr(args[0], e))
""")
    if path == "":
      fd.write("""
  def path(self):
    return ""\n""")
    node = {}
    for i in elements:
      c_str = classes[i["name"]]
      description_str = ""
      if i["description"]:
        description_str = "\n\n      YANG Description: %s" % i["description"].decode('utf-8').encode('ascii', 'ignore')
      fd.write("""
  def _get_%s(self):
    \"\"\"
      Getter method for %s, mapped from YANG variable %s (%s)%s
    \"\"\"
    return self.__%s
      """ % (i["name"], i["name"], i["path"], i["origtype"],
             description_str, i["name"]))

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
      t = %s(v,%s)""" % (c_str["type"], c_str["arg"]))
      fd.write("""
    except (TypeError, ValueError):
      raise ValueError(\"\"\"%s must be of a type compatible with %s\"\"\")
    self.__%s = t\n""" % (i["name"], c_str["arg"], i["name"]))
      fd.write("    self.set()\n")

      if i["name"] in choice_attrs:
        fd.write("""
  def _unset_%s(self):
    self.__%s = %s(%s)\n\n""" % (i["name"], i["name"], c_str["type"], c_str["arg"],))
    for i in elements:
      rw = True
      if not i["config"]:
        rw = False
      elif not parent_cfg:
        rw = False
      elif keyval and i["yang_name"] in keyval:
        rw = False

      if not rw:
        fd.write("""  %s = property(_get_%s)\n""" % (i["name"], i["name"]))
      else:
        fd.write("""  %s = property(_get_%s, _set_%s)\n""" % \
                          (i["name"], i["name"], i["name"]))
  fd.write("\n")
  if choices:
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
    for element_name in self.__elements:
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
            for entry in d[element_id]:
              if hasattr(d[element_id][entry], "changed"):
                if not d[element_id][entry].changed():
                  del d[element_id][entry]
            if len(d[element_id]) == 0:
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

def build_elemtype(ctx, et, prefix=False):
  cls = None

  pattern_stmt =  et.search_one('pattern') if not et.search_one('pattern') is None else False
  range_stmt = et.search_one('range') if not et.search_one('range') is None else False
  length_stmt = et.search_one('length') if not et.search_one('length') is None else False

  restrictions = {}

  if pattern_stmt:
    restrictions['pattern'] = pattern_stmt.arg

  if length_stmt:
    restrictions['length'] = length_stmt.arg

  if range_stmt:
    restrictions['range'] = range_stmt.arg

  if len(restrictions):
    if 'length' in restrictions or 'pattern' in restrictions:
      cls = "restricted-%s" % (et.arg)
      elemtype = {
                    "native_type": """RestrictedClassType(base_type=%s, restriction_dict=%s)"""
                      % (class_map[et.arg]["native_type"], repr(restrictions)),
                    "restriction_dict": restrictions,
                    "parent_type": et.arg,
                    "base_type": False,
                  }
    elif 'range' in restrictions:
      cls = "restricted-%s" % et.arg
      elemtype = {
                    "native_type": """RestrictedClassType(base_type=%s, restriction_dict=%s)"""
                      % (class_map[et.arg]["native_type"], repr(restrictions)),
                    "restriction_dict": restrictions,
                    "parent_type": et.arg,
                    "base_type": False,
      }

  if cls is None:
    cls = "leaf"
    if et.arg == "enumeration":
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
                  "restriction_argument": enumeration_dict, \
                  "restriction_type": "dict_key", \
                  "parent_type": "string", \
                  "base_type": False,}
    elif et.arg == "decimal64":
      fd_stmt = et.search_one('fraction-digits')
      if not fd_stmt is None:
        cls = "restricted-decimal64"
        elemtype = {"native_type": \
                      """RestrictedPrecisionDecimalType(precision=%s)""" % \
                      fd_stmt.arg, "base_type": False, \
                      "parent_type": "decimal64",}
      else:
        elemtype = class_map[et.arg]
    elif et.arg == "union":
      elemtype = []
      for uniontype in et.search('type'):
        elemtype_s = copy.deepcopy(build_elemtype(ctx, uniontype))
        elemtype_s[1]["yang_type"] = uniontype.arg
        elemtype.append(elemtype_s)
      cls = "union"
    elif et.arg == "leafref":
      path_stmt = et.search_one('path')
      if path_stmt is None:
        raise ValueError("leafref specified with no path statement")
      require_instance = class_bool_map[et.search_one('require-instance').arg] if et.search_one('require-instance') \
                            is not None else False
      if ctx.opts.use_xpathhelper:
        elemtype = {"native_type": "ReferenceType",
                    "referenced_path": path_stmt.arg,
                    "parent_type": "string",
                    "base_type": False,
                    "require_instance": require_instance}
        cls = "leafref"
      else:
        elemtype = {
                    "native_type": "str",
                    "parent_type": "string",
                    "base_type": False,
                   }
    elif et.arg == "identityref":
      base_stmt = et.search_one('base')
      if base_stmt is None:
        raise ValueError("identityref specified with no base statement")
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
    if isinstance(elemtype, list):
      cls = "leaf-union"
    elif "class_override" in elemtype:
      # this is used to propagate the fact that in some cases the
      # native type needs to be dynamically built (e.g., leafref)
      cls = elemtype["class_override"]
  return (cls,elemtype)


def get_element(ctx, fd, element, module, parent, path, parent_cfg=True,choice=False):
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
    else:
      npath=path
    if element.i_children:
      chs = element.i_children
      get_children(ctx, fd, chs, module, element, npath, parent_cfg=parent_cfg, choice=choice)
      elemdict = {"name": safe_name(element.arg), "origtype": element.keyword,
                          "type": "yc_%s_%s_%s" % (safe_name(element.arg),
                          safe_name(module.arg), safe_name(path.replace("/", "_"))),
                          "class": element.keyword,
                          "path": safe_name(npath), "config": True,
                          "description": elemdescr,
                          "yang_name": element.arg,
                          "choice": choice,
                 }
      if element.keyword == "list":
        elemdict["key"] = safe_name(element.search_one("key").arg) if element.search_one("key") is not None else False
        user_ordered = element.search_one('ordered-by')
        elemdict["user_ordered"] = True if user_ordered is not None \
          and user_ordered.arg.upper() == "USER" else False
      this_object.append(elemdict)
      p = True
  if not p:
    if element.keyword in ["leaf-list"]:
      create_list = True
    cls,elemtype = copy.deepcopy(build_elemtype(ctx, element.search_one('type')))

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
        if "default" in i[1]:
          elemdefault = i[1]["default"]
          default_type = i[1]
          #default_type = i[1]
          #mapped_elemtype = i[1]
    elif "default" in elemtype:
      # if the actual type defines the default, then we need to maintain
      # this
      elemdefault = elemtype["default"]
      default_type = elemtype

    # we need to indicate that the default type for the class_map
    # is str
    tmp_class_map = copy.deepcopy(class_map)
    tmp_class_map["enumeration"] = {"parent_type": "string"}
    # TODO: add leafref

    if not default_type:
      if isinstance(elemtype, list):
        # this type has multiple parents
        for i in elemtype:
          if "parent_type" in i[1]:
            if isinstance(i[1]["parent_type"], list):
              to_visit = [j for j in i[1]["parent_type"]]
            else:
              to_visit = [i[1]["parent_type"],]
      elif "parent_type" in elemtype:
        if isinstance(elemtype["parent_type"], list):
          to_visit = [i for i in elemtype["parent_type"]]
        else:
          to_visit = [elemtype["parent_type"],]

        checked = list()
        while to_visit:
          check = to_visit.pop(0)
          if check not in checked:
            checked.append(check)
            if "parent_type" in tmp_class_map[check]:
              if isinstance(tmp_class_map[check]["parent_type"], list):
                to_visit.extend(tmp_class_map[check]["parent_type"])
              else:
                to_visit.append(tmp_class_map[check]["parent_type"])

        # checked now has the breadth-first search result
        if elemdefault is None:
          for option in checked:
            if "default" in tmp_class_map[option]:
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
        if "parent_type" in default_type:
          if isinstance(default_type["parent_type"], list):
            to_visit = [i for i in default_type["parent_type"]]
          else:
            to_visit = [default_type["parent_type"],]
        checked = list()
        while to_visit:
          check = to_visit.pop(0) # remove from the top of stack - depth first
          if not check in checked:
            checked.append(check)
            if "parent_type" in tmp_class_map[check]:
              if isinstance(tmp_class_map[check]["parent_type"], list):
                to_visit.expand(tmp_class_map[check]["parent_type"])
              else:
                to_visit.append(tmp_class_map[check]["parent_type"])
        default_type = tmp_class_map[checked.pop()]
        if not default_type["base_type"]:
          raise TypeError("default type was not a base type")

    if default_type:
      quote_arg = default_type["quote_arg"] if "quote_arg" in \
                    default_type else False
      default_type = default_type["native_type"]

    elemconfig = class_bool_map[element.search_one('config').arg] if \
                                  element.search_one('config') else True

    elemname = safe_name(element.arg)
    # if "referenced_path" in elemtype:
    #   referenced_path = elemtype["referenced_path"]

    if create_list:
      cls = "leaf-list"
      if isinstance(elemtype, list):
        c = 0
        allowed_types = []
        for subtype in elemtype:
          # nested union within a leaf-list type
          if isinstance(subtype, tuple):
            if subtype[0] == "leaf-union":
              for subelemtype in subtype[1]["native_type"]:
                allowed_types.append(subelemtype)
            else:
              if isinstance(subtype[1]["native_type"], list):
                allowed_types.extend(subtype[1]["native_type"])
              else:
                allowed_types.append(subtype[1]["native_type"])
          else:
            allowed_types.append(subtype["native_type"])
      else:
        allowed_types = elemtype["native_type"]

      elemntype = {"class": cls, "native_type": ("TypedListType", \
                  allowed_types)}
    else:
      if cls == "union" or cls == "leaf-union":
        elemtype = {"class": cls, "native_type": ("UnionType", elemtype)}
      elemntype = elemtype["native_type"]

    elemdict = {"name": elemname, "type": elemntype,
                        "origtype": element.search_one('type').arg, "path": \
                        safe_name(path),
                        "class": cls, "default": elemdefault, \
                        "config": elemconfig, "defaulttype": default_type, \
                        "quote_arg": quote_arg, \
                        "description": elemdescr, "yang_name": element.arg,
                        "choice": choice,
               }
    if cls == "leafref":
      elemdict["referenced_path"] = elemtype["referenced_path"]
      elemdict["require_instance"] = elemtype["require_instance"]
    this_object.append(elemdict)
  return this_object

