"""
Copyright 2015, Rob Shakir (rjs@jive.com, rjs@rob.sh)

Modifications copyright 2016, Google Inc.

This project has been supported by:
          * Google, Inc.
          * Jive Communications, Inc.
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
import decimal
import copy
import os
from bitarray import bitarray
from pyangbind.lib.yangtypes import safe_name, YANGBool, \
                                  RestrictedClassType
from pyangbind.helpers.identity import IdentityStore
import pyangbind.helpers.misc as misc_help

from pyang import plugin
from pyang import statements
from pyang import util

DEBUG = True
if DEBUG:
  import pprint
  pp = pprint.PrettyPrinter(indent=2)

# YANG is quite flexible in terms of what it allows as input to a boolean
# value, this map is used to provide a mapping of these values to the python
# True and False boolean instances.
class_bool_map = {
    'false': False,
    'False': False,
    'true': True,
    'True': True,
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
    # base_type:          whether the class can be used as
    #                     class(*args, **kwargs) in Python, or whether it is a
    #                     derived class (such as is created based on a typedef,
    #                     or for types that cannot be supported natively, such
    #                     as enumeration, or a string
    #                     with a restriction placed on it)
    # quote_arg (opt):    whether the argument to this class' __init__ needs to
    #                     be quoted (e.g., str("hello")) in the code that is
    #                     output.
    # pytype (opt):       A reference to the actual type that is used, this is
    #                     used where we infer types, such as for an input
    #                     value to a union since we need to actually compare
    #                     the value against the __init__ method and see whether
    #                     it works.
    # parent_type (opt):  for "derived" types, then we store what the enclosed
    #                     type is such that we can create instances where
    #                     required e.g., a restricted string will have a
    #                     parent_type of a string. this can be a list if the
    #                     type is a union.
    # restriction ...:    where the type is a restricted type, then the
    # (optional)          class_map dict entry can store more information about
    #                     the type of restriction. this is generally used when
    #                     we need to re-initialise an instance of the class,
    #                     such as in the setter methods of containers.
    # Other types may add their own types to this dictionary that have
    # meaning only for themselves. For example, a ReferenceType can add the
    # path it references, and whether the require-instance keyword was set
    # or not.
    #
    'boolean': {
        "native_type": "YANGBool",
        "map": class_bool_map,
        "base_type": True,
        "quote_arg": True,
        "pytype": YANGBool
    },
    'binary': {
        "native_type": "bitarray",
        "base_type": True,
        "quote_arg": True,
        "pytype": bitarray
    },
    'uint8': {
        "native_type": ("RestrictedClassType(base_type=int," +
                       " restriction_dict={'range': ['0..255']}, int_size=8)"),
        "base_type": True,
        "pytype": RestrictedClassType(base_type=int,
                    restriction_dict={'range': ['0..255']}, int_size=8)
    },
    'uint16': {
        "native_type": ("RestrictedClassType(base_type=int," +
                       " restriction_dict={'range': ['0..65535']}," +
                       "int_size=16)"),
        "base_type": True,
        "pytype": RestrictedClassType(base_type=int,
                    restriction_dict={'range': ['0..65535']}, int_size=16)
    },
    'uint32': {
        "native_type": ("RestrictedClassType(base_type=long," +
                        " restriction_dict={'range': ['0..4294967295']}," +
                        " int_size=32)"),
        "base_type": True,
        "pytype": RestrictedClassType(base_type=long,
                    restriction_dict={'range': ['0..4294967295']}, int_size=32)
    },
    'uint64': {
        "native_type": ("RestrictedClassType(base_type=long, " +
                       "restriction_dict={'range': " +
                       " ['0..18446744073709551615']}, int_size=64)"),
        "base_type": True,
        "pytype": RestrictedClassType(base_type=long,
                    restriction_dict={'range': ['0..18446744073709551615']},
                    int_size=64)
    },
    'string': {
        "native_type": "unicode",
        "base_type": True,
        "quote_arg": True,
        "pytype": unicode
    },
    'decimal64': {
        "native_type": "Decimal",
        "base_type": True,
        "pytype": decimal.Decimal
    },
    'empty': {
        "native_type": "YANGBool",
        "map": class_bool_map,
        "base_type": True,
        "quote_arg": True,
        "pytype": YANGBool
    },
    'int8': {
        "native_type": "RestrictedClassType(base_type=int, "+
                      "restriction_dict={'range': ['-128..127']}, int_size=8)",
        "base_type": True,
        "pytype": RestrictedClassType(base_type=int,
                    restriction_dict={'range': ['-128..127']}, int_size=8)
    },
    'int16': {
        "native_type": ("RestrictedClassType(base_type=int,"
                       "restriction_dict={'range': ['-32768..32767']}, " +
                       "int_size=16)"),
        "base_type": True,
        "pytype": RestrictedClassType(base_type=int,
                    restriction_dict={'range': ['-32768..32767']}, int_size=16)
    },
    'int32': {
        "native_type": ("RestrictedClassType(base_type=long," +
                        " restriction_dict={'range': " +
                        "['-2147483648..2147483647']}, int_size=32)"),
        "base_type": True,
        "pytype": RestrictedClassType(base_type=long,
                    restriction_dict={'range': ['-2147483648..2147483647']},
                    int_size=32)
    },
    'int64': {
        "native_type": ("RestrictedClassType(base_type=long, " +
                       "restriction_dict={'range': " +
                       "['-9223372036854775808..9223372036854775807']}, " +
                       "int_size=64)"),
        "base_type": True,
        "pytype": RestrictedClassType(base_type=long,
                    restriction_dict={'range':
                    ['-9223372036854775808..9223372036854775807']}, int_size=64)
    },
}

# We have a set of types which support "range" statements in RFC6020. This
# list determins types that should be allowed to have a "range" argument.
INT_RANGE_TYPES = ["uint8", "uint16", "uint32", "uint64",
                    "int8", "int16", "int32", "int64"]

# The types that are built-in to YANG
YANG_BUILTIN_TYPES = class_map.keys() + \
                      ["container", "list", "rpc", "notification", "leafref"]


# Base machinery to support operation as a plugin to pyang.
def pyang_plugin_init():
    plugin.register_plugin(PyangBindClass())


class PyangBindClass(plugin.PyangPlugin):
    def add_output_format(self, fmts):
      # Add the 'pybind' output format to pyang.
      self.multiple_modules = True
      fmts['pybind'] = self

    def emit(self, ctx, modules, fd):
      # When called, call the build_pyangbind function.
      build_pybind(ctx, modules, fd)

    def add_opts(self, optparser):
      # Add pyangbind specific operations to pyang. These are documented in the
      # options, but are essentially divided into three sets.
      #   * xpathhelper - How pyangbind should deal with xpath expressions.
      #     This module is documented in lib/xpathhelper and describes how
      #     to support registration, updates, and retrieval of xpaths.
      #   * class output - whether a single file should be created, or whether
      #     a hierarchy of python modules should be created. The latter is
      #     preferable when one has large trees being compiled.
      #   * extensions - support for YANG extensions that pyangbind should look
      #     for, and add as a dictionary with each element.
      optlist = [
          optparse.make_option("--use-xpathhelper",
                               dest="use_xpathhelper",
                               action="store_true",
                               help="""Use the xpathhelper module to
                                       resolve leafrefs"""),
          optparse.make_option("--split-class-dir",
                               metavar="DIR",
                               dest="split_class_dir",
                               help="""Split the code output into
                                       multiple directories"""),
          optparse.make_option("--interesting-extension",
                              metavar="EXTENSION-MODULE",
                              default=[],
                              action="append",
                              type=str,
                              dest="pybind_interested_exts",
                              help="""A set of extensions that
                                      are interesting and should be
                                      stored with the class. They
                                      can be accessed through the
                                      "extension_dict()" argument.
                                      Multiple arguments can be
                                      specified."""),
          optparse.make_option("--use-extmethods",
                              dest="use_extmethods",
                              action="store_true",
                              help="""Allow a path-keyed dictionary
                                      to be used to specify methods
                                      related to a particular class"""),
          optparse.make_option("--build-rpcs",
                              dest="build_rpcs",
                              action="store_true",
                              help="""Generate class bindings for
                                      the input and output of RPCs
                                      defined in each module. These
                                      are placed at the root of
                                      each module"""),
          optparse.make_option("--presence",
                                dest="generate_presence",
                                action="store_true",
                                help="""Capture whether the presence
                                        keyword is used in the generated
                                        code."""),
          optparse.make_option("--build-notifications",
                              dest="build_notifications",
                              action="store_true",
                              help="""Generate class bindings for
                                      notifications defined in each
                                      module. These are placed at
                                      the root of each module"""),
      ]
      g = optparser.add_option_group("pyangbind output specific options")
      g.add_options(optlist)


# Core function to build the pyangbind output - starting with building the
# dependencies - and then working through the instantiated tree that pyang has
# already parsed.
def build_pybind(ctx, modules, fd):
  # Restrict the output of the plugin to only the modules that are supplied
  # to pyang. More modules are parsed by pyangbind to resolve typedefs and
  # identities.
  module_d = {}
  for mod in modules:
    module_d[mod.arg] = mod
  pyang_called_modules = module_d.keys()

  # Bail if there are pyang errors, since this certainly means that the
  # pyangbind output will fail - unless these are solely due to imports that
  # we provided but then unused.
  if len(ctx.errors):
    for e in ctx.errors:
      print "INFO: encountered %s" % str(e)
      if not e[1] in ["UNUSED_IMPORT", "PATTERN_ERROR"]:
        sys.stderr.write("FATAL: pyangbind cannot build module that pyang" +
          " has found errors with.\n")
        sys.exit(127)

  # Build the common set of imports that all pyangbind files needs
  ctx.pybind_common_hdr = ""
  ctx.pybind_common_hdr += "\n"

  ctx.pybind_common_hdr += "from operator import attrgetter\n"
  if ctx.opts.use_xpathhelper:
    ctx.pybind_common_hdr += "import pyangbind.lib.xpathhelper as " + \
                                "xpathhelper\n"
  ctx.pybind_common_hdr += """from pyangbind.lib.yangtypes import """
  ctx.pybind_common_hdr += """RestrictedPrecisionDecimalType, """
  ctx.pybind_common_hdr += """RestrictedClassType, TypedListType\n"""
  ctx.pybind_common_hdr += """from pyangbind.lib.yangtypes import YANGBool, """
  ctx.pybind_common_hdr += """YANGListType, YANGDynClass, ReferenceType\n"""
  ctx.pybind_common_hdr += """from pyangbind.lib.base import PybindBase\n"""
  ctx.pybind_common_hdr += """from decimal import Decimal\n"""
  ctx.pybind_common_hdr += """from bitarray import bitarray\n"""
  ctx.pybind_common_hdr += """import __builtin__\n"""

  if not ctx.opts.split_class_dir:
    fd.write(ctx.pybind_common_hdr)
  else:
    ctx.pybind_split_basepath = os.path.abspath(ctx.opts.split_class_dir)
    if not os.path.exists(ctx.pybind_split_basepath):
      os.makedirs(ctx.pybind_split_basepath)

  # Determine all modules, and submodules that are needed, along with the
  # prefix that is used for it. We need to ensure that we understand all of the
  # prefixes that might be used to reference an identity or a typedef.
  all_mods = []
  for module in modules:
    local_module_prefix = module.search_one('prefix')
    if local_module_prefix is None:
      local_module_prefix = \
          module.search_one('belongs-to').search_one('prefix')
      if local_module_prefix is None:
        raise AttributeError("A module (%s) must have a prefix or parent " +
          "module")
      local_module_prefix = local_module_prefix.arg
    else:
      local_module_prefix = local_module_prefix.arg
    mods = [(local_module_prefix, module)]

    imported_modules = module.search('import')

    # 'include' statements specify the submodules of the existing module -
    # that also need to be parsed.
    for i in module.search('include'):
      subm = ctx.get_module(i.arg)
      if subm is not None:
        mods.append((local_module_prefix, subm))
        # Handle the case that imports are within a submodule
        if subm.search('import') is not None:
          imported_modules.extend(subm.search('import'))

    # 'import' statements specify the other modules that this module will
    # reference.
    for j in imported_modules:
      mod = ctx.get_module(j.arg)
      if mod is not None:
        imported_module_prefix = j.search_one('prefix').arg
        mods.append((imported_module_prefix, mod))
        modules.append(mod)
    all_mods.extend(mods)


  # remove duplicates from the list (same module and prefix)
  new_all_mods = []
  for mod in all_mods:
    if mod not in new_all_mods:
      new_all_mods.append(mod)
  all_mods = new_all_mods

  # Build a list of the 'typedef' and 'identity' statements that are included
  # in the modules supplied.
  defn = {}
  for defnt in ['typedef', 'identity']:
    defn[defnt] = {}
    for m in all_mods:
      t = misc_help.find_definitions(defnt, ctx, m[1], m[0])
      for k in t:
        if k not in defn[defnt]:
          defn[defnt][k] = t[k]

  # Build the identities and typedefs (these are added to the class_map which
  # is globally referenced).
  build_identities(ctx, defn['identity'])
  build_typedefs(ctx, defn['typedef'])

  # Iterate through the tree which pyang has built, solely for the modules
  # that pyang was asked to build
  for modname in pyang_called_modules:
    module = module_d[modname]
    mods = [module]
    for i in module.search('include'):
      subm = ctx.get_module(i.arg)
      if subm is not None:
        mods.append(subm)
    for m in mods:
      children = [ch for ch in module.i_children
            if ch.keyword in statements.data_definition_keywords]
      get_children(ctx, fd, children, m, m)

      if ctx.opts.build_rpcs:
        rpcs = [ch for ch in module.i_children
                  if ch.keyword == 'rpc']
        # Build RPCs specifically under the module name, since this
        # can be used as a proxy for the namespace.
        if len(rpcs):
          get_children(ctx, fd, rpcs, module, module, register_paths=False,
                      path="/%s_rpc" % (safe_name(module.arg)))

      if ctx.opts.build_notifications:
        notifications = [ch for ch in module.i_children
                  if ch.keyword == 'notification']
        # Build notifications specifically under the module name,
        # since this can be used as a proxy for the namespace.
        if len(notifications):
          get_children(ctx, fd, notifications, module, module, register_paths=False,
                      path="/%s_notification" % (safe_name(module.arg)))

def build_identities(ctx, defnd):
  # Build a storage object that has all the definitions that we
  # require within it.
  idstore = IdentityStore()
  idstore.build_store_from_definitions(ctx, defnd)

  identity_dict = {}
  for identity in idstore:
    for prefix in identity.prefixes():
      ident = "%s:%s" % (prefix, identity.name)
      identity_dict[ident] = {}
      identity_dict["%s" % identity.name] = {}
      for ch in identity.children:
        d = {"@module": ch.source_module, "@namespace": ch.source_namespace}
        for cpfx in ch.prefixes() + [None]:
          if cpfx is not None:
            spfx = "%s:" % cpfx
          else:
            spfx = ""
          identity_dict[ident][ch.name] = d
          identity_dict[identity.name][ch.name] = d
          identity_dict[ident]["%s%s" % (spfx, ch.name)] = d
          identity_dict[identity.name]["%s%s" % (spfx, ch.name)] = d

    if not identity.name in identity_dict:
      identity_dict[identity.name] = {}

  # Add entries to the class_map such that this identity can be referenced by
  # elements that use this identity ref.
  for i in identity_dict:
    id_type = {"native_type": """RestrictedClassType(base_type=unicode, """ +
                              """restriction_type="dict_key", """ +
                              """restriction_arg=%s,)""" % identity_dict[i],
                "restriction_argument": identity_dict[i],
                "restriction_type": "dict_key",
                "parent_type": "string",
                "base_type": False}
    class_map[i] = id_type

def build_typedefs(ctx, defnd):
  # Build the type definitions that are specified within a model. Since
  # typedefs are essentially derived from existing types, order of processing
  # is important - we need to go through and build the types in order where
  # they have a known 'type'.
  unresolved_tc = {}
  for i in defnd:
    unresolved_tc[i] = 0
  unresolved_t = defnd.keys()
  error_ids = []
  known_types = class_map.keys()
  known_types.append('enumeration')
  known_types.append('leafref')
  base_types = copy.deepcopy(known_types)
  process_typedefs_ordered = []

  while len(unresolved_t):
    t = unresolved_t.pop(0)
    base_t = defnd[t].search_one('type')
    if base_t.arg == "union":
      subtypes = []
      for i in base_t.search('type'):
        if i.arg == "identityref":
          subtypes.append(i.search_one('base'))
        else:
          subtypes.append(i)
    elif base_t.arg == "identityref":
      subtypes = [base_t.search_one('base')]
    else:
      subtypes = [base_t]

    any_unknown = False
    for i in subtypes:
      # Resolve this typedef to the module that it
      # was defined by

      if ":" in i.arg:
        defining_module = util.prefix_to_module(defnd[t].i_module,
                           i.arg.split(":")[0], defnd[t].pos, ctx.errors)
      else:
        defining_module = defnd[t].i_module

      belongs_to = defining_module.search_one('belongs-to') 
      if belongs_to is not None:
        for mod in ctx.modules:
          if mod[0] == belongs_to.arg:
            defining_module = ctx.modules[mod]

      real_pfx = defining_module.search_one('prefix').arg

      if ":" in i.arg:
        tn = u"%s:%s" % (real_pfx, i.arg.split(":")[1])
      elif i.arg not in base_types:
        # If this was not a base type (defined in YANG) then resolve it
        # to the module it belongs to.
        tn = u"%s:%s" % (real_pfx, i.arg)
      else:
        tn = i.arg

      if tn not in known_types:
        any_unknown = True

    if not any_unknown:
      process_typedefs_ordered.append((t, defnd[t]))
      known_types.append(t)
    else:
      unresolved_tc[t] += 1
      if unresolved_tc[t] > 1000:
        # Take a similar approach to the resolution of identities. If we have a
        # typedef that has a type in it that is not found after many iterations
        # then we should bail.
        error_ids.append(t)
        sys.stderr.write("could not find a match for %s type -> %s\n" %
          (t, [i.arg for i in subtypes]))
      else:
        unresolved_t.append(t)

  if error_ids:
    raise TypeError("could not resolve typedefs %s" % error_ids)

  # Process the types that we built above.
  for i_tuple in process_typedefs_ordered:
    item = i_tuple[1]
    type_name = i_tuple[0]
    mapped_type = False
    restricted_arg = False
    # Copy the class_map entry - this is done so that we do not alter the
    # existing instance in memory as we add to it.
    cls, elemtype = copy.deepcopy(build_elemtype(ctx, item.search_one('type')))
    known_types = class_map.keys()
    # Enumeration is a native type, but is not natively supported
    # in the class_map, and hence we append it here.
    known_types.append("enumeration")
    known_types.append("leafref")

    # Don't allow duplicate definitions of types
    if type_name in known_types:
      raise TypeError("Duplicate definition of %s" % type_name)
    default_stmt = item.search_one('default')

    # 'elemtype' is a list when the type includes a union, so we need to go
    # through and build a type definition that supports multiple types.
    if not isinstance(elemtype, list):
      restricted = False
      # Map the original type to the new type, parsing the additional arguments
      # that may be specified, for example, a new default, a pattern that must
      # be matched, or a length (stored in the restriction_argument, and
      # restriction_type class_map variables).
      class_map[type_name] = {"base_type": False}
      class_map[type_name]["native_type"] = elemtype["native_type"]
      if "parent_type" in elemtype:
        class_map[type_name]["parent_type"] = elemtype["parent_type"]
      else:
        yang_type = item.search_one('type').arg
        if yang_type not in known_types:
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
      # Handle a typedef that is a union - extended the class_map arguments
      # to be a list that is parsed by the relevant dynamic type generation
      # function.
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
        elif i[1]["yang_type"] == "identityref":
          parent_type.append(i[1]["parent_type"])
        else:
          msg = "typedef in a union specified a native type that was not"
          msg += " supported (%s in %s)" % (i[1]["yang_type"], item.arg)
          raise TypeError(msg)

        if "default" in i[1] and not default:
          # When multiple 'default' values are specified within a union that
          # is within a typedef, then pyangbind will choose the first one.
          q = True if "quote_arg" in i[1] else False
          default = (i[1]["default"], q)
      class_map[type_name] = {"native_type": native_type, "base_type": False,
                              "parent_type": parent_type}
      if default:
        class_map[type_name]["default"] = default[0]
        class_map[type_name]["quote_default"] = default[1]

    class_map[type_name.split(":")[1]] = class_map[type_name]

def get_children(ctx, fd, i_children, module, parent, path=str(),
                 parent_cfg=True, choice=False, register_paths=True):

  # Iterative function that is called for all elements that have childen
  # data nodes in the tree. This function resolves those nodes into the
  # relevant leaf, or container/list configuration and outputs the python
  # code that corresponds to it to the relevant file. parent_cfg is used to
  # ensure that where a parent container was set to config false, this is
  # inherited by all elements below it; and choice is used to store whether
  # these leaves are within a choice or not.
  used_types, elements = [], []
  choices = False

  # When pyangbind was asked to split classes, then we need to create the
  # relevant directories for the modules to be created into. In this case
  # even though fd might be a valid file handle, we ignore it.
  if ctx.opts.split_class_dir:
    if path == "":
      fpath = ctx.pybind_split_basepath + "/__init__.py"
    else:
      pparts = path.split("/")
      npath = "/"

      # Check that we don't have the problem of containers that are nested
      # with the same name
      for i in range(1, len(pparts)):
        if i > 0 and pparts[i] == pparts[i - 1]:
          pname = safe_name(pparts[i]) + "_"
        elif i == 1 and pparts[i] == module.arg:
          pname = safe_name(pparts[i]) + "_"
        else:
          pname = safe_name(pparts[i])
        npath += pname + "/"

      bpath = ctx.pybind_split_basepath + npath
      if not os.path.exists(bpath):
        os.makedirs(bpath)
      fpath = bpath + "/__init__.py"
    if not os.path.exists(fpath):
      try:
        nfd = open(fpath, 'w')
      except IOError, m:
        raise IOError("could not open pyangbind output file (%s)" % m)
      nfd.write(ctx.pybind_common_hdr)
    else:
      try:
        nfd = open(fpath, 'a')
      except IOError, w:
        raise IOError("could not open pyangbind output file (%s)" % m)
  else:
    # If we weren't asked to split the files, then just use the file handle
    # provided.
    nfd = fd

  if parent_cfg:
    # The first time we find a container that has config false set on it
    # then we need to hand this down the tree - we don't need to look if
    # parent_cfg has already been set to False as we need to inherit.
    parent_config = parent.search_one('config')
    if parent_config is not None:
      parent_config = parent_config.arg
      if parent_config.upper() == "FALSE":
        # this container is config false
        parent_cfg = False

  # When we are asked to split the classes into modules, then we need to find
  # all elements that have their own class within this container, and make sure
  # that they are imported. Additionally, we need to find the elements that are
  # within a case, and ensure that these are built with the corresponding
  # choice specified.
  if ctx.opts.split_class_dir:
    import_req = []

  for ch in i_children:
    children_tmp = getattr(ch, "i_children", None)
    if children_tmp is not None:
      children_tmp = [i.arg for i in children_tmp]
    if ch.keyword == "choice":
      for choice_ch in ch.i_children:
        # these are case statements
        for case_ch in choice_ch.i_children:
          elements += get_element(ctx, fd, case_ch, module, parent,
            path + "/" + case_ch.arg, parent_cfg=parent_cfg,
            choice=(ch.arg, choice_ch.arg), register_paths=register_paths)
          if ctx.opts.split_class_dir:
            if hasattr(case_ch, "i_children") and len(case_ch.i_children):
              import_req.append(case_ch.arg)
    else:
      elements += get_element(ctx, fd, ch, module, parent, path + "/" + ch.arg,
        parent_cfg=parent_cfg, choice=choice, register_paths=register_paths)

      if ctx.opts.split_class_dir:
        if hasattr(ch, "i_children") and len(ch.i_children):
          import_req.append(ch.arg)

  # Write out the import statements if needed.
  if ctx.opts.split_class_dir:
    if len(import_req):
      for im in import_req:
        if im == parent.arg:
          im += "_"
        nfd.write("""import %s\n""" % safe_name(im))

  # 'container', 'module', 'list' and 'submodule' all have their own classes
  # generated.
  if parent.keyword in ["container", "module", "list", "submodule", "input",
                         "output", "rpc", "notification"]:
    if ctx.opts.split_class_dir:
      nfd.write("class %s(PybindBase):\n" % safe_name(parent.arg))
    else:
      if not path == "":
        nfd.write("class yc_%s_%s_%s(PybindBase):\n" % (safe_name(parent.arg),
          safe_name(module.arg), safe_name(path.replace("/", "_"))))
      else:
        nfd.write("class %s(PybindBase):\n" % safe_name(parent.arg))

    # If the container is actually a list, then determine what the key value
    # is and store this such that we can give a hint.
    keyval = False
    if parent.keyword == "list":
      keyval = parent.search_one('key').arg if parent.search_one('key') \
          is not None else False
      if keyval and " " in keyval:
        keyval = keyval.split(" ")
      else:
        keyval = [keyval]

    # Auto-generate a docstring based on the description that is provided in
    # the YANG module. This aims to provide readability to someone perusing the
    # code that is generated.
    parent_descr = parent.search_one('description')
    if parent_descr is not None:
      parent_descr = "\n\n  YANG Description: %s" % \
          parent_descr.arg.decode('utf8').encode('ascii', 'ignore')
    else:
      parent_descr = ""

    # Add more helper text.
    nfd.write('''  """
  This class was auto-generated by the PythonClass plugin for PYANG
  from YANG module %s - based on the path %s. Each member element of
  the container is represented as a class variable - with a specific
  YANG type.%s
  """\n''' % (module.arg, (path if not path == "" else "/%s" % parent.arg),
              parent_descr))
  else:
    raise TypeError("unhandled keyword with children %s at %s" % 
      (parent.keyword, parent.pos))

  elements_str = ""
  if len(elements) == 0:
    nfd.write("  _pyangbind_elements = {}")
  else:
    # We want to prevent a user from creating new attributes on a class that
    # are not allowed within the data model - this uses the __slots__ magic
    # variable of the class to restrict anyone from adding to these classes.
    # Doing so gives an AttributeError when a user tries to specify something
    # that was not in the model.
    elements_str = "_pyangbind_elements = {"
    slots_str = "  __slots__ = ('_pybind_generated_by', '_path_helper',"
    slots_str += " '_yang_name', '_extmethods', "
    for i in elements:
      slots_str += "'__%s'," % i["name"]
      elements_str += "'%s': %s, " % (i["name"], i["name"])
    slots_str += ")\n"
    elements_str += "}\n"
    nfd.write(slots_str + "\n")
    # Store the real name of the element - since we often get values that are
    # not allowed in python as identifiers, but we need the real-name when
    # creating instance documents (e.g., peer-group is not valid due to '-').
    nfd.write("  _yang_name = '%s'\n" % (parent.arg))

    choices = {}
    choice_attrs = []
    classes = {}
    for i in elements:
      # Loop through the elements and build a string that corresponds to the
      # class that is going to be created. In all cases (thus far) this uses
      # the YANGDynClass helper function to generate a dynamic type. This
      # can extend the base type that is provided, and does this to give us
      # some attributes that base classes such as int(), or str() don't have -
      # but YANG needs (such as a default value, the original YANG name, any
      # extension that were provided with the leaf, etc.).
      class_str = {}
      if "default" in i and not i["default"] is None:
        default_arg = "\"%s\"" % (i["default"]) if i["quote_arg"] else "%s" \
            % i["default"]

      if i["class"] == "leaf-list":
        # Map a leaf-list to the type specified in the class map. This is a
        # TypedList (see lib.yangtypes) with a particular set of types allowed.
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
        class_str["arg"] += "%s(allowed_type=%s)" % \
          (i["type"]["native_type"][0], allowed_type)
        if "default" in i and not i["default"] is None:
          class_str["arg"] += ", default=%s(%s)" % (i["defaulttype"],
            default_arg)
      elif i["class"] == "list":
        # Map a list to YANGList class - this is dynamically derived by the
        # YANGListType function to have the relevant characteristics, such as
        # whether it is ordered by the user.
        class_str["name"] = "__%s" % (i["name"])
        class_str["type"] = "YANGDynClass"
        class_str["arg"] = "base=YANGListType("
        class_str["arg"] += "%s,%s" % ("\"%s\"" % i["key"] if i["key"]
                                                  else False, i["type"])
        class_str["arg"] += ", yang_name=\"%s\", parent=self" \
            % (i["yang_name"])
        class_str["arg"] += ", is_container='list', user_ordered=%s" \
                                                  % i["user_ordered"]
        class_str["arg"] += ", path_helper=self._path_helper"
        class_str["arg"] += ", yang_keys='%s'" % i["yang_keys"]
        class_str["arg"] += ", extensions=%s" % i["extensions"]
        if i["choice"]:
          class_str["arg"] += ", choice=%s" % repr(choice)
        class_str["arg"] += ")"
      elif i["class"] == "union" or i["class"] == "leaf-union":
        # A special mapped type where there is a union that just includes
        # leaves this is mapped to a particular Union type, and valid types
        # within it. The dynamically generated class will determine whether
        # the input can be mapped to the types included in the union.
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
          class_str["arg"] += ", default=%s(%s)" % (i["defaulttype"],
            default_arg)
      elif i["class"] == "leafref":
        # A leafref, pyangbind uses the special ReferenceType which performs a
        # lookup against the path_helper class provided.
        class_str["name"] = "__%s" % (i["name"])
        class_str["type"] = "YANGDynClass"
        class_str["arg"] = "base=%s" % i["type"]
        class_str["arg"] += "(referenced_path='%s'" % i["referenced_path"]
        class_str["arg"] += ", caller=self._path() + ['%s'], " \
                                % (i["yang_name"])
        class_str["arg"] += "path_helper=self._path_helper, "
        class_str["arg"] += "require_instance=%s)" % (i["require_instance"])
      elif i["class"] == "leafref-list":
        # Deal with the special case of a list of leafrefs, since the
        # ReferenceType has different arguments that need to be provided to the
        # class to properly initialise.
        class_str["name"] = "__%s" % (i["name"])
        class_str["type"] = "YANGDynClass"
        class_str["arg"] = "base=%s" % i["type"]["native_type"][0]
        class_str["arg"] += "(allowed_type=%s(referenced_path='%s'," \
                              % (i["type"]["native_type"][1]["native_type"],
                                i["type"]["native_type"][1]["referenced_path"])
        class_str["arg"] += "caller=self._path() + ['%s'], " % i["yang_name"]
        class_str["arg"] += "path_helper=self._path_helper, "
        class_str["arg"] += "require_instance=%s))" % \
                              (i["type"]["native_type"][1]["require_instance"])
      else:
        # Generically handle all other classes with the 'standard' mappings.
        class_str["name"] = "__%s" % (i["name"])
        class_str["type"] = "YANGDynClass"
        if isinstance(i["type"], list):
          class_str["arg"] = "base=["
          for u in i["type"]:
            class_str["arg"] += "%s," % u
          class_str["arg"] += "]"
        else:
          class_str["arg"] = "base=%s" % i["type"]
        if "default" in i and not i["default"] is None:
          class_str["arg"] += ", default=%s(%s)" % (i["defaulttype"],
                                                        default_arg)
      if i["class"] == "container":
        class_str["arg"] += ", is_container='container'"
        if ctx.opts.generate_presence:
          class_str["arg"] += ", presence=%s" % i["presence"]
      elif i["class"] == "list":
        class_str["arg"] += ", is_container='list'"
      elif i["class"] == "leaf-list":
        class_str["arg"] += ", is_leaf=False"
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
        class_str["arg"] += ", extmethods=self._extmethods"
        class_str["arg"] += ", register_paths=%s" % i["register_paths"]
        if "extensions" in i:
          class_str["arg"] += ", extensions=%s" % i["extensions"]
        if keyval and i["yang_name"] in keyval:
          class_str["arg"] += ", is_keyval=True"
        class_str["arg"] += ", namespace='%s'" % i["namespace"]
        class_str["arg"] += ", defining_module='%s'" % i["defining_module"]
        class_str["arg"] += ", yang_type='%s'" % i["origtype"]
        class_str["arg"] += ", is_config=%s" % (i["config"] and parent_cfg)
        classes[i["name"]] = class_str

    # TODO: get and set methods currently have errors that are reported that
    # are a bit ugly. The intention here is to act like an immutable type -
    # such that new class instances are created each time that the value is
    # set.

    # Generic class __init__, set up the path_helper if asked to.
    nfd.write("""
  _pybind_generated_by = 'container'

  def __init__(self, *args, **kwargs):\n""")
    if ctx.opts.use_xpathhelper:
      nfd.write("""
    helper = kwargs.pop("path_helper", None)
    if helper is False:
      self._path_helper = False
    elif helper is not None and isinstance(helper, xpathhelper.YANGPathHelper):
      self._path_helper = helper
    elif hasattr(self, "_parent"):
      helper = getattr(self._parent, "_path_helper", False)
      self._path_helper = helper
    else:
      self._path_helper = False\n""")
    else:
      nfd.write("""
    self._path_helper = False\n""")

    if ctx.opts.use_extmethods:
      nfd.write("""
    extmethods = kwargs.pop("extmethods", None)
    if extmethods is False:
      self._extmethods = False
    elif extmethods is not None and isinstance(extmethods, dict):
      self._extmethods = extmethods
    elif hasattr(self, "_parent"):
      extmethods = getattr(self._parent, "_extmethods", None)
      self._extmethods = extmethods
    else:
      self._extmethods = False\n""")
    else:
      nfd.write("""
    self._extmethods = False\n""")

    # Write out the classes that are stored locally as self.__foo where
    # foo is the safe YANG name.
    for c in classes:
      nfd.write("    self.%s = %s(%s)\n" % (classes[c]["name"],
                                  classes[c]["type"], classes[c]["arg"]))
    # Don't accept arguments to a container/list/submodule class
    nfd.write("""
    load = kwargs.pop("load", None)
    if args:
      if len(args) > 1:
        raise TypeError("cannot create a YANG container with >1 argument")
      all_attr = True
      for e in self._pyangbind_elements:
        if not hasattr(args[0], e):
          all_attr = False
          break
      if not all_attr:
        raise ValueError("Supplied object did not have the correct attributes")
      for e in self._pyangbind_elements:
        nobj = getattr(args[0], e)
        if nobj._changed() is False:
          continue
        setmethod = getattr(self, "_set_%s" % e)
        if load is None:
          setmethod(getattr(args[0], e))
        else:
          setmethod(getattr(args[0], e), load=load)\n""")

    # A generic method to provide a path() method on each container, that gives
    # a path in the form of a list that describes the nodes in the hierarchy.
    nfd.write("""
  def _path(self):
    if hasattr(self, "_parent"):
      return self._parent._path()+[self._yang_name]
    else:
      return %s\n""" % path.split("/")[1:])
    node = {}

    # For each element, write out a getter and setter method - with the doc
    # string of the element within the model.
    for i in elements:
      c_str = classes[i["name"]]
      description_str = ""
      if i["description"]:
        description_str = "\n\n    YANG Description: %s" \
            % i["description"].decode('utf-8').encode('ascii', 'ignore')
      nfd.write('''
  def _get_%s(self):
    """
    Getter method for %s, mapped from YANG variable %s (%s)%s
    """
    return self.__%s
      ''' % (i["name"], i["name"], i["path"], i["origtype"],
             description_str, i["name"]))

      nfd.write('''
  def _set_%s(self, v, load=False):
    """
    Setter method for %s, mapped from YANG variable %s (%s)
    If this variable is read-only (config: false) in the
    source YANG file, then _set_%s is considered as a private
    method. Backends looking to populate this variable should
    do so via calling thisObj._set_%s() directly.%s
    """''' % (i["name"], i["name"], i["path"],
                          i["origtype"], i["name"], i["name"],
                          description_str))
      if keyval and i["yang_name"] in keyval:
        nfd.write("""
    parent = getattr(self, "_parent", None)
    if parent is not None and load is False:
      raise AttributeError("Cannot set keys directly when" +
                             " within an instantiated list")\n""")
      nfd.write("""
    if hasattr(v, "_utype"):
      v = v._utype(v)""")
      nfd.write("""
    try:
      t = %s(v,%s)""" % (c_str["type"], c_str["arg"]))
      nfd.write("""
    except (TypeError, ValueError):\n""")
      nfd.write("""      raise ValueError({
          'error-string': \"\"\"%s must be of a type compatible with %s\"\"\",
          'defined-type': "%s",
          'generated-type': \"\"\"%s(%s)\"\"\",
        })\n\n""" % (i["name"], i["origtype"],
                  "%s:%s" % (i["defining_module"], i["origtype"]) if ":"
                  not in i["origtype"] and not i["origtype"] in
                  YANG_BUILTIN_TYPES else i["origtype"], c_str["type"],
                  c_str["arg"]))
      nfd.write("    self.__%s = t\n" % (i["name"]))
      nfd.write("    if hasattr(self, '_set'):\n")
      nfd.write("      self._set()\n")

      # When we want to return a value to its default, the unset method can
      # be used. Generally, this is done in a choice where one branch needs to
      # be set to the default, but may be used wherever re-initialiation of
      # the object is required.
      nfd.write("""
  def _unset_%s(self):
    self.__%s = %s(%s)\n\n""" % (i["name"], i["name"],
                                  c_str["type"], c_str["arg"],))

    # When an element is read-only, write out the _set and _get methods, but
    # we don't actually make the property object accessible. This ensures that
    # where backends are populating the model, then they can do so via the
    # _set_X method - but a 'normal' user can't just do container.X = 10.
    for i in elements:
      rw = True
      if not i["config"]:
        rw = False
      elif not parent_cfg:
        rw = False

      if not rw:
        nfd.write("""  %s = __builtin__.property(_get_%s)\n""" % (i["name"], i["name"]))
      else:
        nfd.write("""  %s = __builtin__.property(_get_%s, _set_%s)\n""" %
                          (i["name"], i["name"], i["name"]))
  nfd.write("\n")

  # Store a list of the choices that are included within this module such that
  # we can enforce each branch.
  if choices:
    nfd.write("  __choices__ = %s" % repr(choices))
  nfd.write("""\n  %s\n""" % elements_str)
  nfd.write("\n")

  if ctx.opts.split_class_dir:
    nfd.close()

  return None


def build_elemtype(ctx, et, prefix=False):
  # Build a dictionary which defines the type for the element. This is used
  # both in the case that a typedef needs to be built, as well as on per-list
  # basis.
  cls = None
  pattern_stmt = et.search_one('pattern') if not et.search_one('pattern') \
                                              is None else False
  range_stmt = et.search_one('range') if not et.search_one('range') \
                                              is None else False
  length_stmt = et.search_one('length') if not et.search_one('length') \
                                              is None else False

  # Determine whether there are any restrictions that are placed on this leaf,
  # and build a dictionary of the different restrictions to be placed on the
  # type.
  restrictions = {}
  if pattern_stmt:
    restrictions['pattern'] = pattern_stmt.arg

  if length_stmt:
    if "|" in length_stmt.arg:
      restrictions['length'] = [i.replace(' ', '') for i in
                                  length_stmt.arg.split("|")]
    else:
      restrictions['length'] = [length_stmt.arg]

  if range_stmt:
    # Complex ranges are separated by pipes
    if "|" in range_stmt.arg:
      restrictions['range'] = [i.replace(' ', '') for i in
                                  range_stmt.arg.split("|")]
    else:
      restrictions['range'] = [range_stmt.arg]

  # Build RestrictedClassTypes based on the compiled dictionary and the
  # underlying base type.
  if len(restrictions):
    if 'length' in restrictions or 'pattern' in restrictions:
      cls = "restricted-%s" % (et.arg)
      elemtype = {
          "native_type":
              """RestrictedClassType(base_type=%s, restriction_dict=%s)"""
              % (class_map[et.arg]["native_type"], repr(restrictions)),
          "restriction_dict": restrictions,
          "parent_type": et.arg,
          "base_type": False,
      }
    elif 'range' in restrictions:
      cls = "restricted-%s" % et.arg
      elemtype = {
          "native_type":
              """RestrictedClassType(base_type=%s, restriction_dict=%s)"""
              % (class_map[et.arg]["native_type"], repr(restrictions)),
          "restriction_dict": restrictions,
          "parent_type": et.arg,
          "base_type": False,
      }

  # Handle all other types of leaves that are not restricted classes.
  if cls is None:
    cls = "leaf"
    # Enumerations are built as RestrictedClasses where the value that is
    # provided to the class is check against the keys of a dictionary.
    if et.arg == "enumeration":
      enumeration_dict = {}
      for enum in et.search('enum'):
        enumeration_dict[unicode(enum.arg)] = {}
        val = enum.search_one('value')
        if val is not None:
          enumeration_dict[unicode(enum.arg)]["value"] = int(val.arg)
      elemtype = {"native_type": """RestrictedClassType(base_type=unicode, \
                                    restriction_type="dict_key", \
                                    restriction_arg=%s,)""" %
                                    (enumeration_dict),
                  "restriction_argument": enumeration_dict,
                  "restriction_type": "dict_key",
                  "parent_type": "string",
                  "base_type": False}
    # Map decimal64 to a RestrictedPrecisionDecimalType - this is there to
    # ensure that the fraction-digits argument can be implemented. Note that
    # fraction-digits is a mandatory argument.
    elif et.arg == "decimal64":
      fd_stmt = et.search_one('fraction-digits')
      if fd_stmt is not None:
        cls = "restricted-decimal64"
        elemtype = {"native_type":
                      """RestrictedPrecisionDecimalType(precision=%s)""" %
                      fd_stmt.arg, "base_type": False,
                      "parent_type": "decimal64"}
      else:
        elemtype = class_map[et.arg]
    # Handle unions - build a list of the supported types that are under the
    # union.
    elif et.arg == "union":
      elemtype = []
      for uniontype in et.search('type'):
        elemtype_s = copy.deepcopy(build_elemtype(ctx, uniontype))
        elemtype_s[1]["yang_type"] = uniontype.arg
        elemtype.append(elemtype_s)
      cls = "union"
    # Map leafrefs to a ReferenceType, handling the referenced path, and
    # whether require-instance is set. When xpathhelper is not specified, then
    # no such mapping is done - at this point, we solely map to a string.
    elif et.arg == "leafref":
      path_stmt = et.search_one('path')
      if path_stmt is None:
        raise ValueError("leafref specified with no path statement")
      require_instance = \
                  class_bool_map[et.search_one('require-instance').arg] \
                          if et.search_one('require-instance') \
                            is not None else True
      if ctx.opts.use_xpathhelper:
        elemtype = {"native_type": "ReferenceType",
                    "referenced_path": path_stmt.arg,
                    "parent_type": "string",
                    "base_type": False,
                    "require_instance": require_instance,}
        cls = "leafref"
      else:
        elemtype = {
            "native_type": "unicode",
            "parent_type": "string",
            "base_type": False,
        }
    # Handle identityrefs, but check whether there is a valid base where this
    # has been specified.
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
      # For all other cases, then we should be able to look up directly in the
      # class_map for the defined type, since these are not 'derived' types
      # at this point. In the case that we are referencing a type that is a
      # typedef, then this has been added to the class_map.
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
        if passed is False:
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

  return (cls, elemtype)


def find_absolute_default_type(default_type, default_value, elemname):
  if not isinstance(default_type, list):
    return default_type

  for i in default_type:
    if not i[1]["base_type"]:
      test_type = class_map[i[1]["parent_type"]]
    else:
      test_type = i[1]
    try:
      tmp = test_type["pytype"](default_value)
      default_type = test_type
      break
    except (ValueError, TypeError):
      pass
  return find_absolute_default_type(default_type, default_value, elemname)


def get_element(ctx, fd, element, module, parent, path,
                  parent_cfg=True, choice=False, register_paths=True):
  # Handle mapping of an invidual element within the model. This function
  # produces a dictionary that can then be mapped into the relevant code that
  # dynamically generates a class.

  # Find element's namespace and defining module
  # If the element has the "main_module" attribute then it is part of a
  # submodule and hence we should check the namespace and defining module
  # of this, rather than the submodule
  if hasattr(element, "main_module"):
    element_module = element.main_module()
  elif hasattr(element, "i_orig_module"):
    element_module = element.i_orig_module
  else:
    element_module = None

  namespace = element_module.search_one("namespace").arg if \
                element_module.search_one("namespace") is not None else \
                  None
  defining_module = element_module.arg

  this_object = []
  default = False
  has_children = False
  create_list = False

  elemdescr = element.search_one('description')
  if elemdescr is None:
    elemdescr = False
  else:
    elemdescr = elemdescr.arg

    # In cases where there there are a set of interesting extensions specified
    # then build a dictionary of these extension values to provide with the
    # specific leaf for this element.
  if element.substmts is not None and \
        ctx.opts.pybind_interested_exts is not None:
    extensions = {}
    for ext in element.substmts:
      if ext.keyword[0] in ctx.opts.pybind_interested_exts:
        if not ext.keyword[0] in extensions:
          extensions[ext.keyword[0]] = {}
        extensions[ext.keyword[0]][ext.keyword[1]] = ext.arg

  # If the element has an i_children attribute then this is a container, list
  # leaf-list or choice. Alternatively, it can be the 'input' or 'output'
  # substmts of an RPC or a notification
  if hasattr(element, 'i_children'):
    if element.keyword in ["container", "list", "input", "output", "notification"]:
      has_children = True
    elif element.keyword in ["leaf-list"]:
      create_list = True

    # Fixup the path when within a choice, because this iteration belives that
    # we are under a new container, but this does not exist in the path.
    if element.keyword in ["choice"]:
      path_parts = path.split("/")
      npath = ""
      for i in range(0, len(path_parts) - 1):
        npath += "%s/" % path_parts[i]
      npath.rstrip("/")
    else:
      npath = path

    # Create an element for a container.
    if element.i_children or ctx.opts.generate_presence:
      chs = element.i_children
      has_presence = True if element.search_one('presence') is not None else False
      if has_presence is False and len(chs) == 0:
        return []

      get_children(ctx, fd, chs, module, element, npath, parent_cfg=parent_cfg,
                   choice=choice, register_paths=register_paths)

      elemdict = {
          "name": safe_name(element.arg), "origtype": element.keyword,
          "class": element.keyword,
          "path": safe_name(npath), "config": True,
          "description": elemdescr,
          "yang_name": element.arg,
          "choice": choice,
          "register_paths": register_paths,
          "namespace": namespace,
          "defining_module": defining_module,
          "extensions": extensions if len(extensions) else None,
          "presence": has_presence,
      }

      # Handle the different cases of class name, this depends on whether we
      # were asked to split the bindings into a directory structure or not.
      if ctx.opts.split_class_dir:
        # If we were dealing with split classes, then rather than naming the
        # class based on a unique intra-file name - and rather we must import
        # the relative path to the module.class
        if element.arg == parent.arg:
          modname = safe_name(element.arg) + "_"
        else:
          modname = safe_name(element.arg)
        elemdict["type"] = "%s.%s" % (modname, safe_name(element.arg))

      else:
        # Otherwise, give a unique name for the class within the dictionary.
        elemdict["type"] = "yc_%s_%s_%s" % (safe_name(element.arg),
                                            safe_name(module.arg),
                                            safe_name(path.replace("/", "_")))

      # Deal with specific cases for list - such as the key and how it is
      # ordered.
      if element.keyword == "list":
        elemdict["key"] = safe_name(element.search_one("key").arg) \
            if element.search_one("key") is not None else False
        elemdict["yang_keys"] = element.search_one("key").arg \
            if element.search_one("key") is not None else False
        user_ordered = element.search_one('ordered-by')
        elemdict["user_ordered"] = True if user_ordered is not None \
          and user_ordered.arg.upper() == "USER" else False
      this_object.append(elemdict)
      has_children = True

  # Deal with the cases that the attribute does not have children.
  if not has_children:
    if element.keyword in ["leaf-list"]:
      create_list = True
    cls, elemtype = copy.deepcopy(build_elemtype(ctx,
                        element.search_one('type')))

    # Determine what the default for the leaf should be where there are
    # multiple available.
    # Algorithm:
    #   - build a tree that is rooted on this class.
    #   - perform a breadth-first search - the first node found
    #   - that has the "default" leaf set, then we take this
    #     as the value for the default

    # then starting at the selected default node, traverse
    # until we find a node that is declared to be a base_type
    elemdefault = element.search_one('default')
    default_type = False
    quote_arg = False
    if elemdefault is not None:
      elemdefault = elemdefault.arg
      default_type = elemtype
    if isinstance(elemtype, list):
      # this is a union, we should check whether any of the types
      # immediately has a default
      for i in elemtype:
        if "default" in i[1]:
          elemdefault = i[1]["default"]
          default_type = i[1]
          # default_type = i[1]
          # mapped_elemtype = i[1]
    elif "default" in elemtype:
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
          if "parent_type" in i[1]:
            if isinstance(i[1]["parent_type"], list):
              to_visit = [j for j in i[1]["parent_type"]]
            else:
              to_visit = [i[1]["parent_type"]]
      elif "parent_type" in elemtype:
        if isinstance(elemtype["parent_type"], list):
          to_visit = [i for i in elemtype["parent_type"]]
        else:
          to_visit = [elemtype["parent_type"]]

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
        default_type = find_absolute_default_type(default_type, elemdefault,
                          element.arg)

      if not default_type["base_type"]:
        if "parent_type" in default_type:
          if isinstance(default_type["parent_type"], list):
            to_visit = [i for i in default_type["parent_type"]]
          else:
            to_visit = [default_type["parent_type"]]
        checked = list()
        while to_visit:
          check = to_visit.pop(0)  # remove from the top of stack - depth first
          if check not in checked:
            checked.append(check)
            if "parent_type" in tmp_class_map[check]:
              if isinstance(tmp_class_map[check]["parent_type"], list):
                to_visit.extend(tmp_class_map[check]["parent_type"])
              else:
                to_visit.append(tmp_class_map[check]["parent_type"])
        default_type = tmp_class_map[checked.pop()]
        if not default_type["base_type"]:
          raise TypeError("default type was not a base type")

    # Set the default type based on what was determined above about the
    # correct value to set.
    if default_type:
      quote_arg = default_type["quote_arg"] if "quote_arg" in \
          default_type else False
      default_type = default_type["native_type"]

    elemconfig = class_bool_map[element.search_one('config').arg] if \
                                  element.search_one('config') else True

    elemname = safe_name(element.arg)

    # Deal with the cases that there is a requirement to create a list - these
    # are leaf lists. There is some special handling for leaf-lists to ensure
    # that the references are correctly created.
    if create_list:
      if not cls == "leafref":
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
      else:
        cls = "leafref-list"
        allowed_types = {
            "native_type": elemtype["native_type"],
            "referenced_path": elemtype["referenced_path"],
            "require_instance": elemtype["require_instance"],
        }
      elemntype = {"class": cls, "native_type": ("TypedListType",
                  allowed_types)}

    else:
      if cls == "union" or cls == "leaf-union":
        elemtype = {"class": cls, "native_type": ("UnionType", elemtype)}
      elemntype = elemtype["native_type"]

    # Build the dictionary for the element with the relevant meta-data
    # specified within it.
    elemdict = {
        "name": elemname, "type": elemntype,
        "origtype": element.search_one('type').arg, "path":
        safe_name(path),
        "class": cls, "default": elemdefault,
        "config": elemconfig, "defaulttype": default_type,
        "quote_arg": quote_arg,
        "description": elemdescr, "yang_name": element.arg,
        "choice": choice,
        "register_paths": register_paths,
        "namespace": namespace,
        "defining_module": defining_module
    }
    if len(extensions):
      elemdict["extensions"] = extensions

    if cls == "leafref":
      elemdict["referenced_path"] = elemtype["referenced_path"]
      elemdict["require_instance"] = elemtype["require_instance"]

    this_object.append(elemdict)
  return this_object
