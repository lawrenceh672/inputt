"""
Every real world object modeled in this program is defined by a series of attributes and values.  This class creates an easy way to add and manage these
attributes, without created hand tailored code to modify and set it, the variable name is fed into the class and it exposes an interface
to change, record, validate input
"""
class Parameters(): #Holds values that define the dimensions and properties of anything, allows updates and saves old values
	def __init__(self, dict):
		self.p = dict
		self.iterableIndex = 0 #For the iterable function

	def __str__(self):
		line = ""
		#list each attribute, its value and description if available
		for name, values in self.p.items():
			desc = values[1]
			value = values[0]
			updated = values[2] #We're updating the Parameter attribute
			line += "{}({}) : {}. Updated = {}\n".format(name,desc,value, updated)
		return line
	def __len__(self):
		return len(self.p)
		
	def set(self, attribute, value):
		try:
			existing = self.p[attribute]
			desc = existing[1] #get the description
			self.p[attribute] = (value, desc, True)
		except KeyError:
			parameterType = str(type(value))
			if parameterType == "<class 'tuple'>":
				self.p[attribute] = (value[0],value[1],True)
			else:
				self.p[attribute] = (value, "No Description", False)
		
	def delete(self, attribute):
		try:
			del self.p[attribute]
		except Exception:
			pass

	def setDescription(self, attribute, description):
		try:
			existing = self.p[attribute]
			value = existing[0]
			isUpdated = existing[2]
			self.p[attribute] = (value, description, isUpdated)
		except KeyError:
			parameterType = str(type(value))
			if parameterType == "<class 'tuple'>":
				self.p[attribute] = (value[0], value[1], value[2])
			else:
				self.p[attribute] = (value, description, True)

	def get(self, key):
		try:
			ret = self.p[key]
			#Change the updated parameter to False, assuming that if we get this parameter, it is being processed
			value = ret[0]
			desc = ret[1]
			self.p[key] = (value,desc,False)
			ret = value
		except KeyError:
			print("{} not a valid parameter ".format(key))
			return None
		return ret

	def addTo(self, attribute, value): #When the value of the attribute is a list
		try:
			self.variable[attribute].append(value)
		except KeyError:
			print("{} not in the dictionary. Nothing changed".format(attribute))
		except Exception:
			print("Exception encountered add to variable list attribute")

	def changeParameters(self):
		index = enumerateAndSelect(self.p) #List the value, prompt the user for a selection returns the index for the dictionary
		parameterValue = self.p[index][0]
		description = self.p[index][1]
		parameterType = str(type(parameterValue))
		try:
			#List out the parameters and let the user select some to change
			if parameterType == "<class 'int'>":
				newVal = getInteger("Enter new value[{}]: ".format(parameterValue), 0, -1000000,1000000)
			if parameterType == "<class 'datetime.date'>":
				newVal = getDate("Enter new date YYYY-MM-DD.", parameterValue)
			if parameterType == "<class 'float'>":
				newVal = float(input("Enter new value[{}]: ".format(parameterValue)))
			if parameterType == "<class 'boolean'>":
				print("Changing boolean parameter type")
			self.p[index] = (newVal, description) #And now lets put it into master dictionary
		except Exception as e:
			print("{}, cancelling parameter change.".format(e))
			raise Exception("Cancelling change")

	def toCSV(self):
		ret = ""
		for k,v in self.p.items():
			ret += "{}[{}],".format(k, v[1])
		ret += "\n"
		for k,v in self.p.items():
			ret += "{},".format(v[0])
		ret += "\n"

	def toCSVHeader(self): #REturn a line with the variable names with description separated by commas
		ret = ""
		for k,v in self.p.items():
			ret += "{}[{}],".format(k, v[1])
		ret += "\n"
		return ret

	def toCSVData(self): #Return all the elements in the dictionary values comma separated
		ret = ""
		for k,v in self.p.items():
			ret += "{},".format(v[0])
		ret += "\n"
		return ret

	def iterable(self): #return the next parameter, return False at the end, then reset it
		ret = []
		for name, values in self.p.items():
			if values[0] is not None:
				ret.append(values[0])
		return ret

	def toList(self): #Return a list of all the items in the Parameters
		ret = []
		for name, values in self.p.items():
			ret.append(name)
		return ret
	
	def isUpdated(self, key):
		ret = self.p[key][2]
		return ret

