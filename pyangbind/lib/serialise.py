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
from __future__ import unicode_literals

import json
from collections import OrderedDict
from decimal import Decimal

import six
from enum import IntEnum
from lxml import objectify, etree

from pyangbind.lib.yangtypes import YANGBool, safe_name


if six.PY3:
    long = int


class WithDefaults(IntEnum):
    IF_SET = 0


class pybindJSONIOError(Exception):
    pass


class pybindLoadUpdateError(Exception):
    pass


class pybindJSONDecodeError(Exception):
    pass


class UnmappedItem(Exception):
    """Used to simulate an Optional value"""
    pass


class SerialisedTypedList(list):
    pass


class YangDataSerialiser(object):
    """
    This class encapsulates the logic to parse the object tree and generate appropriate
    value data types for encoding
    """

    def preprocess_element(self, d):
        nd = {}
        if isinstance(d, OrderedDict) or isinstance(d, dict):
            index = 0
            for k in d:
                if isinstance(d[k], dict) or isinstance(d[k], OrderedDict):
                    nd[k] = self.preprocess_element(d[k])
                    if getattr(d, "_user_ordered", False):
                        nd[k]["__yang_order"] = index
                else:
                    nd[k] = self.default(d[k])
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

    def default(self, obj):
        pybc = getattr(obj, "_pybind_generated_by", None)
        elem_name = getattr(obj, "_yang_name", None)
        orig_yangt = getattr(obj, "_yang_type", None)

        # Expand lists
        if isinstance(obj, list):
            return [self.default(i) for i in obj]
        # Expand dictionaries
        elif isinstance(obj, dict):
            return {k: self.default(v) for k, v in six.iteritems(obj)}

        if pybc is not None:
            # Special cases where the wrapper has an underlying class
            if pybc == "RestrictedClassType":
                pybc = getattr(obj, "_restricted_class_base")[0]
            elif pybc == "TypedListType":
                return self.yangt_typed_list(obj)

        # Map based on YANG type
        if orig_yangt in ["leafref"]:
            return self.default(obj._get()) if hasattr(obj, "_get") else six.text_type(obj)
        elif orig_yangt in ["int64", "uint64"]:
            return self.yangt_long(obj)
        elif orig_yangt in ["identityref"]:
            try:
                return self.yangt_identityref(obj)
            except UnmappedItem:
                pass
        elif orig_yangt in ["int8", "int16", "int32", "uint8", "uint16", "uint32"]:
            return self.yangt_int(obj)
        elif orig_yangt in ["string", "enumeration"]:
            return six.text_type(obj)
        elif orig_yangt in ["binary"]:
            return obj.to01()
        elif orig_yangt in ["decimal64"]:
            return self.yangt_decimal(obj)
        elif orig_yangt in ["bool"]:
            return True if obj else False
        elif orig_yangt in ["empty"]:
            return self.yangt_empty(obj)
        elif orig_yangt in ["container"]:
            return self.preprocess_element(obj.get())

        # The value class is actually a pyangbind class, so map it
        pyc = getattr(obj, "_pybind_base_class", None) if pybc is None else pybc
        if pyc is not None:
            val = self.map_pyangbind_type(pyc, orig_yangt, obj)
            if val is not None:
                return val

        # We are left with a native type
        if isinstance(obj, list):
            nlist = []
            for elem in obj:
                nlist.append(self.default(elem))
            return nlist
        elif isinstance(obj, dict):
            ndict = {}
            for k, v in six.iteritems(obj):
                ndict[k] = self.default(v)
            return ndict
        elif isinstance(obj, six.string_types + (six.text_type,)):
            return six.text_type(obj)
        elif isinstance(obj, six.integer_types):
            return int(obj)
        elif isinstance(obj, (YANGBool, bool)):
            return bool(obj)
        elif isinstance(obj, Decimal):
            return self.yangt_decimal(obj)

        raise AttributeError(
            "Unmapped type: %s, %s, %s, %s, %s, %s" % (elem_name, orig_yangt, pybc, pyc, type(obj), obj)
        )

    def map_pyangbind_type(self, map_val, original_yang_type, obj):
        if map_val in ["pyangbind.lib.yangtypes.RestrictedClass", "RestrictedClassType"]:
            map_val = getattr(obj, "_restricted_class_base")[0]

        if map_val in ["pyangbind.lib.yangtypes.ReferencePathType", "ReferencePathType"]:
            return self.default(obj._get())
        elif map_val in ["pyangbind.lib.yangtypes.RestrictedPrecisionDecimal", "RestrictedPrecisionDecimal"]:
            # NOTE: this doesn't seem like it needs to be a special case?
            return self.yangt_decimal(obj)
        elif map_val in ["bitarray.bitarray"]:
            return obj.to01()
        elif map_val in ["unicode"]:
            return six.text_type(obj)
        elif map_val in ["pyangbind.lib.yangtypes.YANGBool"]:
            if original_yang_type == "empty":
                # NOTE: previously with IETF mode the code would fall-through if obj was falsey
                return self.yangt_empty(obj)
            else:
                return bool(obj)
        elif map_val in ["pyangbind.lib.yangtypes.TypedList"]:
            return self.yangt_typed_list(obj)
        elif map_val in ["int", "long"]:
            int_size = getattr(obj, "_restricted_int_size", None)
            return self.yangt_long(obj) if int_size == 64 else self.yangt_int(obj)
        elif map_val in ["container"]:
            return self.preprocess_element(obj.get())
        elif map_val in ["decimal.Decimal"]:
            return self.yangt_decimal(obj)

    def yangt_int(self, obj):
        # for values that are 32-bits and under..
        return int(obj)

    def yangt_long(self, obj):
        # don't need to special-case for PY3 because we assign `long = int` in the header
        return long(obj)

    def yangt_identityref(self, obj):
        # we don't want to do anything for non-IETF serialisation, this will fall-through
        raise UnmappedItem

    def yangt_decimal(self, obj):
        return float(obj)

    def yangt_empty(self, obj):
        return bool(obj)

    def yangt_typed_list(self, obj):
        return [self.default(i) for i in obj]


