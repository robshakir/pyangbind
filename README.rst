PyangBind
=========

PyangBind is a plugin for pyang which converts YANG data models into a Python class hierarchy, such that Python can be used to manipulate data that conforms with a YANG model.

This module provides the supporting classes and functions that PyangBind modules utilise, particularly:

* pyangbind.base.PybindBase - which is the parent class inherited by all container or module YANG objects.

* pyangbind.pybindJSON - which containers wrapper functions which can be used to help with serialisation of YANG to JSON.

* pyangbind.serialise.pybindJSONEncoder - a class that can be used as a custom encoder for the JSON module to serialise PyangBind class hierarchies to JSON.

* pyangbind.serialise.pybindJSONDecoder - a class that can be used as a custom decoder to load JSON-encoded instances of YANG models into a PyangBind class hierarchy.

* pyangbind.xpathhelper.YANGPathHelper - a class which can have objects registered against it, and subsequently retrieved from it using XPATH expressions. This module also includes parent classes that can be used to implement other helper modules of this nature.

* pyangbind.yangtypes: The various functions which generate python types that are used to represent YANG types, and some helper methods.

  - pyangbind.yangtypes.is_yang_list and is_yang_leaflist are self explainatory, but may be useful.

  - pyangbind.yangtypes.safe_name is used throughout PyangBind to determine how to map YANG element names into Python attribute names safely.

  - pyangbind.yangtypes.RestrictedPrecisionDecimalType - generates wrapped Decimal types that has a restricted set of decimal digits - i.e., can deal with fraction-digits arguments in YANG.

  - pyangbind.yangtypes.RestrictedClassType - generates types which wrap a 'base' type (e.g., integer) with particular restrictions. The restrictions are supplied as a dictionary, or with specific arguments if single restrictions are required. Currently, the restrictions supported are regexp matches, ranges, lengths, and restrictions to a set of values (provided as keys to a dict).

  - pyangbind.yangtypes.TypedListType - generates types which wrap a list to restrict the objects that it may contain.

  - pyangbind.yangtypes.YANGListType - generates types which wrap a class representing a container, such that it acts as a YANG list.

  - pyangbind.yangtypes.YANGBool - a boolean class.

  - pyangbind.yangtypes.YANGDynClass - generates types which consist of a wrapper (YANGDynClass) and a wrapped object which may be any other class. YANGDynClass is a meta-class that provides additional data on top of the attributes and functions of the wrapped class.

  - pyangbind.yangtypes.ReferenceType - generates types which can use a pyangbind.xpathhelper.PybindXpathHelper instance to look up values - particularly to support leafrefs in YANG.

Usage documentation for PyangBind itself can be found on GitHub: https://github.com/robshakir/pyangbind