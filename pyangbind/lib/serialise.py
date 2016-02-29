"""
Copyright 2015  Rob Shakir (rjs@jive.com, rjs@rob.sh)

This project has been supported by:
          * Jive Communcations, Inc.
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

serialise:
  * module containing methods to serialise pyangbind class hierarchie
    to various data encodings. XML and/or JSON as the primary examples.
"""

import json
import numpy as np
from collections import OrderedDict
from decimal import Decimal
from pyangbind.lib.yangtypes import safe_name, NUMPY_INTEGER_TYPES
from types import ModuleType
import copy

import sys

class pybindJSONIOError(Exception):
  pass


class pybindJSONUpdateError(Exception):
  pass


class pybindJSONEncoder(json.JSONEncoder):
  def _preprocess_element(self, d, mode="default"):
    nd = {}
    if isinstance(d, OrderedDict) or isinstance(d, dict):
        index = 0
        for k in d:
            if isinstance(d[k], dict) or isinstance(d[k], OrderedDict):
                nd[k] = self._preprocess_element(d[k], mode=mode)
                if isinstance(d, OrderedDict):
                    nd[k]['__yang_order'] = index
            else:
                nd[k] = self.default(d[k], mode=mode)
            # if we wanted to do this as per draft-ietf-netmod-yang-metadata
            # then the encoding is like this
            # if not "@%s" % k in nd:
            #  nd["@%s" % k] = {}
            #  nd["@%s" % k]['order'] = index
            # this has the downside that iterating over the dict gives you
            # some elements that do not really exist - there is a need to
            # exclude all elements that begin with "@"
            index += 1
    else:
        nd = d
    return nd

  def encode(self, obj):
    return json.JSONEncoder.encode(self, self._preprocess_element(obj))

  def default(self, obj, mode="default"):

    original_yang_type = getattr(obj, "_yang_type", None)
    elem_name = getattr(obj, "_yang_name", None)

    if original_yang_type is None:
      # check for specific elements such as dictionaries and lists
      if isinstance(obj, list):
        nlist = []
        for elem in obj:
          nlist.append(self.default(elem, mode=mode))
        return nlist

      if isinstance(obj, dict):
        ndict = {}
        for k,v in obj.iteritems():
          ndict[k] = self.default(v, mode=mode)
        return ndict

      if type(obj) in NUMPY_INTEGER_TYPES:
        if type(obj) in [np.uint64, np.int64] and mode == "ietf":
          return unicode(obj)
        else:
          return int(obj)

      if type(obj) in [str, unicode]:
        return unicode(obj)

      if type(obj) in [int]:
        return int(obj)

    else:
      if original_yang_type == "leafref":
        if hasattr(obj, "_get"):
          return self.default(obj._get(), mode=mode)
        return unicode(obj)

      if original_yang_type in ["int64", "uint64"]:
        if mode == "ietf":
          return unicode(obj)
        return int(obj)

      if original_yang_type in ["int8", "int16", "int32", "uint8",
                                "uint16", "uint32"]:
        return int(obj)

      if original_yang_type == "string":
        return unicode(obj)

      if original_yang_type == "binary":
        return obj.to01()

      if original_yang_type == "decimal64":
        if mode == "ietf":
          return unicode(obj)
        return float(obj)

      if original_yang_type == "bool":
        if obj:
          return True
        return False

      if original_yang_type == "empty":
        if obj and mode == "ietf":
          return [None]
        elif obj:
          return True
        return False

      if original_yang_type == "leaf-list":
        return [self.default(i, mode=mode) for i in obj]

      # Now we hit derived types, and need to use additional information
      map_val = getattr(obj, "_pybind_base_class", None)

      if map_val in ["pyangbind.lib.yangtypes.RestrictedClass"]:
        map_val = getattr(obj, "_restricted_class_base")[0]

      if map_val in ["numpy.uint8", "numpy.uint16", "numpy.uint32",
              "numpy.uint64", "numpy.int8", "numpy.int16", "numpy.int32",
              "numpy.int64"]:
        if mode == "ietf":
          if map_val in ["numpy.int64", "numpy.uint64"]:
            return str(obj)
        return int(obj)
      elif map_val in ["pyangbind.lib.yangtypes.ReferencePathType"]:
        return self.default(obj._get(), mode=mode)
      elif map_val in ["pyangbind.lib.yangtypes.RestrictedPrecisionDecimal"]:
        return float(obj)
      elif map_val in ["bitarray.bitarray"]:
        return obj.to01()
      elif map_val in ["pyangbind.lib.yangtypes.YANGBool"]:
        if obj:
          return True
        else:
          return False
      elif map_val in ["unicode", unicode]:
        return unicode(obj)
      elif map_val in ["pyangbind.lib.yangtypes.TypedList"]:
        keys = obj._list
        for i in obj._list:
          for t in obj._allowed_type:
            try:
              tmp = t(i)
              break
            except ValueError:
              tmp = None

        return [self.default(i) for i in obj]


      raise AttributeError("Unmapped type: %s" % original_yang_type)