class IETFYangDataSerialiser(YangDataSerialiser):
    """
    IETF data serialiser overrides some of the data type formats only
    """

    def yangt_long(self, obj):
        return six.text_type(obj)

    def yangt_identityref(self, obj):
        try:
            emod = obj._enumeration_dict[obj]["@module"]
            if emod != obj._defining_module:
                return "%s:%s" % (obj._enumeration_dict[obj]["@module"], obj)
        except KeyError:
            pass
        return six.text_type(obj)

    def yangt_decimal(self, obj):
        return six.text_type(obj)

    def yangt_empty(self, obj):
        return [None] if obj else False


class XmlYangDataSerialiser(IETFYangDataSerialiser):
    """
    XML can have an empty tag, and a TypedList must be treated specially, here we mark it with a custom type
    """

    def yangt_typed_list(self, obj):
        # We have already used a standard list to denote a container, so we instead we use a custom list
        # type here in the serialised model
        return SerialisedTypedList([self.default(i) for i in obj])

    def yangt_empty(self, obj):
        return None


class _pybindJSONEncoderBase(json.JSONEncoder):
    """
    Pybind JSON encoder base class. Implements default `encode()` and `default()` methods
    to be used as an encoder class with the deault *json* module.

    Do not use directly, subclass and set the `serialiser_class` attribute appropriately
    """
    serialiser_class = None

    def encode(self, obj):
        return json.JSONEncoder.encode(self, self.serialiser_class().preprocess_element(obj))

    def default(self, obj):
        return self.serialiser_class().default(obj)


class pybindJSONEncoder(_pybindJSONEncoderBase):
    """Default pybind JSON encoder"""
    serialiser_class = YangDataSerialiser


