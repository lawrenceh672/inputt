import msvcrt
from datetime import timedelta, date
import os

"""
Standalone functions, used by different classes
"""
def OneTouchInput(prompt): #Reads one keypress and returns it no enter needed
	print(prompt)
	pressed = msvcrt.getch() #Get the keyboard input
	if pressed == b'\x00':
		pressed = msvcrt.getch() #Push it out now
		if pressed == b';': #Not too sure where this comes from, but its what it outputs
			return "F1"
	if pressed == b'\x1b': 
		raise Exception("User Cancelled")
	if pressed == b'\xe0':
		pressed = msvcrt.getch() #Push it out now
		if pressed == b'\x86': #Not too sure where this comes from, but its what it outputs
			return "F12"
	returnValue = pressed.decode()
	return returnValue

def getFileName(default): #Gets a filename from the user, using enter to select the default string
	pressed = OneTouchInput("Enter file name({}). Enter for default, Escape to cancel".format(default))
	if pressed == 'esc': #User wants to cancel selecting a file
		print("Cancelling")
		raise Exception("Input Cancelled by user")
	if pressed == '\r':
		print("Default {} selected.".format(default))
		return default

	filename = input("Type your filename: ") #start print the characted selected and add the remaining input onto it
	return filename

def enumerateAndSelect(dict): #take a dictionary, print out an enumerated list and get the user to select a number #C
	#check if its a list or dictionary being enumerated
	typer = str(type(dict))
	if typer == "<class 'list'>":
		for i, k in enumerate(dict): #Enumerate the list
			print("{}: {}".format(i, k))
			
		try:
			selection = OneTouchInput("Selection: ")
			selection = int(selection) #Get the index
			ret = dict[selection]
			return selection
		except Exception as e:
			print("{}".format(e))
			return None
	indexDict = {}
	for i, (k, v) in enumerate(dict.items()):
		print("{}: {}[{}]".format(i, k, v))
		indexDict[i] = k #Save the key of the dictionary corresponding to an enumeration
	
	try:
		selection = int(OneTouchInput("Select option: "))
		key = indexDict[selection]
		return key
	except Exception as e:
		print("{}".format(e))
		return None


def getDate(prompt, default): #Get a string input for a date from the user
	plantdate = input("{}. Enter for default[{}].".format(prompt, default))
	if plantdate == "":
		print("Default {} selected.".format(default))
		return default

	plantdate = plantdate.split("-")
	try:
		year = int(plantdate[0])
		month = int(plantdate[1])
		day = int(plantdate[2])
		plantdate = date(year,month,day)
	except KeyError:
		print("Invalid input, leaving {}".format(default))
		return default
	except ValueError as v: #Something wrong with the date
		print("{}".format(v))
		return default
	return plantdate

def getInteger(prompt, default, minimum, maximum):
	#Prompt the user for a number and raise exceptions if its an invalid input
	val = input("{} Enter to default to {} z to cancel.".format(prompt, default))
	try:
		if val == "":
			return default
		if val == "z" or val == "Z":
			raise Exception("User Cancelled")
		val = int(val)
		if val > maximum:
			raise Exception("Exceed max value")
		if val < minimum:
			raise Exception("Below minimum")
	except ValueError as v:
		raise v
	return val



def enumeratedFileSelector(extension): #List all files with the given extension
	dir_path = r'.'
	files = []
	extension = "." + extension #to match output of splitext
	for path in os.scandir(dir_path):
		if path.is_file():
			root_extension = os.path.splitext(path)

			print("The output tuple", root_extension)
			fileroot = root_extension[0]
			fileextension =root_extension[1]
			if extension == fileextension:
				files.append(fileroot + fileextension)
	key = enumerateAndSelect(files)
	return files[key]