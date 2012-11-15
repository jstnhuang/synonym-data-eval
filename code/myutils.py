def addToDictWithFn(dict, key, value, addFunction):
  if key in dict:
    dict[key] = addFunction(dict[key], value)
  else:
    dict[key] = value

def addToDict(dict, key, num):
  addToDictWithFn(dict, key, num, lambda x, y: x+y)
