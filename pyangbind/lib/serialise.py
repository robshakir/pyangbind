"""
Copyright 2015  Rob Shakir (rjs@jive.com, rjs@rob.sh)

Modifications copyright 2016, Google, Inc.

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
from collections import OrderedDict
from decimal import Decimal
from pyangbind.lib.yangtypes import safe_name, YANGBool
from types import ModuleType
import copy

import sys


class pybindJSONIOError(Exception):
  pass


class pybindJSONUpdateError(Exception):
  pass


class pybindJSONDecodeError(Exception):
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

  def default(self, obj, mode='default'):
    pybc = getattr(obj, "_pybind_generated_by", None)
    elem_name = getattr(obj, "_yang_name", None)
    orig_yangt = getattr(obj, "_yang_type", None)

    # Expand lists
    if isinstance(obj, list):
      return [self.default(i, mode=mode) for i in obj]
    # Expand dictionaries
    elif isinstance(obj, dict):
      return {k: self.default(v, mode=mode) for k, v in obj.iteritems()}

    if pybc is not None:
      # Special cases where the wrapper has an underlying class
      if pybc == "RestrictedClassType":
        pybc = getattr(obj, "_restricted_class_base")[0]
      elif pybc == "TypedListType":
        return [self.default(i) for i in obj]

    # Map based on YANG type
    if orig_yangt in ["leafref"]:
      return self.default(obj._get()) if hasattr(obj, "_get") \
                                                  else unicode(obj)
    elif orig_yangt in ["int64", "uint64"]:
      return unicode(obj) if mode == "ietf" else int(obj)
    elif orig_yangt in ["identityref"]:
      if mode == "ietf":
        try:
          emod = obj._enumeration_dict[obj]["@module"]
          if emod != obj._defining_module:
            return "%s:%s" % (obj._enumeration_dict[obj]["@module"], obj)
        except KeyError:
          pass
        return unicode(obj)
    elif orig_yangt in ["int8", "int16", "int32", "uint8", "uint16", "uint32"]:
      return int(obj)
    elif orig_yangt in ["int64" "uint64"]:
      if mode == "ietf":
        return unicode(obj)
      else:
        return int(obj)
    elif orig_yangt in ["string", "enumeration"]:
      return unicode(obj)
    elif orig_yangt in ["binary"]:
      return obj.to01()
    elif orig_yangt in ["decimal64"]:
      return unicode(obj) if mode == "ietf" else float(obj)
    elif orig_yangt in ["bool"]:
      return True if obj else False
    elif orig_yangt in ["empty"]:
      if obj:
        return [None] if mode == "ietf" else True
      return False
    elif orig_yangt in ["container"]:
      return self._preprocess_element(obj.get(), mode=mode)

    # The value class is actually a pyangbind class, so map it
    pyc = getattr(obj, "_pybind_base_class", None) if pybc is None else pybc
    if pyc is not None:
      val = self.map_pyangbind_type(pyc, orig_yangt, obj, mode)
      if val is not None:
        return val

    # We are left with a native type
    if isinstance(obj, list):
      nlist = []
      for elem in obj:
        nlist.append(self.default(elem, mode=mode))
      return nlist
    elif isinstance(obj, dict):
      ndict = {}
      for k, v in obj.iteritems():
        ndict[k] = self.default(v, mode=mode)
      return ndict
    elif type(obj) in [str, unicode]:
      return unicode(obj)
    elif type(obj) in [int, long]:
      return int(obj)
    elif type(obj) in [YANGBool, bool]:
      return bool(obj)

    raise AttributeError("Unmapped type: %s, %s, %s, %s, %s, %s" %
                                  (elem_name, orig_yangt, pybc, pyc,
                                    type(obj), obj))

  def map_pyangbind_type(self, map_val, original_yang_type, obj, mode):
    if map_val in ["pyangbind.lib.yangtypes.RestrictedClass",
                                                "RestrictedClassType"]:
      map_val = getattr(obj, "_restricted_class_base")[0]

    if map_val in ["pyangbind.lib.yangtypes.ReferencePathType", "ReferencePathType"]:
      return self.default(obj._get(), mode=mode)
    elif map_val in ["pyangbind.lib.yangtypes.RestrictedPrecisionDecimal", "RestrictedPrecisionDecimal"]:
      if mode == "ietf":
        return unicode(obj)
      return float(obj)
    elif map_val in ["bitarray.bitarray"]:
      return obj.to01()
    elif map_val in ["unicode"]:
      return unicode(obj)
    elif map_val in ["pyangbind.lib.yangtypes.YANGBool"]:
      if original_yang_type == "empty" and mode == "ietf":
        if obj:
          return [None]
      else:
        if obj:
          return True
        else:
          return False
    elif map_val in ["pyangbind.lib.yangtypes.TypedList"]:
        return [self.default(i) for i in obj]
    elif map_val in ["int"]:
      return int(obj)
    elif map_val in ["long"]:
      int_size = getattr(obj, "_restricted_int_size", None)
      if mode == "ietf" and int_size == 64:
        return unicode(obj)
      return int(obj)
    elif map_val in ["container"]:
      return self._preprocess_element(obj.get(), mode=mode)
    elif map_val in ["decimal.Decimal"]:
      return unicode(obj) if mode == "ietf" else float(obj)




class pybindJSONDecoder(object):
  @staticmethod
  def load_json(d, parent, yang_base, obj=None, path_helper=None,
                extmethods=None, overwrite=False, skip_unknown=False):

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

    # Handle the case where we are supplied with a scalar value rather than
    # a list
    if not isinstance(d, dict) or isinstance(d, list):
      set_method = getattr(obj._parent, "_set_%s" % safe_name(obj._yang_name))
      set_method(d)
      return obj

    for key in d:
      child = getattr(obj, "_get_%s" % safe_name(key), None)
      if child is None and skip_unknown is False:
        raise AttributeError("JSON object contained a key that" +
                              "did not exist (%s)" % (key))
      elif child is None and skip_unknown:
        # skip unknown elements if we are asked to by the user`
        continue
      chobj = child()

      if hasattr(chobj, "_presence"):
        if chobj._presence:
          chobj._set_present()

      set_via_stdmethod = True
      pybind_attr = getattr(chobj, '_pybind_generated_by', None)
      if pybind_attr in ["container"]:
        if overwrite:
          for elem in chobj._pyangbind_elements:
            unsetchildelem = getattr(chobj, "_unset_%s" % elem)
            unsetchildelem()
        pybindJSONDecoder.load_json(d[key], chobj, yang_base, obj=chobj,
            path_helper=path_helper, skip_unknown=skip_unknown)
        set_via_stdmethod = False
      elif pybind_attr in ["YANGListType", "list"]:
        # we need to add each key to the list and then skip a level in the
        # JSON hierarchy
        list_obj = getattr(obj, safe_name(key), None)
        if list_obj is None and skip_unknown is False:
          raise pybindJSONDecodeError("Could not load list object " +
                    "with name %s" % key)
        if list_obj is None and skip_unknown is not False:
          continue

        ordered_list = getattr(list_obj, "_ordered", None)
        if ordered_list:
          # Put keys in order:
          okeys = []
          kdict = {}
          for k, v in d[key].iteritems():
            if "__yang_order" not in v:
              # Element is not specified in terms of order, so
              # push to a list that keeps this order
              okeys.append(k)
            else:
              kdict[v["__yang_order"]] = k
              # Throw this metadata away
              v.pop("__yang_order", None)
          okeys.reverse()
          key_order = [kdict[k] for k in sorted(kdict)]
          for add_element in okeys:
            key_order.append(add_element)
        else:
          key_order = d[key].keys()

        for child_key in key_order:
          if child_key not in chobj:
            chobj.add(child_key)
          parent = chobj[child_key]
          pybindJSONDecoder.load_json(d[key][child_key], parent, yang_base,
                obj=parent, path_helper=path_helper, skip_unknown=skip_unknown)
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
      elif pybind_attr in ["RestrictedClassType", "ReferencePathType", "RestrictedPrecisionDecimal"]:
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

  @staticmethod
  def check_metadata_add(key, data, obj):
    keys = [unicode(k) for k in data]
    if ("@" + key) in keys:
      for k, v in data["@" + key].iteritems():
        obj._add_metadata(k, v)

  @staticmethod
  def load_ietf_json(d, parent, yang_base, obj=None, path_helper=None,
                extmethods=None, overwrite=False, skip_unknown=False):
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

    # Handle the case where we are supplied with a scalar value rather than
    # a list
    if not isinstance(d, dict) or isinstance(d, list):
      set_method = getattr(obj._parent, "_set_%s" % safe_name(obj._yang_name))
      set_method(d)
      return obj

    for key in d:
      # Fix any namespace that was supplied in the JSON
      if ":" in key:
        ykey = key.split(":")[-1]
      else:
        ykey = key

      if key == "@":
        # Handle whole container metadata object
        for k, v in d[key].iteritems():
          obj._add_metadata(k, v)
        continue
      elif "@" in key:
        # Don't handle metadata elements, each element
        # will look up its own metadata
        continue

      std_method_set = False
      # Handle the case that this is a JSON object
      if isinstance(d[key], dict):
        # Iterate through attributes and set to that value
        attr_get = getattr(obj, "_get_%s" % safe_name(ykey), None)
        if attr_get is None and skip_unknown is False:
          raise AttributeError("Invalid attribute specified (%s)" % ykey)
        elif attr_get is None and skip_unknown is not False:
          # Skip unknown JSON keys
          continue

        chobj = attr_get()
        if hasattr(chobj, "_presence"):
          if chobj._presence:
            chobj._set_present()

        pybindJSONDecoder.check_metadata_add(key, d, chobj)
        pybindJSONDecoder.load_ietf_json(d[key], None, None, obj=chobj,
                  path_helper=path_helper, extmethods=extmethods,
                      overwrite=overwrite, skip_unknown=skip_unknown)
      elif isinstance(d[key], list):
        for elem in d[key]:
          # if this is a list, then this is a YANG list
          this_attr = getattr(obj, "_get_%s" % safe_name(ykey), None)
          if this_attr is None:
            raise AttributeError("List specified that did not exist")
          this_attr = this_attr()
          if hasattr(this_attr, "_keyval"):
            if overwrite:
              existing_keys = this_attr.keys()
              for i in existing_keys:
                this_attr.delete(i)
            #  this handles YANGLists
            if this_attr._keyval is False:
              # Keyless list, generate a key
              k = this_attr.add()
              nobj = this_attr[k]
            elif " " in this_attr._keyval:
              keystr = u""
              kwargs = {}
              for pkv, ykv in zip(this_attr._keyval.split(" "),
                                      this_attr._yang_keys.split(" ")):
                kwargs[pkv] = elem[ykv]
                keystr += u"%s " % elem[ykv]
              keystr = keystr.rstrip(" ")
              if not keystr in this_attr:
                nobj = this_attr.add(**kwargs)
              else:
                nobj = this_attr[keystr]
            else:
              k = elem[this_attr._yang_keys]
              if not k in this_attr:
                nobj = this_attr.add(k)
              else:
                nobj = this_attr[k]
            pybindJSONDecoder.load_ietf_json(elem, None, None, obj=nobj,
                path_helper=path_helper, extmethods=extmethods,
                  overwrite=overwrite, skip_unknown=skip_unknown)
            pybindJSONDecoder.check_metadata_add(key, d, nobj)
          else:
            # this is a leaf-list
            std_method_set = True
      else:
        std_method_set = True

      if std_method_set:
        get_method = getattr(obj, "_get_%s" % safe_name(ykey), None)
        if get_method is None and skip_unknown is False:
          raise AttributeError("JSON object contained a key that " +
                              "did not exist (%s)" % (ykey))
        elif get_method is None and skip_unknown is not False:
          continue
        chk = get_method()
        if chk._is_keyval is True:
          pass
        elif chk._yang_type == "empty":
          if d[key] == None:
            set_method(True)
        else:
          set_method = getattr(obj, "_set_%s" % safe_name(ykey), None)
          if set_method is None:
            raise AttributeError("Invalid attribute specified in JSON - %s"
                                    % (ykey))
          set_method(d[key])
        pybindJSONDecoder.check_metadata_add(key, d, get_method())
    return obj


class pybindIETFJSONEncoder(pybindJSONEncoder):
  @staticmethod
  def generate_element(obj, parent_namespace=None, flt=False):
    """
      Convert a pyangbind class to a format which encodes to the IETF JSON
      specification, rather than the default .get() format, which does not
      match this specification.

      The implementation is based on draft-ietf-netmod-yang-json-07.
    """
    generated_by = getattr(obj, "_pybind_generated_by", None)
    if generated_by == "YANGListType":
      return [pybindIETFJSONEncoder.generate_element(i, flt=flt) for i in
                                                            obj.itervalues()]
    d = {}
    for element_name in obj._pyangbind_elements:
      element = getattr(obj, element_name, None)
      yang_name = getattr(element, "yang_name", None)
      yname = yang_name() if yang_name is not None else element_name

      if not element._namespace == parent_namespace:
        # if the namespace is different, then precede with the module
        # name as per spec.
        yname = "%s:%s" % (element._defining_module, yname)

      generated_by = getattr(element, "_pybind_generated_by", None)
      if generated_by == "container":
        d[yname] = pybindIETFJSONEncoder.generate_element(element,
                      parent_namespace=element._namespace, flt=flt)
        if not len(d[yname]):
          del d[yname]
      elif generated_by == "YANGListType":
        d[yname] = [pybindIETFJSONEncoder.generate_element(i,
                      parent_namespace=element._namespace, flt=flt)
                        for i in element._members.itervalues()]
        if not len(d[yname]):
          del d[yname]
      else:
        if flt and element._changed():
          d[yname] = element
        elif not flt:
          d[yname] = element
    return d


  def encode(self, obj):
    return json.JSONEncoder.encode(self,
        self._preprocess_element(obj, mode="ietf"))

  def default(self, obj, mode="ietf"):
    return pybindJSONEncoder().default(obj, mode="ietf")
