# Errors thrown by PyangBind

**Note**: the functionality specified in this document is currently subject to some change. Feedback as to useful functionality is appreciated. Please open an issue.

PyangBind re-uses Python error types where possible, particularly:

 * `KeyError` will be raised when an element does not have a particular key. The arguments to this error are a string.
 * `ValueError` is raised when the supplied data does not match the YANG data type. This value is only raised where the input cannot be cast to the type that is stored in the data. For example, a YANG integer type (`int8`, `int16`, ... etc.) will accept `True` as an input but store the value `1`. This intentional and aims to provide a balance between duck-typing in Python, and the more strict typing in YANG:
 	* As of [docs@21/03/2016](https://github.com/robshakir/pyangbind/commit/0c28c057eeb7034c23c94a4e7ec09a9fd2ae00d0), the argument passed by PyangBind setters to ValueError is a dictionary - this can be accessed using code such as:
 	
 	```python
try:
    pybindobj.value = "anInvalidValue"
except ValueError as e:
    # Check the args and types, just in case we have
    # old bindings
    if len(e.args) and isinstance(e.args[0], dict):
        print "Hit a PyangBind ValueError"
        for k, v in e.args[0].iteritems():
            print "%s->%s" % (k, v)
    else:
        print unicode(e)
 				
 	```
 	* The keys of the dictionary are:
 		- `error-string`: a simple error string that provides some insight (but not all information) as to the type that was not matched. It will currently capture the original YANG type that was specified, but no additional restrictions.
 		- `generated-type`: the dynamic class specification that PyangBind tried to generate for this type - this is often unwieldy, but tends to be useful for debugging.
 		- `defined-type`: the simple defined type, resolved to module if it is not native that the leaf is. Again this does not include all information.
 * `AttributeError` will be raised when an invalid member of a YANG object is specified, or a method does not exist. In some cases, since PyangBind's meta-class defines some methods which are used to modify mutable objects in place (to capture changes) then `dir(...)` for the object may show methods that return `AttributeError` when they are passed to the super-class. 