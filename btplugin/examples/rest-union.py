#!/usr/bin/env python

class T: pass

def MultiClassType(*args, **kwargs):
	types = kwargs.pop("types", False)
	print types
	class MultiClass(T):
		_type_list = types
		_selected_type = False
		def __new__(self, *args, **kwargs):
			if not types or not type(types) == type([]) or len(types) == 0:
				raise ValueError, "need a list of types"

			#print "hit here"
			type_found = False
			#for t in types:
			#	try:
			#print args
			#print kwargs
			#obj = str.__new__(self, *args, **kwargs)

			for t in types:
				try:
					obj = t.__new__(self, *args, **kwargs)
					self._selected_type = t
					type_found = True
					break
				except:
					pass
			self.__bases__ = (t)
			print "was ok with %s" % t
			#break
			#	except:
			#		pass
			if not type_found:
					raise ValueError, "object that was created was invalid"

			return obj

		def __init__(self, *args, **kwargs):
			#print "hit here"
			return self._selected_type.__init__(*args, **kwargs)
	return type(MultiClass(*args, **kwargs))

x = MultiClassType(types=[list,str])

#y = x("10")


#print y