class pybindIETFJSONEncoder(_pybindJSONEncoderBase):
    """IETF JSON encoder, we add a special method `generate_element()` that should be used
    to restructure the pybind object to fit IETF requirements prior to JSON encoding."""
    serialiser_class = IETFYangDataSerialiser

    @staticmethod
    def yname_ns_func(parent_namespace, element, yname):
        if not element._namespace == parent_namespace:
            # if the namespace is different, then precede with the module
            # name as per spec.
            return "%s:%s" % (element._defining_module, yname)
        else:
            return yname

    @staticmethod
    def generate_element(obj, parent_namespace=None, flt=False, with_defaults=None):
        """Restructure pybind `obj` to IETF spec"""
        ietf_tree_json_func = make_generate_ietf_tree(pybindIETFJSONEncoder.yname_ns_func)
        return ietf_tree_json_func(obj, parent_namespace=parent_namespace, flt=flt, with_defaults=with_defaults)


class pybindIETFXMLEncoder(object):
    """
    IETF XML encoder for pybind object tree serialisation.
    Use the `encode()` method to return an lxml.objectify tree representation of the pybind object.
    The `serialise()` method is a helper around that to return a pretty-printed XML string.
    """

    class EMF(objectify.ElementMaker):
        """Custome ElementMaker class to ease netconf namespace handling"""

        def __init__(self, namespace=None, nsmap=None):
            assert namespace or nsmap, "Must set either namespace or nsmap"
            if namespace:
                nsmap = {None: namespace}
            elif nsmap:
                namespace = nsmap[None]
            super(pybindIETFXMLEncoder.EMF, self).__init__(annotate=False, namespace=namespace, nsmap=nsmap)

    @classmethod
    def generate_xml_tree(cls, module_name, module_namespace, tree):
        """Map the IETF structured, and value-processed, object tree into an lxml objectify object"""
        doc = pybindIETFXMLEncoder.EMF(namespace=module_namespace)(module_name)

        def aux(parent, root):
            for k, v in root.items():
                k, nsmap = k
                E = pybindIETFXMLEncoder.EMF(nsmap=dict(nsmap))
                if isinstance(v, SerialisedTypedList):
                    # TypedList (e.g. leaf-list or union-list), process each element as a sibling
                    for i in v:
                        el = E(k, str(i))
                        parent.append(el)
                elif isinstance(v, list):
                    # a container maps to a list, recursively process each element as a child element
                    for i in v:
                        el = E(k)
                        parent.append(el)
                        aux(el, i)
                elif isinstance(v, dict):
                    el = E(k)
                    parent.append(el)
                    aux(el, v)
                elif v is None:
                    el = E(k)
                    parent.append(el)
                elif isinstance(v, bool):
                    _v = str(v).lower()
                    parent.append(E(k, _v))
                else:
                    parent.append(E(k, str(v)))

        aux(doc, tree)
        return doc

    @staticmethod
    def yname_ns_func(parent_namespace, element, yname):
        # to keeps things simple, we augment every key with a complete namespace map
        ns_map = [(None, element._namespace)]
        if element._yang_type == "identityref" and element._changed():
            # configured identityref (i.e. points to a valid identity)
            ns_map.append(
                (element._enumeration_dict[element]["@module"], element._enumeration_dict[element]["@namespace"])
            )
        return yname, tuple(ns_map)

    @classmethod
    def encode(cls, obj, filter=True):
        """return the lxml objectify tree for the pybind object"""
        ietf_tree_xml_func = make_generate_ietf_tree(pybindIETFXMLEncoder.yname_ns_func)
        tree = ietf_tree_xml_func(obj, flt=filter)
        preprocessed = XmlYangDataSerialiser().preprocess_element(tree)
        return cls.generate_xml_tree(obj._yang_name, obj._yang_namespace, preprocessed)

    @classmethod
    def serialise(cls, obj, filter=True, pretty_print=True):
        """return the complete XML document, as pretty-printed string"""
        doc = cls.encode(obj, filter=filter)
        return etree.tostring(doc, pretty_print=pretty_print).decode("utf8")


