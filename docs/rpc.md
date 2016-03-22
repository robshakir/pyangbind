# RPCs in PyangBind

PyangBind generates bindings for RPCs that are specified within a YANG module. The assumption is made that an RPC is not bound to any particular location within the data tree (the YANG 1.1 `action` statement is intended to meet this requirement). To this end, bindings are generated within a module named `<yang module name>_rpcs`.

All RPC bindings have the property `register_paths` set to `False`. This results in them never using a `path_helper` object that is handed to them for `register()` or `unregister()` purposes. A `path_helper` class will still be used to resolve `leafref` values (and other XPATH expressions) if required.

An class generated for an RPC has two member containers - `input` and `output` as per the specification provided in RFC6020. The corresponding data definitions are within these two elements (which act as per YANG containers).

## Contents

* [Example RPC](#examplerpc)  
	* [Generating an RPC `input`](#exinput)
	* [Parsing an RPC `output`](#exoutput)
	* [Example Code](#excode)

## Example RPC <a name="examplerpc"></a>

An example simple RPC could be defined as:

```yang
    rpc test {
        input {
            container input-container {
                leaf argument-one {
                    type string;
                }

                leaf argument-two {
                    type uint8;
                }
            }
        }

        output {
            leaf response-id {
                type uint32;
            }

            list elements {
                leaf response-value {
                    type string;
                }
            }

        }
    }
```

In this definition, the RPC `test` has an input that takes a `container` with two arguments (`argument-one` and `argument-two`) specified within it. It outputs an object that has a single `response-id` and a list of `elements` wtihin the reply. This list is not keyed (RPC outputs are defined to be `config false`).

### Generating an RPC Input <a name="exinput"></a>
To generate an input for an RPC, the `input` container can be directly imported. If the example module above is generated with `--split-class-dir` into a module directory named `rbindings` then, for example:

```python
from rbindings.simple_rpc_rpc.test.input import input
```

The `input` class can be instantiated and populated as per any other PyangBind class that represents a container:

```python
rpc_input = input()
rpc_input.input_container.argument_one = "test_call"
rpc_input.input_container.argument_two = 32
```

The object generated can be serialised to IETF JSON as per any other container using `dumps` from `pyangbind.lib.pybindJSON`:

```python
>> print(dumps(rpc_input, mode="ietf"))
{
    "simple_rpc:input-container": {
        "argument-two": 32, 
        "argument-one": "test_call"
    }
}
```

### Parsing an RPC Output <a name="exoutput"></a>

In a similar manner, an RPC output can be read back into the corresponding `output` class using the standard deserialisation functionality in PyangBind. For example:

```python
from rbindings.simple_rpc_rpc.test.output import output
rpc_output = output()
fn = os.path.join("json", "rpc-output.json")
json_obj = json.load(open(fn, 'r'))
pybindJSONDecoder.load_ietf_json(json_obj, None, None, obj=rpc_output)
```

The output class can then be manipulated and/or read in Python:

```python
>>> print(rpc_output.response_id)
32
```

### Example Code

The RPC example here can be found in `docs/example/simple-rpc`.

 