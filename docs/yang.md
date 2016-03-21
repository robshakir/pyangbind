# Python to YANG mapping

PyangBind makes a number of design decisions about how to map YANG data types of Python types, and how to carry the additional attributes that are required for serialisation and deserialisation; and other interaction with YANG-modelled data in Python.

 * [High Level Design for Mapped Classes](#hld) - how PyangBind handles YANG classes
 * [Items With No Direct Type Mapping](#nodirect) - Classes defined by PyangBind to represent YANG types.
 * [config false](#configfalse) - Special properties of `config false` items.
 * [YANG Data Types and Feature Support](#yangfeature) - An overview of the YANG types and features supported in PyangBind


## High-Level Design for Mapped Classes <a name="hld"></a>
Where possible, a built-in Python type is utilised for each class - for example, mapping a YANG `string` to Python `unicode`. All methods of `unicode` are kept such that the YANG `string` can be manipulated as per a standard Python string.

However, running `type(yang_string)` will yield that the type of the string is a `<class 'pyangbind.lib.yangtypes.YANGBaseClass'>`. PyangBind wraps each class in a meta-class which provides a number of other attributes. Particularly, elements such as storing the original YANG name of the object, tracking its path in the data tree, determining whether it has changed from its default, its namespace etc. These are defined in `pyangbind.lib.yangtypes` as a part of the `YANGBaseClass`.

Each type is dynamically generated at instantiation time using the `YANGDynClass` function. This function takes the relevant arguments and generates a dynamic type which can be used to represent the YANG data type.

## Items with no Direct Type Mapping <a name="nodirect"></a>

Some YANG types, e.g., `leaf-list`, do not have a direct analogue in Python (a `leaf-list` is a Python `list` which restricts the type/values of items that can be added to it). To this end, `pyangbind.lib.yangtypes` defines a number of classes which provide restrictions such as those that are required for a `leaf-list`. The types defined are:

 - `RestrictedPrecisionDecimalType` - used for YANG's `decimal64` - this class represents a Decimal that can only have a restricted number of fractional digits (as specified by YANG's `fraction-digits` statement).
 - `RestrictedClassType` - used as a flexible wrapper around a number of native types to restrict their values. A dictionary of restrictions is provided to the class. Made up of entries specifying:
   * `pattern` - used for any type that can be restricted using a regular expression.
   * `range`  - used for any type that can be restricted using a range of possible numeric values.
   * `length` - used for any type where the length of the input can be restricted.
   * `dict_key` - used for `enumeration` and `identityref` types - a dictionary is provided and the valid values are restricted to keys of the supplied dictionary. Each dictionary value can hold metadata elements such as `@namespace` and `@defining_module` which are used in serialisation.
 - `TypedListType` - which is used for leaf-list values where the only values in the list must correspond to the types allowed in the `leaf-list` `type` statement.
 - `YANGListType` - implements a YANG list as a keyed data structure (internally a Python `dict`), which can only hold instances of a particular class (which represents the list's children), and the key value must be valid within the enclosed object.
 -  `YANGBool` - a boolean type. This is generally required because `bool` is not extensible in Python.
 - `ReferenceType` - a type represeting a `leafref` which provides a lookup against the data tree for valid values, and allows pointer `leafref` items.

## `config false` Elements <a name="configfalse"></a>

PyangBind objects are generically set through simply defining the value using `container.leaf = value`, however, for `config false` elements, PyangBind restricts how these can be set by the progammer. The intention of this behaviour is to ensure that a user is specifically aware that they are setting a value that is not intended to be writable in the module. However, back-end code may need to populate such values.

To set a `config false` leaf, the setter method must be accessed directly, this can be done through the method `_set_X` where X is the Python-safe name of the element to be set (e.g., `total-paths` becomes `total_paths` in the `openconfig_bgp.global.state` container). Attempting to set the `total_paths` value directly will result in an `AttributeError` being raised. For example:

```python
>>>ocbgp.bgp.global_.state.total_paths = 500
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
AttributeError: can't set attribute
>>> ocbgp.bgp.global_.state._set_total_paths(500)
>>> ocbgp.bgp.global_.state.total_paths
500
```

## YANG Data Types and Feature Support <a name="yangfeature"></a>

PyangBind does not currently try and be feature complete against the YANG language. Contributions to add new features are appreciated. The table below attempts to map the design choices that PyangBind makes, and provide pointers to tests which demonstrate how this functionality can be used:

 **Type**            | **Sub-Statement**   | **Supported Type**      | **Unit Tests**
 --------------------|--------------------|--------------------------|---------------
 **binary**          | -                   | [bitarray](https://github.com/ilanschnell/bitarray)           | tests/binary
 -                   | length              | Supported           | tests/binary
 **bits**            | -                   | Not supported           | N/A
 -                   | position            | Not supported           | N/A
 **boolean**         | -                   | YANGBool                | tests/boolean-empty
 **empty**           | -                   | YANGBool                | tests/boolean-empty
 **decimal64**       | -                   | [Decimal](https://docs.python.org/2/library/decimal.html) | tests/decimal64
 -                   | fraction-digits     | Supported               | tests/decimal64
 **enumeration**     | -                   | Supported               | tests/enumeration
 **identityref**     | -                   | Supported               | tests/identityref
 **int{8,16,32,64}** | -                   | [numpy int](http://docs.scipy.org/doc/numpy/user/basics.types.html) | tests/int
 -                   | range               | Supported               | tests/int
 **uint{8,16,32,64}**| -                   | [numpy uint](http://docs.scipy.org/doc/numpy/user/basics.types.html) | tests/int
 -                   | range               | Supported               | tests/int
 **leafref**         | -                   | Supported               | tests/xpath/...
 **string**          | -                   | *str*                   | tests/string
 -                   | pattern             | Using python *re.match* | tests/string
 -                   | length              | Supported using *len*   | tests/string
 **typedef**         | -                   | Supported               | tests/typedef
 **container**       | -                   | *class*                 | tests/*
 **list**            | -                   | YANGList                | tests/list
 **leaf-list**       | -                   | TypedList               | tests/leaf-list
 **union**           | -                   | Supported               | tests/union
 **choice**          | -                   | Supported               | tests/choice
 **rpc**             | -                   | Supported                  | tests/rpc
 **extension**             | -                   | Supported                  | *TODO*