def make_generate_ietf_tree(yname_ns_func):
    """
    Convert a pyangbind class to a format which encodes to the IETF JSON
    specification, rather than the default .get() format, which does not
    match this specification.

    Modes of operation controlled by with_defaults:

      - None: skip data set to default values
      - WithDefaults.IF_SET: include all explicitly set data

    The implementation is based on draft-ietf-netmod-yang-json-07.

    Resulting namespaced key names can be customised via *yname_func*
    """

    def generate_ietf_tree(obj, parent_namespace=None, flt=False, with_defaults=None):
        generated_by = getattr(obj, "_pybind_generated_by", None)
        if generated_by == "YANGListType":
            return [generate_ietf_tree(i, flt=flt, with_defaults=with_defaults) for i in obj.itervalues()]
        elif generated_by is None:
            # This is an element that is not specifically generated by
            # pyangbind, so we simply serialise it how we would if it
            # were a scalar.
            return obj

        d = {}
        for element_name in obj._pyangbind_elements:
            element = getattr(obj, element_name, None)
            yang_name = getattr(element, "yang_name", None)
            yname = yang_name() if yang_name is not None else element_name

            # adjust yname, if necessary, given the current namespace context
            yname = yname_ns_func(parent_namespace, element, yname)

            generated_by = getattr(element, "_pybind_generated_by", None)
            if generated_by == "container":
                d[yname] = generate_ietf_tree(
                    element, parent_namespace=element._namespace, flt=flt, with_defaults=with_defaults
                )
                if not len(d[yname]):
                    del d[yname]
            elif generated_by == "YANGListType":
                d[yname] = [
                    generate_ietf_tree(i, parent_namespace=element._namespace, flt=flt, with_defaults=with_defaults)
                    for i in element.itervalues()
                ]
                if not len(d[yname]):
                    del d[yname]
            else:
                if with_defaults is None:
                    if flt and element._changed():
                        d[yname] = element
                    elif not flt:
                        d[yname] = element
                elif with_defaults == WithDefaults.IF_SET:
                    if element._changed() or element._default == element:
                        d[yname] = element
        return d

    return generate_ietf_tree


