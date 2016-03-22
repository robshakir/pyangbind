![#PyangBind](http://rob.sh/img/pyblogo_gh.png)

# PyangBind Documentation

If you haven't already - it's best to start with the README.md file in the main repository. This provides a quick-start guide to PyangBind, including a walk-through of how to use PyangBind to manipulate an OpenConfig model. Reading this will give some context around where you might want to start reading in this documentation.

## Documentation

The `docs` directory contains the following documents:

  * [Errors](errors.md) -- explains the errors that PyangBind classes will throw.
  * [Extension Methods](extmethods.md) -- usage and intention of the `extmethods` functionality in PyangBind
  * [Generic Methods](generic_methods.md) -- the methods that the PyangBind meta-class defines, as well as methods that are added for YANG-specific types such as `container` and `list`.
  * [RPC](rpc.md) -- explains PyangBind's support for the YANG `rpc` statement, and how one may use this functionality.
  * [Serialisation and Deserialisation](serialisation.md) -- covers how PyangBind's `lib.serialise` and `lib.pybindJSON` classes can be used to output and load instances of data that have been created with a program using PyangBind's classes.
  * [Usage](usage.md) -- documents the command-line switches that PyangBind uses.
  * [XPathHelper](xpathhelper.md) -- provides information relating to PyangBind's optional `XPathHelper` classes which are used to resolve XPATH expressions and can be used to traverse a data tree consisting on multiple models.
  * [YANG](yang.md) -- gives an overview of how various YANG language features are supported in PyangBind.

## Examples

In order to allow new users to quickly see how PyangBind might work for them, some examples are included in this directory:

  * [`example/oc-local-routing`](example/oc-local-routing) uses the OpenConfig `local-routing` module an example and shows how one can build static routes using this module. The main directory's README.md provides a worked example of this.
  * [`example/simple-rpc`](example/simple-rpc) shows how a YANG `rpc` definition can be manipulated when PyangBind classes are generated for it. The RPC document provides further explanation of this example.
  * [`example/simple-serialise`](example/simple-serialise) shows how PyangBind's serialisation and deserialisation capabilities work. The serialisation document walks through this example.

In order to understand some of the internals of PyangBind a bit better, the `tests` directory may also be useful - this provides numerous test cases intended to ensure PyangBind keeps working the way one would expect, but can be a valuable source of pointers as to how things might work.

## If you're stuck...

Please open an issue. The author (singular for the moment!) tries to help out where he can.