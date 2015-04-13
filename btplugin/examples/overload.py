
import numpy as np

def defineYANGDynClass(*args, **kwargs):
	base_type = kwargs.pop("base",int)
	class YANGDynClass(base_type):
		_changed = False

		def yang_set(self):
			return self._changed

		def __new__(self, *args, **kwargs):
			default = kwargs.pop("default", None)
			try:
				value = args[0]
			except IndexError:
				value = None

			obj = base_type.__new__(self, *args, **kwargs)
			if default == None:
				if value == None or value == base_type():
					obj._changed = False
				else:
					obj._changed = True
			else:
				if value == default:
					obj._changed = False
				else:
					obj._changed = True

			return obj
	return YANGDynClass(*args,**kwargs)


c = defineYANGDynClass(1,default=1,base=int)
d = defineYANGDynClass(2,base=int)
e = defineYANGDynClass(3,base=np.uint8)
f = defineYANGDynClass("hello",base=str)
g = defineYANGDynClass([],base=list)

print "%d, %d, %d, %s, %s" % (c,d,e, f, g)
print "%s, %s, %s, %s, %s" % (c.yang_set(), d.yang_set(), e.yang_set(), f.yang_set(), g.yang_set())

#print c.yang_set()
#print d.yang_set()
#print e.yang_set()

print (c+d)
print (d+e)



#c = YANGInt(1, default=1)
#d = YANGInt(2)
#e = YANGInt()

#print c.yang_set()
#print d.yang_set()
#print e.yang_set()

#print (c+d)
#print (d+e)


	# class YANGInt(int):
	# 	_changed = False

	# 	def yang_set(self):
	# 		return self._changed

	# 	def __new__(self, *args, **kwargs):
	# 		default = kwargs.pop("default", None)
	# 		try:
	# 			value = args[1]
	# 		except IndexError:
	# 			value = None

	# 		obj = int.__new__(self, *args, **kwargs)
	# 		obj._changed = True if (default == None and not value == None) \
	# 							or (not default == None and not value == default) \
	# 							else False
	# 		return obj