class pybindIETFXMLDecoder(object):
    """
    IETF XML decoder for pybind object tree deserialisation.
    Use the `decode()` method to return an pyangbind representation of the yang object.
    """

    @classmethod
    def decode(cls, xml, bindings, module_name):
        # using a custom parser to strip comments (so we don't handle them later)
        parser = objectify.makeparser(remove_comments=True, remove_blank_text=True)
        doc = objectify.fromstring(xml, parser=parser)
        return cls.load_xml(doc, bindings, module_name)

    @staticmethod
    def load_xml(d, parent, yang_base, obj=None, path_helper=None, extmethods=None):
        """low-level XML deserialisation function, based on pybindJSONDecoder.load_ietf_json()"""
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
                    raise pybindLoadUpdateError("update was attempted to a node that " + "was not unique")
            else:
                # in this case, we cannot check for an existing object
                obj = base_mod_cls(path_helper=path_helper, extmethods=extmethods)

        for child in d.getchildren():
            # separate element namespace and tag
            qn = etree.QName(child)
            namespace, ykey = qn.namespace, qn.localname

            # need to look up the key in the object to find out what type it should be,
            # because we can't tell from the XML structure
            attr_get = getattr(obj, "_get_%s" % safe_name(ykey), None)
            if attr_get is None:
                raise AttributeError("Invalid attribute specified (%s)" % ykey)
            chobj = attr_get()

            if chobj._yang_type == "container":

                if hasattr(chobj, "_presence"):
                    if chobj._presence:
                        chobj._set_present()

                pybindIETFXMLDecoder.load_xml(
                    child, None, None, obj=chobj, path_helper=path_helper, extmethods=extmethods
                )

            elif chobj._yang_type == "list":
                if not chobj._keyval:
                    raise NotImplementedError("keyless list?")

                # we just need to find the key value to add it to the list
                key_parts = []
                add_kwargs = {}
                for pkv, ykv in zip(chobj._keyval.split(" "), chobj._yang_keys.split(" ")):
                    add_kwargs[pkv] = child[ykv]
                    key_parts.append(str(child[ykv]))
                key_str = " ".join(map(str, key_parts))
                if key_str not in chobj:
                    nobj = chobj.add(**add_kwargs)
                else:
                    nobj = chobj[key_str]

                # now we have created the nested object element, we add other members
                pybindIETFXMLDecoder.load_xml(
                    child, None, None, obj=nobj, path_helper=path_helper, extmethods=extmethods
                )

            elif hasattr(chobj, "_pybind_generated_by") and chobj._pybind_generated_by == "TypedListType":
                # NOTE: this is a little curious, because we are relying on the coercion of types
                #   i.e. lxml will "identify" the type based on its own internal model of Python
                #   types, see: https://lxml.de/2.0/objectify.html#how-data-types-are-matched
                # There are limitations which need to be addressed, e.g. hexadecimal strings.
                # Already, we have a stringify-fallback: if we fail on the first attempt then
                # try again as a pure string (if its allowed).
                try:
                    chobj.append(child.pyval)
                except ValueError:
                    if six.text_type in chobj._allowed_type:
                        chobj.append(str(child.pyval))
                    else:
                        raise

            else:
                if chobj._is_keyval is True:
                    # we've already added the key
                    continue

                val = child.text
                if chobj._yang_type == "empty":
                    if child.text is None:
                        val = True
                    else:
                        raise ValueError("Invalid value for empty in input XML - key: %s, got: %s" % (ykey, val))

                elif chobj._yang_type == "identityref":
                    if ":" in val:
                        _, val = val.split(":", 1)

                if val is not None:
                    set_method = getattr(obj, "_set_%s" % safe_name(ykey), None)
                    if set_method is None:
                        raise AttributeError("Invalid attribute specified in XML - %s" % (ykey))
                    set_method(val)

        return obj


