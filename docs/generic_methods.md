# Generic Methods Provided through PyangBind

PyangBind's `YANGDynClass` function generates meta-classes around the class that is defined as the `base_type`/`base` when the class is generated. The wrapper that is provided gives a set of functions and variables that allow YANG-specific information to be stored alongside the value of the class.

Some of these methods are generically useful when handling the classes, as well as internally to PyangBind.

In general, methods are defined as `_<methodname>` such that clashes with the elements within YANG containers can be avoided - although for historical reasons, in some cases the `_` is omitted.

## Contents

 * [YANGDynClass Methods](#ydcmethods) - generic to all PyangBind wrapped objects other than those corresponding to YANG modules.
 * [YANG Container Methods](#containermethods) - methods defined for PyangBind objects corresponding to YANG `container` items.
 * [YANG List Methods](#listmethods) - methods defined for PyangBind objects corresponding to YANG `list` items.


## Methods/Variables Defined in YANGDynClass <a name="#ydcmethods"></a>

### `default()`

Where a YANG type has a default value specified, the default method returns this value. The actual class' value is set to the null value of the base class (e.g., `unicode` objets return `''`, `int` objects return 0), whereas the default value is stored in `_default`. If there is no default defined, then `_default` is set to False.

### `_changed()`

Returns `True` when the class (or a child of the class if it represents a container) has been set. This allows subsets of the data tree that have been manipulated to be retrieved as opposed to all elements.

### `yang_name()`

Returns the name of the data element as defined in the YANG module rather than the `safe_name` returned value.

### `_add_metadata()` & `_metadata`

The `_metadata` element is a dictionary which can stores any meta-data that was provided as part of the data instance. For example, the Juniper example JSON instance for BGP global configuration may be akin to:

```python
"config" : {
   "@router-id" : {
      "inactive" : true
   },
   "router-id" : "10.10.10.10"
}
```

In this case, the `router_id` member of the `config` class will have a dictionary of the form `{"inactive": True}` stored with it.

The `_add_metadata()` method allows new metadata to be added. The arguments expected are a key, followed by a metadata value, e.g.:

```python
config.router_id._add_metadata("inactive", True)
```

will add the metadata shown above.

### `_register_path()` & `_path()`

Both of these methods currently return the same data: a list defining the elements of the path to the data element in the tree. For example, the entry for `/bgp/neighbors/neighbor[peer-address='192.0.2.1']/config/peer-as` will return `['bgp', 'neighbors', 'neighbor[peer-address='192.0.2.1']', 'config', 'peer-as']`.

### `_yang_path()`

Returns the path to the YANG object as a string.

### `_namespace`

Returns the namespace (from the `namespace` statement) of the YANG module that defined the element.

### `_defining_module`

Returns the module name from the `module` statement of the YANG module that defined the element. This is used in a number of cases within IETF JSON serialisation/deserialisation.

### `_choice`

If the element is defined within a `choice` statement, then this value carries the name of the `case` that it is a part of. This is used to call `_unset_X` where X is the element's `safe_name` when a member of another `case` is set (since two `case` elements of a choice cannot co-exist).

### `_parent`

Returns a reference to the element's parent class - for example, if one has a list entry at `/bgp/neighbors/neighbor[peer-address='2001:DB8::1']/config/peer-as` then `_parent` of the `peer-as` object refers to the `config` object, and the corresponding `_parent` of the `config` object refers to the list entry for the neighbor.

This is generally useful in the cases where one has a `leafref` value that refers to the key of a list and the application requires the list entry itself (i.e., in this case one can do: `leafref_leaf._parent` to get to the list entry of a list).

### `_is_keyval`

Set to `True` if this value is the key of a list.

### `_is_config`

Set to True if the node is configurable within the YANG schema - reflecting the YANG `config` statement.

## YANG Container (`PybindBase`) defined Methods <a name="containermethods"></a>

### `elements()`

Returns a list of the names of the elements of the container. This can be used when iterating, although `for child in container` can also be used.

### `get(filter=<bool>)`

Returns a nested set of dictionaries that represent the current container. The filter argument provides a means to get only those elements that have changed during the current manipulation of the data tree (including being deserialised from a data instance):

```python
# Setup of data omitted
>> import pprint
>> pp = pprint.PrettyPrinter(indent=4)
>> pp.pprint(r.tables.get(filter=True))
{   'table': {   'AGGREGATE': {   'config': {   'table-name': u'AGGREGATE'},
                                  'table-name': u'AGGREGATE'},
                 'BGP': {   'config': {   'table-name': u'BGP'},
                            'table-name': u'BGP'},
                 'STATIC': {   'config': {   'table-name': u'STATIC'},
                               'table-name': u'STATIC'}}}
```

This may be used as an alternative to serialising/deserialising instances especially for debugging. In general, the serailisation classes will use this format as a intermediary to be able to retrieve data from the classes.

## YANG List Methods <a name="listmethods"></a>

PyangBind provides two special methods for YANG `list` objects:

### `add(<keyspec>)`

Adds a new entry to the list. In the case that the list is a keyed list - then the value returned is a reference to the newly created list entry. In the case that the list is not keyed, the value returned is the key value (a UUID) that has been defined internally by PyangBind.

The key specification can be of three forms:
  * A value representing the key - in the case of a list with a single key, then the entire value is used as a key.
  * A space-separated string representing multiple keys. In this case, the key ordering is as specified in the `key` leaf in the YANG module, and the string is split at each space. For example, a list two with a key specification of `key "srcip index"` supplies with `.add("192.0.2.1 1")` would set `srcip=192.0.2.1` and `index=1`. The key values will cast the split string into the relevant type for storage in the corresponding list entry.
  * A set of keyword arguments for each key. For example, if the same list as above were called with `.add(index=1, srcip="192.0.2.1")` then the keyword arguments for each key would be extracted. In this case, order does not matter.

### `delete(<keyspec>)`

Removes the key value specified by `keyspec` from the list. The logic for the format of `keyspec` is the same as `add`.

### `_new_item()`

In some cases it is preferable to create a valid object outside of the context of it being added to the list (for example, in cases where there is some action performed around the `add()` call by the program consuming PyangBind's classes). To this end, the `_new_item()` method (called as `yang_list._new_item())` returns an empty instance of a member of the list, which can be populated.

### `append(object)`

Where an item has been created without being added to the list, it can be added using the `append()` function. The object supplied as the `obj` argument is used to extract the list key which is to be used for the item. As per a standard Python `list` item's `append()` method, there is no return from this function.

