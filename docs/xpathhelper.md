# XPATH and Data Tree Structure in PyangBind

 * [Overview](#overview)
 * [PyangBind's XPathHelper Classes](#xpathhelpercls)
 * [Usage of YANGPathHelper](#yangpathhelper)

## Overview <a name="overview"></a>

YANG data models describe a tree structure - where there is a single root for all modules, and each module creates schema nodes (e.g., containers or leaves) at that root. Essentially (based on YANG's historical ties to XML) this tree structure is conceptually an XML document - and hence XPATH expressions are used to provide references between different elements in the tree.

For example:

```yang

leaf reference {
  type leafref {
    path "/path/to/another/node";
  }
}

augment "/bgp" {
  uses some-new-grouping;
}
```

Both the augment and leafref statements here utilise XPATH expressions to refer to a remote node. When the value of a leafref is set then there is a requirement to check the value it is set to against the path that it refers to.

## PyangBind's XPathHelper Classes <a name="xpathhelpercls"></a>

To allow such references to be looked up, all PyangBind classes take an argument of `path_helper` which points to an object that they can use to resolve an XPATH expression into the data instances that that path refers to.

Generically, this helper class is described in `pyangbind.lib.xpathhelper` as the `PyangbindXpathHelper` class. This is a skeleton class (or interface, essentially) - that specifies the methods that PyangBind classes expect of this helper module. These are:

* `register(self, path, object_ptr, caller=False)` - this method is called when a PyangBind object is created such that a pointer between the `path` argument and the object referred to by `object_ptr` can be maintained by the XPathHelper class. The `caller` argument specifies the path to the object that is making the `register()` call - with the logic that the `path` argument may be relative in some cases.
* `unregister(self, path, caller=False)` - this function is the partner to `register()` and is called when a PyangBind object is removed to remove the mapping for its path.
* `get(self, path, caller=False)` - this function is used by PyangBind to retrieve all data nodes that correspond to a certain path.

It is intended that there can be multiple implementations of the XPathHelper interface such that one can use it to provide database backing if required (e.g., the XPathHelper class' `register` method could be used to serialise the corresponding data instances and insert them into a database).

## PyangBind's YANGPathHelper Class

`pyangbind.lib.xpathhelper` provides an implementation of an XPathHelper class named `YANGPathHelper`. This class implements an in-memory mapping between paths and the corresponding PyangBind object. It does this by constructing a lightweight XML document of the form:

```xml
<root>
  <bgp object_ptr='(str)'>
    <neighbors object_ptr='(str)'>
      <neighbor peer-addr='192.0.2.1' object_ptr='(str)'>
        ...
      </neighbor>
    </neighbors>
  </bgp>
</root>
```

The `object_ptr` attribute of each XML Element provides a reference to an entry in `_library` dictionary which stores references to the PyangBind classes. The contents of the document can be viewed using the `tostring()` method of any YANGPathHelper instance.

The YANGPathHelper provides a `get()` and `get_unique()` method - the latter raises an exception if there is >1 object corresponding to the path that is specified.

## Usage of YANGPathHelper <a name="yangpathhelper"></a>

To initialise a YANGPathHelper class and use it with PyangBind-generated classes, the bindings must have been specified with the `--use-xpathhelper` argument. This ensures that the bindings are configured to pass the `path_helper` reference to one another as new classes are instantiated.

In order to then use the YANGPathHelper, an instance should be created and then handed to the PyangBind class as it is created through the `path_helper` kwarg:

```python
>>>
>>> from openconfig import openconfig_bgp
>>> from pyangbind.lib.xpathhelper import YANGPathHelper
>>>
>>> ph = YANGPathHelper()
>>> ob = openconfig_bgp(path_helper=ph)
>>>
```

Following this initialisation, the classes are then utilised as per the normal operation:

```python
>>> peer = ob.bgp.neighbors.neighbor.add("192.0.2.1")
>>> peer.config.peer_as = 15169
```

After creating an entry such as this, it is then possible to view the data using the standard `.get()` method, and see the XML document that has been created by the `YANGPathHelper` `ph` object:

```python
>>> print peer.get(filter=True)
{'neighbor-address': u'192.0.2.1', 'config': {'neighbor-address': u'192.0.2.1', 'peer-as': 15169}}
>>> print ph.tostring(pretty_print=True)
<root>
  <bgp obj_ptr="cedd3b87-edf1-11e5-92c1-acbc32aad1a5">
    <neighbors obj_ptr="cee14035-edf1-11e5-a7be-acbc32aad1a5">
      <neighbor obj_ptr="d329332b-edf1-11e5-9868-acbc32aad1a5" neighbor-address="192.0.2.1">
        <route-reflector obj_ptr="d3294b63-edf1-11e5-b14d-acbc32aad1a5">
...
```

It is rare that there is a requirement to interact directly with this XML. Rather the `get()` method of the `ph` object can now be utilised to retrieve values by their path.

For instance, if another peer is added (`10.0.0.1`, `config.peer_as = 6643`), then the following XPATH expressions retrieve the possible neighbors, and a particular neighbor's AS number:

```
>>> ph.get("/bgp/neighbors/neighbor/neighbor-address")
[u'192.0.2.1', u'10.0.0.1']
>>> ph.get("/bgp/neighbors/neighbor[neighbor-address='192.0.2.1']/config/peer-as")
[15169]
>>> ph.get_unique("/bgp/neighbors/neighbor[neighbor-address='10.0.0.1']/config/peer-as")
6643
```

The `get()` method will return a list of all objects that match the expression, whereas `get_unique` will return an individual object.

When looking up a certain neighbor, it is possible to utilise the `_parent` attribute of a particular object to traverse up the tree to retrieve a wider object. For instance:

```python
>>> peer_as = ph.get_unique("/bgp/neighbors/neighbor[neighbor-address='10.0.0.1']/config/peer-as")
>>> peer_as._parent._parent.get(filter=True)
{'neighbor-address': u'10.0.0.1', 'config': {'neighbor-address': u'10.0.0.1', 'peer-as': 6643}}
```

No action is required  to ensure that objects unregister themselves as they are removed from the data tree:

```python
>>> ob.bgp.neighbors.neighbor.delete("10.0.0.1")
>>> ph.get("/bgp/neighbors/neighbor/neighbor-address")
[u'192.0.2.1']
```