class pybindJSONDecoder(object):

    @staticmethod
    def load_json(
        d, parent, yang_base, obj=None, path_helper=None, extmethods=None, overwrite=False, skip_unknown=False
    ):

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
                    raise pybindLoadUpdateError("update was attempted to a node that " + "was not unique")
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
                raise AttributeError("JSON object contained a key that" + "did not exist (%s)" % (key))
            elif child is None and skip_unknown:
                # skip unknown elements if we are asked to by the user`
                continue
            chobj = child()

            if hasattr(chobj, "_presence"):
                if chobj._presence:
                    chobj._set_present()

            set_via_stdmethod = True
            pybind_attr = getattr(chobj, "_pybind_generated_by", None)
            if pybind_attr in ["container"]:
                if overwrite:
                    for elem in chobj._pyangbind_elements:
                        unsetchildelem = getattr(chobj, "_unset_%s" % elem)
                        unsetchildelem()
                pybindJSONDecoder.load_json(
                    d[key], chobj, yang_base, obj=chobj, path_helper=path_helper, skip_unknown=skip_unknown
                )
                set_via_stdmethod = False
            elif pybind_attr in ["YANGListType", "list"]:
                # we need to add each key to the list and then skip a level in the
                # JSON hierarchy
                list_obj = getattr(obj, safe_name(key), None)
                if list_obj is None and skip_unknown is False:
                    raise pybindJSONDecodeError("Could not load list object " + "with name %s" % key)
                if list_obj is None and skip_unknown is not False:
                    continue

                ordered_list = getattr(list_obj, "_ordered", None)
                if ordered_list:
                    # Put keys in order:
                    okeys = []
                    kdict = {}
                    for k, v in six.iteritems(d[key]):
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
                    pybindJSONDecoder.load_json(
                        d[key][child_key],
                        parent,
                        yang_base,
                        obj=parent,
                        path_helper=path_helper,
                        skip_unknown=skip_unknown,
                    )
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
                raise pybindLoadUpdateError("unknown pybind type when loading JSON: %s" % pybind_attr)

            if set_via_stdmethod:
                # simply get the set method and then set the value of the leaf
                set_method = getattr(obj, "_set_%s" % safe_name(key))
                set_method(d[key], load=True)
        return obj

    @staticmethod
    def check_metadata_add(key, data, obj):
        keys = [six.text_type(k) for k in data]
        if ("@" + key) in keys:
            for k, v in six.iteritems(data["@" + key]):
                obj._add_metadata(k, v)

    @staticmethod
    def load_ietf_json(
        d, parent, yang_base, obj=None, path_helper=None, extmethods=None, overwrite=False, skip_unknown=False
    ):
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
                    raise pybindLoadUpdateError("update was attempted to a node that " + "was not unique")
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
                for k, v in six.iteritems(d[key]):
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
                pybindJSONDecoder.load_ietf_json(
                    d[key],
                    None,
                    None,
                    obj=chobj,
                    path_helper=path_helper,
                    extmethods=extmethods,
                    overwrite=overwrite,
                    skip_unknown=skip_unknown,
                )
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
                            keystr = ""
                            kwargs = {}
                            for pkv, ykv in zip(this_attr._keyval.split(" "), this_attr._yang_keys.split(" ")):
                                kwargs[pkv] = elem[ykv]
                                keystr += "%s " % elem[ykv]
                            keystr = keystr.rstrip(" ")
                            if keystr not in this_attr:
                                nobj = this_attr.add(**kwargs)
                            else:
                                nobj = this_attr[keystr]
                        else:
                            k = elem[this_attr._yang_keys]
                            if k not in this_attr:
                                nobj = this_attr.add(k)
                            else:
                                nobj = this_attr[k]
                        pybindJSONDecoder.load_ietf_json(
                            elem,
                            None,
                            None,
                            obj=nobj,
                            path_helper=path_helper,
                            extmethods=extmethods,
                            overwrite=overwrite,
                            skip_unknown=skip_unknown,
                        )
                        pybindJSONDecoder.check_metadata_add(key, d, nobj)
                    else:
                        # this is a leaf-list
                        std_method_set = True
            else:
                std_method_set = True

            if std_method_set:
                get_method = getattr(obj, "_get_%s" % safe_name(ykey), None)
                if get_method is None and skip_unknown is False:
                    raise AttributeError("JSON object contained a key that " + "did not exist (%s)" % (ykey))
                elif get_method is None and skip_unknown is not False:
                    continue
                chk = get_method()
                if chk._is_keyval is True:
                    pass
                else:
                    val = d[key]
                    if chk._yang_type == "empty":
                        # A 'none' value in the JSON means that an empty value is set,
                        # since this is serialised as [null] in the input JSON.
                        if val == [None]:
                            val = True
                        else:
                            raise ValueError("Invalid value for empty in input JSON " "key: %s, got: %s" % (ykey, val))

                    if chk._yang_type == "identityref":
                        # identityref values in IETF JSON may contain their module name, as a prefix,
                        # but we don't build identities with these as valid values. If this is the
                        # case then re-write the value to just be the name of the identity that we
                        # should know about.
                        if ":" in val:
                            _, val = val.split(":", 1)

                    if val is not None:
                        set_method = getattr(obj, "_set_%s" % safe_name(ykey), None)
                        if set_method is None:
                            raise AttributeError("Invalid attribute specified in JSON - %s" % (ykey))
                        set_method(val)
                pybindJSONDecoder.check_metadata_add(key, d, get_method())
        return obj