class pybindJSONDecoder(object):
  def load_json(self, d, parent, yang_base, obj=None, path_helper=None,
                extmethods=None, overwrite=False):

    if obj is None:
      # we need to find the class to create, as one has not been supplied.
      base_mod_cls = getattr(parent, safe_name(yang_base))
      tmp = base_mod_cls(path_helper=False)

      if path_helper is not None:
        # check that this path doesn't already exist in the
        # tree, otherwise we create a duplicate.
        existing_objs = path_helper.get(tmp._path())
        if len(existing_objs) == 0:
          obj = base_mod_cls(path_helper=path_helper, extmethods=extmethods)
        elif len(existing_objs) == 1:
          obj = existing_objs[0]
        else:
          raise pybindJSONUpdateError('update was attempted to a node that ' +
                                      'was not unique')
      else:
        # in this case, we cannot check for an existing object
        obj = base_mod_cls(path_helper=path_helper, extmethods=extmethods)

    for key in d:
      child = getattr(obj, "_get_%s" % safe_name(key), None)
      if child is None:
        raise AttributeError("JSON object contained a key that" +
                              "did not exist (%s)" % (key))
      chobj = child()
      set_via_stdmethod = True
      pybind_attr = getattr(chobj, '_pybind_generated_by', None)
      if pybind_attr in ["container"]:
        if overwrite:
          for elem in chobj._pyangbind_elements:
            unsetchildelem = getattr(chobj, "_unset_%s" % elem)
            unsetchildelem()
        self.load_json(d[key], chobj, yang_base, obj=chobj, path_helper=path_helper)
        set_via_stdmethod = False
      elif pybind_attr in ["YANGListType", "list"]:
        # we need to add each key to the list and then skip a level in the
        # JSON hierarchy
        for child_key in d[key]:
          if child_key not in chobj:
            chobj.add(child_key)
          parent = chobj[child_key]
          self.load_json(d[key][child_key], parent, yang_base, obj=parent, path_helper=path_helper)
          set_via_stdmethod = False
        if overwrite:
          for child_key in chobj:
            if child_key not in d[key]:
              chobj.delete(child_key)
      elif pybind_attr in ["TypedListType"]:
        if not overwrite:
          list_obj = getattr(obj, "_get_%s" % safe_name(key))()
          for item in d[key]:
            if item not in list_obj:
              list_obj.append(item)
          list_copy = []
          for elem in list_obj:
            list_copy.append(elem)
          for e in list_copy:
            if e not in d[key]:
              list_obj.remove(e)
          set_via_stdmethod = False
        else:
          # use the set method
          pass
      elif pybind_attr in ["RestrictedClassType", "ReferencePathType"]:
        # normal but valid types - which use the std set method
        pass
      elif pybind_attr is None:
        # not a pybind attribute at all - keep using the std set method
        pass
      else:
        raise pybindJSONUpdateError("unknown pybind type when loading JSON: %s"
                                     % pybind_attr)
      if set_via_stdmethod:
        # simply get the set method and then set the value of the leaf
        set_method = getattr(obj, "_set_%s" % safe_name(key))
        set_method(d[key], load=True)
    return obj


  def load_ietf_json(self, d, parent, yang_base, obj=None, path_helper=None,
                extmethods=None, overwrite=False):
    if obj is None:
      # we need to find the class to create, as one has not been supplied.
      base_mod_cls = getattr(parent, safe_name(yang_base))
      tmp = base_mod_cls(path_helper=False)

      if path_helper is not None:
        # check that this path doesn't already exist in the
        # tree, otherwise we create a duplicate.
        existing_objs = path_helper.get(tmp._path())
        if len(existing_objs) == 0:
          obj = base_mod_cls(path_helper=path_helper, extmethods=extmethods)
        elif len(existing_objs) == 1:
          obj = existing_objs[0]
        else:
          raise pybindJSONUpdateError('update was attempted to a node that ' +
                                      'was not unique')
      else:
        # in this case, we cannot check for an existing object
        obj = base_mod_class(path_helper=path_helper, extmethods=extmethods)

    for key in d:
      # Fix any namespace that was supplied in the JSON
      if ":" in key:
        ykey = key.split(":")[-1]
      else:
        ykey = key

      std_method_set = False
      # Handle the case that this is a JSON object
      if isinstance(d[key], dict):
        # Iterate through attributes and set to that value
        attr_get = getattr(obj, "_get_%s" % ykey, None)
        if attr_get is None:
          raise AttributeError("Invalid attribute specified")
        self.load_ietf_json(d[key], None, None, obj=attr_get(), path_helper=path_helper, extmethods=extmethods, overwrite=overwrite)
      elif isinstance(d[key], list):
        for elem in d[key]:
          # if this is a list, then this is a YANG list
          this_attr = getattr(obj, "_get_%s" % safe_name(ykey), None)
          if this_attr is None:
            raise AttributeError("List specified that did not exist")
          this_attr = this_attr()
          if hasattr(this_attr, "_keyval"):
            #  this handles YANGLists
            if this_attr._keyval is False:
              # Keyless list, generate a key
              k = this_attr.add()
            elif " " in this_attr._keyval:
              raise AttributeError("TODO")
              pass
            else:
              nobj = this_attr.add(elem[this_attr._keyval])
              self.load_ietf_json(elem, None, None, obj=nobj, path_helper=path_helper, extmethods=extmethods, overwrite=overwrite)
          else:
            std_method_set = True
      else:
        std_method_set = True

      if std_method_set:
        get_method = getattr(obj, "_get_%s" % safe_name(ykey), None)
        chk = get_method()
        if chk._is_keyval is True:
          pass
        else:
          set_method = getattr(obj, "_set_%s" % safe_name(ykey), None)
          if set_method is None:
            raise AttributeError("Invalid attribute specified in JSON - %s" % (ykey))
          set_method(d[key])
    return obj

