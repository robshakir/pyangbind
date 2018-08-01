# Serialisation and Deserialisation of YANG-modelled Data


PyangBind provides a set of helper classes which allow data to be loaded from, or serialised to a loaded data format. At the time of writing, the supported formats are:

 * XML - defined in [RFC 7950](https://tools.ietf.org/html/rfc7950)
 * IETF JSON - defined in `draft-ietf-netmod-yang-json-08`.
 * OpenConfig/PyangBind JSON - which does not currently have a published specification.

In the future, it is expected that an XML serialisation module may be required, given the current bias of devices towards this serialisation format.

## Contents
 * [Loading from JSON - Entire Module](#load-json-module)
   - [Load Functions](#load-functions)
     - [`loads` and `loads_ietf`](#json-loads)
     - [`load` and `load_ietf`](#json-load)
   - [Example Loading (Deserialisation)](#example-load)
     - [Loading OpenConfig/PyangBind JSON-encoded Data](#example-load-oc)
     - [Loading IETF-JSON encoded Data](#example-load-ietf)
 * [Loading Data into an Existing Instance](#load-json-existing)
   - [Example of Loading to Existing Instances](#load-json-existing-example)
 * [Serialising Data into XML](#serialising-xml)
 * [Serialising Data into JSON](#serialising-json)
   - [Example Serialisation](#example-serialisation)
 * [Example Code](#example-code)

## Loading from JSON - Entire Module <a name="load-json-module"></a>

The module `pyangbind.lib.pyangbindJSON` provides a wrapper around the encoder and decoder classes that are defined in `pyangbind.lib.serialise`. These methods are heavily biased towards loading an entire module into a new instance of the data tree.

The functions `loads`, `load`, `loads_ietf` and `load_ietf` are analagous to the Python `json` module's functions. The `loads.*` functions load from a string which is expected to be valid JSON, whereas the `load.*` functions load from a file name that is specified to the modules.

### Load Functions <a name="load-json-module"></a>

#### `loads(data, python_module, class_name)` and `loads_ietf(data, python_module, class_name)` <a name="json-loads"></a>

The arguments to the `loads` functions are expected to be:
 * `data` - a JSON-encoded string that can be loaded using Python's `json.load()` function.
 * `python_module` - the module within which the class that is to be instantiated is defined. In the case that `-o <filename>` is used, then this is `filename` as this code is a Python module that can be loaded with `import`. In the case that `--split-class-dir <directory>` has been used then it is `directory`.
  * `class_name` - the name of the Python class that is found within `module`. This is the safe name (i.e., Python-safe - using no reserved Python keywords and substituting hyphens for underscores) of the YANG module that has been compiled - e.g., `openconfig_bgp`.

These functions return a PyangBind class instance with the data from `data` loaded into it.

#### `load(filename, python_module, class_name)` and `load_ietf(filename, python_module, class_name)` <a name="json-load"></a>

The arguments to the `load` and `load_ietf` functions are identitical to those of the `loads` functions, other than the `filename` argument is a path to a file that can be loaded using `open(filename, 'r')`.

These functions return a PyangBind class instance with the data from `filename` loaded.

### Example Loading (Deserialisation) <a name="example-load"></a>

With a simple module - such as the following:

```yang
module simple_serialise {
    yang-version "1";
    namespace "http://rob.sh/yang/test/ss";
    prefix "ss";

    container a-container {
        leaf a-value {
            type int8;
        }
    }

    list a-list {
        key "the-key";

        leaf the-key {
            type string;
        }
    }
}
```

And bindings generated using:

```
$ pyang --plugindir $PYBINDPLUGIN -f pybind -o sbindings.py simple_serialise.yang
```

#### Loading OpenConfig/PyangBind JSON-encoded Data <a name="example-load-oc"></a>

An example instance of data for the above module encoded as PyangBind JSON looks like the following:

```json
{
    "a-container": {
        "a-value": 8
    },
    "a-list": {
        "entry-one": {
            "the-key": "entry-one"
        },
        "entry-two": {
            "the-key": "entry-two"
        }
    }
}
```

To load this, using `load` and `loads` the following code can be used:

```python
#!/usr/bin/env python

import pprint
import pyangbind.lib.pybindJSON as pbJ
import sbindings

pp = pprint.PrettyPrinter(indent=4)

loaded_object = pbJ.load("json/simple-instance.json", sbindings, "simple_serialise")
pp.pprint(loaded_object.get(filter=True))

string_to_load = open('json/simple-instance.json', 'r').read().replace('\n', '')
loaded_object_two = pbJ.loads(string_to_load, sbindings, "simple_serialise")
pp.pprint(loaded_object_two.get(filter=True))
```

In both cases, the `python_module` name used is the name of the bindings file generated (`sbindings`) and the modulename is as specified in the YANG module (i.e., `simple_serialise`).

Both loading methods will return the same output:

``python
{   'a-container': {   'a-value': 8},
    'a-list': {   u'entry-one': {   'the-key': u'entry-one'},
                  u'entry-two': {   'the-key': u'entry-two'}}}
```

#### Loading IETF JSON-encoded Data <a name="example-load-ietf"></a>

Loading IETF encoded data is almost identical, other than using the `loads_ietf` and `load_ietf` functions in place of `loads` and `load` respectively.

The corresponding example IETF-encoded JSON object for the above data is:

```json
{
    "simple_serialise:a-container": {
        "a-value": 8
    },
    "simple_serialise:a-list": [
        {"the-key": "entry-one"},
        {"the-key": "entry-two"}
    ]
}
```

This can be loaded in the same way using the following Python:

```python
# Load an instance from an IETF-JSON file
loaded_ietf_obj = pbJ.load_ietf("simple-instance-ietf.json", sbindings,
                                  "simple_serialise")
pp.pprint(loaded_ietf_obj.get(filter=True))

# Load an instance from an IETF-JSON string
string_to_load = open('json/simple-instance-ietf.json', 'r').read().replace('\n',
                                                                         '')
loaded_ietf_obj_two = pbJ.loads_ietf(string_to_load, sbindings,
                                                "simple_serialise")
pp.pprint(loaded_ietf_obj_two.get(filter=True))
```

Again, the data loaded is idential to that shown above.

## Loading Data into an Existing Instance <a name="load-json-existing"></a>

In a number of cases, it is desirable to load data from a serialised JSON input into an existing set of PyangBind classes - such as when accepting input from an external API. Doing this requires direct access of the `pyangbind.lib.serialise` classes, rather than the `pyangbind.lib.pybindJSON` helper functions. The relevant functions are those within `pybindJSONDecoder` - particularly `load_ietf_json` and `load_json`.

In order to use these functions (which are generally directly-called by the corresponding `pyangbind.lib.pybindJSON` functions - then there is a requirement to specify an already existing object, and skip the class instantiation stage of the loading functions.

When calling the load functions, the following format is expected to load into an existing object:

```python
load_json(input_data, None, None, obj=existing_object, path_helper=path_helper,
                extmethods=extmethods, overwrite=overwrite):
load_ietf_json(input_data, None, None, obj=existing_object, path_helper=path_helper,
					extmethods=extmethods, overwrite=overwrite)
```

Where:
  * `input_data` is a iterable object that corresponds to loaded JSON data.
  * `existing_object` is the object that should be loaded into - i.e., an instantiated set of PyangBind classes.
  * `path_helper`, `extmethods` - are the corresponding XPathHelper and extension methods that are to be used if required. In the case that these do not differ from the parent, they will be inherited.
  * `overwrite` determines whether the existing instance's data should be overwritten by the loaded data.

#### Example of Loading to Existing Instances <a name="load-json-existing-example"></a>

Using the same module as above, with the loaded instance in question (defining `/a-list[the-key='entry-one']` and `/a-list[the-key='entry-two']` then data can be loaded using the following `load_json` call:

```python
data_to_load = json.load(open('json/simple-instance-additional.json','r'))
pybindJSONDecoder.load_json(data_to_load, None, None, obj=existing_instance)
```

The `existing_instance` object is modified in-place, and hence the list acquires the additional `entry-three` data defined in the `simple-instance-additional.json` file:

```python
pp.pprint(existing_instance.a_list.keys())
# Outputs:
# [u'entry-two', u'entry-three', u'entry-one']
```

## Serialising Data into XML <a name="serialising-xml"></a>

In order to serialise a PyangBind class instance JSON, the `pybindIETFXMLEncoder` class defined in `pyangbind.lib.serialise` can be used. There are two relevant class methods `pybindIETFXMLEncoder.serialise` and `pybindIETFXMLEncoder.encode`,
which emit a string or an [`lxml.objectify`](https://lxml.de/objectify.html) instance, respectively.

 ```
 pybindIETFXMLEncoder.serialise(obj, filter=<bool>, pretty_print=<bool>)
 ```

  * `obj` - which is a PyangBind class instance that is to be dumped. It is expected to have a `get` method, hence be a list or a container.
  * `filter` - analagous to the `filter` argument to a PyangBind class' `get` method (see the documentation relating to generic methods), which determines whether the entire tree, or just the changed elements are to be dumped.
  * `pretty_print` - determines whether to apply pretty-printing to the emitted XML string (e.g. newlines and 2-space indentation).

 ```
 pybindIETFXMLEncoder.encode(obj, filter=<bool>, pretty_print=<bool>)
 ```

  * The `obj` and `filter` arguments are as per `pybindIETFXMLEncoder.serialise`.

## Serialising Data into JSON <a name="serialising-json"></a>

In order to serialise a PyangBind class instance into JSON, the `dump`, `dumps` functions defined in `pyangbind.lib.pybindJSON` are used. These functions take a `mode` keyword argument which determines whether they dump IETF-specified JSON or PyangBind JSON. 

 ```
 dump(obj, filename, indent=<int>, filter=<bool>, skip_subtrees=<list>, mode="default")
 ```
  
  * `obj` - which is a PyangBind class instance that is to be dumped. It is expected to have a `get` method, hence be a list or a container.
  * `filename` - the file to which the JSON should be written.
  * `indent` - the number of spaces to use to indent the JSON.
  * `filter` - analagous to the `filter` argument to a PyangBind class' `get` method (see the documentation relating to generic methods), which determines whether the entire tree, or just the changed elements are to be dumped.
  * `skip_subtrees` - a list of paths (absolute rather than relative) that should be pruned from the output JSON. This is useful if multiple output files are used to save data instances.
  * `mode` - a string specifying the JSON encoding to be output -- currently either "default" or "ietf".

 ```
 dumps(obj, indent=4, filter=True, skip_subtrees=[], select=False, mode="default")
 ```
 * The `obj`, `indent`, `filter`, `skip_subtrees` and `mode` arguments of dumps are as per `dump`.
 * `select` - when provided is expected to be a dictionary of the form `{ "element_name": value }`. When this is specified only elements where `obj.element_name == value` are output. This is useful when using query parameters to select subsets of an object, or list.

### Example Serialisation <a name="example-serialisation"></a>

In order to serialise an instance of the `simple_serialise` module used above - the following call is used:

```python
pyangbindJSON.dumps(existing_instance, filter=True)
```

This outputs the entire module as JSON:

```json
{
    "a-list": {
        "entry-two": {
            "the-key": "entry-two"
        }, 
        "entry-three": {
            "the-key": "entry-three"
        }, 
        "entry-one": {
            "the-key": "entry-one"
        }
    }
}
```

The JSON format can be switched to IETF-encoded JSON by using the `mode="ietf"` argument to dumps.

To select an entry from the list where the `the-key` leaf is equal to "entry-one" (although this is a gratiutous example), the `select` dictionary can be used:

```python
pbJ.dumps(existing_instance.a_list, select={'the-key': 'entry-one'}, mode="ietf")
```

This outputs only the `entry-one` output of the list being shown:

```json
[
    {
        "simple_serialise:the-key": "entry-one"
    }
]
```

## Example Code <a name="example-code"></a>

The example used throughout this document is included under `docs/example/simple-serialise`.

