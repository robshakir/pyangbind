# Extension Methods in PyangBind

PyangBind is designed both as a means to generate data instances for YANG modules, but also as a software component that can be used in an  NMS implementation. To that end, there can be requirements to tie methods to particular data instances in the tree.

The extension methods (`extmethods`) functionality provides a means to tie arbitrary methods to a particular path in the tree.

## Contents

 * [Initialisation of classes with `extmethods`](#initialisation)
 * [Example calls with `extmethods`](#example-calls)

## Initialising Classes with `extmethods` <a name="initialisation"></a>

To use extension methods, the PyangBind bindings must be generated with `--use-extmethods`. This ensures that the `extmethods` dictionary is propagated from parent to child objects as they are instantiated.

The `extmethods` dictionary is of the form:

```python
  {
    "/path/to/object/one": <Class Instance>,
    "/path/to/object/two": <Class instance>
  }
```

Where `/path/to/object/one` is defined as the XPATH to the object that the method is to be bound to *without* any filtering attributes. That is to say, for `/bgp/global/config/as` the path specified is simply `/bgp/global/config/as` whereas for `/bgp/neighbors/neighbor[peer-addr='192.0.2.1']/config/peer-as` then the path specified is `/bgp/neighbors/neighbor/config/peer-as`. It is not possible to bind an extension method to a single instance.

Each object, as it is instantiated, then consults the `extmethods` dictionary, if it finds an entry which corresponds to its exact path, it inherits all methods of the class instance provided - and will proxy any calls to itself to that class. The names of the methods are prefixed by an underscore in order to avoid collisions between actual data element names and method names.

## Example Calls with `extmethods` <a name="example-calls"></a>

If one has the following class definition:

```python

from openconfig import openconfig_bgp

class BgpNeighborHelper(object):
  def soft_reset(self, *args, **kwargs):
    # Do a soft reset of the neighbor
    pass

  def hard_reset(self, *args, **kwargs):
    # Do a hard reset of the neighbor
    pass
```

A set of PyangBind classes (e.g., OpenConfig BGP) can be initialised with an `extmethods` dictionary that provides a mapping between an instance of the `BGPNeighborHelper` class and an XPATH expression. For example, between the `config/enabled` leaf of each BGP neighbor and this class:

```python
bgp_helper =  BGPNeighborHelper()
extmethods = {
      '/bgp/neighbors/neighbor/neighbor/config/enabled': bgp_helper
}

ocbgp = openconfig_bgp(extmethods=extmethods)
```

Each entry within the `/bgp/neighbors/neighbor` list would have methods named `soft_reset` and `hard_reset` bound to their `config/enabled` leaf.

i.e., a hard reset or soft reset could be initiated by calling:

```python
ocbgp.bgp.neighbors.neighbor["192.0.2.1"].config.enabled._hard_reset()
ocbgp.bgp.neighbors.neighbor["192.0.2.1"].config.enabled._soft_reset()
```

When this call is made, the instance of the `BgpNeighborHelper` class named `bgp_helper` (which was supplied in the `extmethods` dictionary) will receive a call to the `soft_reset` or `hard_reset` method).

In addition to the arguments and keyword arguments that are supplied to the function (which are directly proxied through), two additional `kwargs` are added:

 * `caller` - this is a list which provides the components of the path of the actual object that the method was called against. For example in the above case this would correspond to `/bgp/neighbors/neighbor[peer-addr="192.0.2.1"].config.enabled` - and hence be `['bgp', 'neighbors', 'neighbor[peer-addr='192.0.2.1'], 'config', 'enabled']`. This allows disambiguation of calls that may come from multiple sources.
 * `path_helper` which provides a reference to the `path_helper` class that is being used by the classes. This can allow the `extmethod` to retrieve the data instance that called it if required. 