class pybindIETFJSONEncoder(pybindJSONEncoder):
  def generate_element(self, obj, parent_namespace=None, flt=False):
    """
      Convert a pyangbind class to a format which encodes to the IETF JSON
      specification, rather than the default .get() format, which does not
      match this specification.

      The implementation is based on draft-ietf-netmod-yang-json-07.
    """
    d = {}
    for element_name in obj._pyangbind_elements:
      element = getattr(obj, element_name, None)
      yang_name = getattr(element, "yang_name", None)
      yname = yang_name() if not yang_name is None else element_name

      if not element._namespace == parent_namespace:
        yname = "%s:%s" % (element._namespace, yname)

      generated_by = getattr(element, "_pybind_generated_by", None)
      if generated_by  == "container":
        d[yname] = self.generate_element(element, parent_namespace=element._namespace, flt=flt)
      elif generated_by == "YANGListType":
        d[yname] = [self.generate_element(i, parent_namespace=element._namespace, flt=flt) for i in element._members.itervalues()]
      else:
        if flt and element._changed():
          d[yname] = element
        elif not flt:
          d[yname] = element
    return d

  def encode(self, obj):
    return json.JSONEncoder.encode(self, self._preprocess_element(obj, mode="ietf"))

  def default(self, obj, mode="ietf"):
    return pybindJSONEncoder().default(obj, mode="ietf")
