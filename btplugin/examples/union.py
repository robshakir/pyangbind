#!/usr/bin/env python

def UnionType(*args, **kwargs):
	expected_types = kwargs.pop("expected_types", False)
	if not expected_types or not type(expected_types) == type([]):
		raise AttributeError, "could not initialise union"
	if not len(args):
		return expected_types[0]
	else:
		for t in expected_types:
			try:
				return t(args[0])
			except ValueError:
				pass
		raise AttributeError, "specified argument did not match any union type"


t = UnionType(expected_types=[int,str])
x = UnionType("hello", expected_types=[int,str])


class foo(UnionType(expected_types=[int,str])):
	pass

g = foo()

g = foo()