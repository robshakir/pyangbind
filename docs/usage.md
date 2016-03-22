# PyangBind CLI usage

PyangBind adds a number of command-line options to Pyang:

 * [Output options](#output-options) - `-o`, `--split-class-dir`
 * [XPathHelper options](#xpathhelper) - `--use-xpath-helper`
 * [Extensions options](#extensions) - `--interesting-extension`
 * [RPC options](#rpcs) -- `--build-rpcs`
 * [Extended Methods](#extmethods) -- `--use-extmethods`
 * [YANG Module Arguments](#yangmods)

## Output Options <a name="output-options"></a>

PyangBind has three output modes:
  * A file for all generated classes:
    * Written to `stdout`
    * Written to a single .py file
  * A Python module hierarchy.

### stdout

When no options are specified, PyangBind will write a single file to `stdout`, this is considered to be self-contained and can be redirected to a particular location by the shell.

### -o <filename>

When `-o <filename>` is specified (a standard Pyang option), then the single file output is redirected to the filename specified. Within this single file, to ensure that class names remain unique then the class naming used for all non-top-level classes is of the form `yc_<lastcontainername>_<modulename>__<object path, replacing "/" with "_">`. Clearly, this results in relatively complex class names such as `yc_config_openconfig_bgp__bgp_global_config` corresponding to the `/bgp/global/config` container in the OpenConfig BGP module.

### --split-class-dir <directory>

When `--split-class-dir <directory>` is specified then PyangBind will create a Python module hierarchy in `directory`. This will result in each level of hierarchy in the YANG module becoming its own sub-module.

For example, the OpenConfig BGP module has the following hierarchy:

```
module: openconfig-bgp
   +--rw bgp!
      +--rw global
      |  +--rw config
      |  |  +--rw as           inet:as-number
      |  |  +--rw router-id?   inet:ipv4-address
      |  +--ro state
      |  |  +--ro as                inet:as-number
      |  |  +--ro router-id?        inet:ipv4-address
      |  |  +--ro total-paths?      uint32
      |  |  +--ro total-prefixes?   uint32
```

When `--split-class-dir openconfig` is specified, then the class corresponding to the `bgp` container will be output in a Python module named `openconfig`. This module can then be imported via:

```python
from openconfig import bgp

ocbgp = bgp()
```

At deeper levels of hierarchy a class is output within a sub-module of the same name, such that to import the BGP `global` container class, then the `global_` module is imported, with the `global_` class within it being instantiated:

```python
from openconfig.bgp import global_    # global is a reserved word
from openconfig.bgp.global_ import config

bgp_global = global_.global_()
bgp_global_config = config.config()
```

## XPathHelper Options <a name="xpathhelper"></a>

If `--use-xpath-helper` is _not_ specified, then all XPATH references throughout the classes generated will act as strings - such that any element that relies in XPATH (`when`/`leaf-ref` statements etc.) will simply take on any value that they are set to.

When` --use-xpath-helper` is specified, then references to the `path_helper` object that is supplied at the time of class instantiation will be passed to all of the classes children. This object is then used to provide lookup capabilities for XPATH expressions. This behaviour is further documented in (the XPathHelper documentation](xpathhelper.md).

## Extension Options

When `--interesting-extension <modulename>` is specified then PyangBind will look for extensions from the module name provided that are included in the YANG module. These extensions are then placed in a dictionary that is accessible through each class' `_extensions()` method.

For example, with the following YANG:

```yang
import example-extension { prefix "egx"; }

leaf description {
  egx:descr-flag "d";
  egx:descr-order 100;
  type string;
  description
    "A human-readable text description";
}
```

If `--interesting-extension example-extension` is specified, then the `description` object's `_extensions()` method will return a dictionary:

```python
>>> print(cls.description._extensions())
{u'example-extensions': {u'descr-flag': u'd', u'descr-order': u'100'}}
```

These extensions can then be consumed by the program manipulating the classes.

## RPC Options <a name="rpcs"></a>

By default, PyangBind will ignore all RPC definitions within a YANG file. When `--build-rpcs` is specified, then each RPC, with its corresponding `input` and `output` containers will be generated into a class which corresponds to `<modulename>_rpc` at the root of the data tree.

See the [RPC documentation](rpc.md) for more detail as to the usage of generated RPC classes.

## Extended Methods <a name="extmethods"></a>

When the `--use-extmethods` command-line option is specified, PyangBind will propagate the dictionary that is provided as the option `extmethods=` argument during class initialisation to the children objects. If this option is not specified, this option is always `False`.

See the [Extension Methods](extmethods.md) documentation for detail of this functionality.

## YANG Module Arguments <a name="yangmods"></a>

As per Pyang - when using the PyangBind plugin, the YANG modules to be compiled are specified on the command line, along with `-p <path>` to specify where Pyang should look for other modules that are included. However, unlike Pyang, PyangBind needs to be able to resolve all base typedefs - in some cases this may involve specifying additional modules to be compiled if they included `identity` or `typedef` statements. In the case that a definition cannot be resolved, PyangBind will not generate bindings and will return a list of the known definitions at the time of the error. The current error language is not particularly user friendly - if PyangBind is unable to resolve a type definition or identity statement, please open a bug with the YANG modules being used such that this can be examined.
