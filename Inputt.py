from pynput.keyboard import Key, Listener
import time
from parameters import Parameters
from guiThread import GUIThread
import numpy as np
from globals import threads, globals
import math
from PIL import Image
import os
import sys

class Inputt():
	#just like input, but non blocking and flags keystrokes
	def __init__(self):
		self.active = False
		self.keydown = False #If any key is being pressed
		self.lastKey = ''
		self.lines = ['start'] #Log all lines ended by an enter
		self.enterLine = False
		self.oneTouchKeys = [] #A list of characters the user can press without pressing enter to input in
		self.output = "" #Stores the string as the user types it
		self.menuItems = {} #Detail the menu structure
		self.menuLevel = [] #Start at the root menu
		self.endProgram = False #Keep running till the user escapes to the end
		self.statusVariables = {} #{"name": "value"}
		self.pressed = None
		self.promptText = "" #the bottom line prompt prompt> output
		self.functionReturn = None #After the user selects a function, this is its return value, set it back to None after its displayed
		self.menuSelections = [] #A list of all menu options available, set up by the print menu function
		self.gui = GUIThread(80,25) #Start running the GUI, and update it as necessary
		self.gui.start()
	def __str__(self):
		ret = ""
		if self.keydown:
			keydown = "key {} is being pressed".format(self.lastKey)
		else:
			keydown = "unpressed"
		if self.enterLine:
			enterLine = "Enter is pressed, user entered".format(self.output)
		else:
			enterLine = "User is still typing, current line {}".format(self.pressed)
		ret += "Inputt is active: {}. {} lines entered. Keyboard is {}\n".format(self.active, len(self.lines), keydown)
		ret += "Current menu system:\n"
		ret += self.printFullMenu()
		ret += "Currently in menu {}".format(self.menuLevel)
		return ret

	def start(self): #Start listening
		self.output = ""  #Start collecting the users input
		if self.active == True:
			return
		self.listener = Listener(on_press=self.on_press,on_release=self.on_release)
		self.listener.start() #start the keyboard listener thread
		self.active = True
		print("Keyboard listening ON")
	def stop(self): #Stop the listener thread
		try:
			self.active = False
			self.enterLine = False
			self.listener.stop()
		except Exception: #In case its called when the thread is already gone
			pass
		print("Keyboard listener OFF")
	def on_press(self, key):
		#if self.keydown == True: #Want to avoid long presses for one touch processing
		#	return
		self.keydown = True
		if key == Key.enter:
			#Check if this is a menu selection
			if self.output in self.menuSelections:
				print("Menu option {} selected".format(self.output))
				self.menuLevel.append(self.output)	#Advance into this menu option
			self.lines.append(self.output)
			print("Line {} entered".format(self.output))
			self.output = ""
			self.enterLine = True #Flag a line of input is ready, flip it back once processed
			return
		elif key == Key.esc:
			self.output = "Escape"
			self.enterLine = True
			self.lines.append(self.output)
			return
		elif self.oneTouchKeys == ['ALL']:
			try:
				key = key.char
			except:
				pass #Try to convert to character, or just pass on the Key.whatever
			self.output = key
			self.lines.append(self.output)
			self.output = ""
			self.enterLine = True
			return
		elif key == Key.backspace:
			if self.output == "":
				return #Dont backspace no input, it'll erase things off the field of input
			self.output = self.output[:-1] #chop off the end of the output string
			print("\b \b", end = "") #Backspace erase and backspace again to reset the cursor
			return
		#Now lets separate alphanumeric keys from others
		try:
			self.output += key.char
			print(key.char, end = "") #Echo the keypress
			self.updatePrompt() #Update the buffer for the keypress
		except Exception as e:
			if key == Key.left:
				self.output = "<-"
			elif key == Key.right:
				self.output = "->"

		#Now check if this keypress is a one touch key
		if self.output in self.oneTouchKeys:
			self.lines.append(self.output) #Store it as a line the history list
			self.enterLine = True
			#advance the menu option one level in
			self.menuLevel.append(self.output)	#Need to appened menu levels even if its not a one touch key
		self.lastKey = key
	def on_release(self, key):
		self.keydown = False

	def printFullMenu(self):  #Output the whole menu system
		ret = ""
		for menu, text in self.menuItems.items():
			menu = list(menu) #Bc we cant hash lists so the dictionary needs this converted
			name = text[0]
			ret += "{}. {}\n".format(menu, name)
		return ret

	def getTitle(self):
		#Return the title of the current menu level
		ret = self.menuItems[tuple(self.menuLevel)][0]
		return ret
	def updateMenuItem(self, menuPath, message):
		try:
			func = self.menuItems[tuple(menuPath)][1]
			self.menuItems[tuple(menuPath)] = (message, func)
		except Exception as e:
			print("Inputt error {}".format(e))
			print(self)		
	def addMenuItem(self, id, name, func):
		#id = menu index, ie 1. or 1.1, 4.1, 4.2 etc
		#1. Option 1 = [1]
		#2. heading 1 = [2]
		#   2.1 Option 2 = [2,1]
		#   2.2 Option 3 = [2,2]
		#   2.3 Heading 2 = [2,3]
		#      2.3.1 Option 4 = [2,3,1]
		#      2.3.2 Option 5 = [2,3,2]
		#3. Option 6 = [3]
		#4. Heading 3 = [4]
		#   4.1 Option 7 = [4,1]
		#   4.2 Option 8 = [4,2]
		#   4.3 Heading 4 = [4,3]
		#      4.3.1 Option 9 = [4,3,1]
		#and so on 
		typer = str(type(name))
		if typer == "<class 'numpy.ndarray'>": #change it to a PIL image
			name = Image.fromarray(name)
		self.menuItems[tuple(id)] = (name, func)
	def deleteMenuPath(self, menuPath):
		#First remove the any current options on this menu path
		for k in list(self.menuItems.keys()):
			#Check if the menu path is the root menu of this menu option
			if len(k) == len(menuPath) +  1:
				#Assume match is true,only set it false when known for sure
				match = True
				#Its the right length for menuPath to be the root menu
				for index, mp in enumerate(menuPath):
					if mp == k[index]: #Match letter by letter
						continue
					else: #No match
						match = False
						break
				if match == True:
					#If this menu option is one level from the menuPath, remove it for adding later
					del self.menuItems[k]

	def enumerationSelection(self, x):
		return lambda : [x]  #Return the item selected
	def enumerateAndSelect(self, items): #process function points to the function to executed when the user makes their selection
		self.gui.updatingBuffer(bufferUpdating = True) #Set the drawing and buffer locks
		self.deleteMenuPath(self.menuLevel) #Clear the menu options below it must be dynamic
		self.oneTouchKeys = [] #We'll remake the list while dynamically creating the menu entry
		self.gui.clearText() #Prep the screen for new things

		typer = str(type(items)) #Multiple data types can be enumerated, but lets make one function to handle them all
		#first make the selection names based on the object type
		if typer == "<class 'parameters.Parameters'>":
			#Make a list off all the items in the parameter object
			ParametersList = items.toList()
			for index, i in enumerate(ParametersList, 1):
				added = self.menuLevel.copy()
				added.append(str(index)) #Make the new, dynamic menu entry, starting at 1
				name = str(i)
				func = self.enumerationSelection(str(items.get(ParametersList[index - 1]))) #This is in a list going into another list FIX
				self.addMenuItem(added, name, func)

		if typer == "<class 'dict'>":
			rowcount = 0
			for index, (key, val) in enumerate(items.items(),1):
				added = self.menuLevel.copy()
				#name = items[key]
				added.append(str(index)) #Make the new, dynamic menu entry, starting at 1
				func = self.enumerationSelection(key)
				menuText = "{}".format(key)
				self.addMenuItem(added, menuText, func)
				indent = len(menuText) + 3
				line_number = rowcount
				rowcount += self.gui.addToBuffer(indent, line_number, val)

		if typer == "<class 'list'>":
			rowcount = 0
			for index, i in enumerate(items, 1):
				added = self.menuLevel.copy()
				added.append(str(index)) #Make the new, dynamic menu entry, starting at 1
				name = items[index - 1] #Because we started from 1 but lists start from zero
				rowcount += self.gui.addToBuffer(0,rowcount,i)
				func = self.enumerationSelection(i)
				self.addMenuItem(added, name, func)

		self.enterLine = False
		self.output = "" #Prep the indicator variables to accept new input and prepare to select from the list
		self.printMenu() #Display it and set one touch keys, if less than 10 items being displayed
		title = self.getTitle()
		self.gui.setOutputPane(["Viewing {}".format(title)])
		self.gui.updatingBuffer(False) #We know this thread is done updating the buffer
		selection = self.nextLine() #And then get the users selection
		ret = self.outputProcessed()
		if ret[0] == 'Returning to menu level':
			return False
		return ret

	def goUpOneLevel(self):
		if self.menuLevel == []: #Were at the root menu
			self.endProgram = True
			return
		self.menuLevel = self.menuLevel[:-1] #Go up one level
	
	def Escape(self): #The all important escape key, go up one menu level for everything, defined in inputt
		self.goUpOneLevel()
		ret = ["Returning to menu level".format(self.menuLevel)]
		#Need to check the menu level and activate outputvisual for running threads, if we go to the level that spawned the thread
		
		runningThreads = threads.iterable()
		for rt in runningThreads:
			threadMenuLevel = rt.P.get("Visualization menu level") #Check this running thread and if we just went to its creation menu level restart the visualization output
			if threadMenuLevel == self.menuLevel:
				rt.outputVisual = True #Enable it
			else:
				rt.outputvisual = False

		return ret
	def printMenu(self): 
		#Prints the menu and calculates metrics like selection options and screen size while doing it
		self.gui.updatingBuffer(bufferUpdating = True) #Set the drawing and buffer locks
		escapeOption = self.menuLevel.copy()
		escapeOption.append("Escape") #So hitting the Escape key brings us one menu level, escaping up
		self.addMenuItem(escapeOption,"Go up one level", self.Escape) #Put in the 
		oneTouchCount = 0 #If its above 10 we need to cancel one touch keys
		y = 1 #Top row is for menu id status, count the rows needed to display the menu
		title = str(self.menuLevel) + ": " + str(self.menuItems[tuple(self.menuLevel)][0]) #Level: Level's name
		x = int((self.gui.numberOfColumns - len(title))/2)
		self.gui.addToBuffer(x,0,title)
		print(title)
		#Count the size of the printed menu and resize it for the printed menu
		nameLength = 80
		#Calculate the size of the menu and prompt
		current_row_height = 1 #Increase for the height of the image
		#Clear the menu selection lists for this new menu
		self.oneTouchKeys = [] #If less than 10, do one touches, 
		self.menuSelections = [] #But still need to know what the selection options are
		for menu, text in self.menuItems.items():
			menu = list(menu) #Bc we cant hash lists so the dictionary needs this converted
			menuPath = menu[0:-1] #The path is everything except the last element the user selects as a onetouchkey
			if menuPath == self.menuLevel:
				try:
					menuOneTouch = menu[-1] #Select the one touch key menu option and the previous one touch key
				except Exception as e:
					continue
				name = text[0] #Check for row height
				typer = str(type(name))
				if typer == "<class 'numpy.ndarray'>":
					i = Image.fromarray(i)
					typer =  str(type(i))
				if typer == "<class 'PIL.Image.Image'>": #Its an image
					size = name.size
					y += 2 #Because Im using thumbnails defined as twice row size for menu selection
				if typer == "<class 'str'>":
					y += 1
					
				nameLength = max(len(text),nameLength) #Fix this, not quite right
		print("Printing menu {} lines".format(y))
		#if y > self.gui.numberOfRows or nameLength > self.gui.numberOfColumns:
		self.gui.resize(nameLength, y)

		#Add the items in the menu and prompt to the gui
		y=1
		for menu, text in self.menuItems.items():
			menu = list(menu) #Bc we cant hash lists so the dictionary needs this converted
			menuPath = menu[0:-1] #The path is everything except the first element
			if menuPath == self.menuLevel:
				try:
					menuOneTouch = menu[-1] #Select the one touch key menu option and the previous one touch key
				except Exception as e:
					continue
				name = text[0] #Check for row height
				text = "{}. {}".format(menuOneTouch, name)
				nameLength = max(len(text),80)
				print(text)
				#Add it to the CLI GUI as well as printing it
				typer = str(type(name))
				if typer == "<class 'PIL.Image.Image'>": #Its an image
					maxSize = self.gui.getImageThumbnailSize()
					name.thumbnail(maxSize)
					self.gui.addToBuffer(0,y, menuOneTouch + ". ")
					y += self.gui.addToBuffer(5,y, name)
				else:
					y += self.gui.addToBuffer(0, y, text) #add the text or image

				self.oneTouchKeys.append(menuOneTouch)
				self.menuSelections.append(menuOneTouch) #This list stays, onetouch disappears over 10 selection options
				oneTouchCount += 1 
	
		if oneTouchCount > 10: #Cant type 16 for instance without onetouching 1 first so we need to disable it
			self.oneTouchKeys = []
		self.gui.divideLineInputVOutput = y + 3 #To maximize screen space for output, start output right beneath the input&prompt
		#Add the prompt to the buffer
		self.gui.addToBuffer(0, y + 1, "Select Option(1-{})".format(oneTouchCount))
		self.gui.updatingBuffer(False) #Done writing the menu
	def outputProcessed(self):
		self.gui.updatingBuffer(bufferUpdating = True) #Set the drawing and buffer locks
		#Lets get the last line entered by the user
		lastLineEntered = self.lines[-1]
		#Lets get the menuItem the user has selected
		menuItem = self.menuItems[tuple(self.menuLevel)]

		#Lets process the user input
		name = menuItem[0] #unpack the tuple
		func = menuItem[1]

		#Do the escape function if escape is pressed, later try to handle this automatically as part of the function execution
		if lastLineEntered == "Escape":
			func = self.Escape

		if func != None: #run the function if supplied
			self.functionReturn = func()
			#Clear the screen to put in the new output and prep it for the next menu printing
			while self.gui.drawingScreen():
				pass
			self.gui.clearText() #Prep the text array for a new set of characters
			self.printMenu() #Add the menu into the buffer array
			#Set the window size based on the output size and write in the output from the menu function
			self.gui.setOutputPane(self.functionReturn)
		self.enterLine = False	#Get ready for a nextline
		self.gui.updatingBuffer(False) #Open for screen drawing now
		return self.functionReturn #True if a function ran, false otherwise
	def nextLine(self): #returns a string the user typed or false if still checking
		#Lets reset the interface window to sync it with the user input
		#Flag the prompt to draw the gui screen
		if self.enterLine: #The enter key was pressed, get the last line recorded
			return self.lines[-1]
		self.start()
		#Lets see if any running thread started from this current menu level, if so show the the threads output in the output pane
		runningThreads = threads.iterable()
		images = []
		displayThread = False #Presume no thread to display
		for rt in runningThreads:
			threadMenuLevel = rt.P.get("Menu Level")
			if threadMenuLevel == self.menuLevel:
				displayThread = rt #We have a thread created at this menu level, we will display it in the output pane


		while self.enterLine == False: #Wait for the user to type a selection
			for rt in runningThreads:
				threadMenuLevel = rt.P.get("Menu Level")
				if threadMenuLevel == self.menuLevel:
					displayThread = rt #We have a thread created at this menu level, we will display it in the output pane
				else:
					displayThread = False
			if displayThread:
				imageUpdated = displayThread.P.isUpdated("outputImage") #Dont rewrite it unless theres a new image to put in
				if imageUpdated:
					images.clear()
					img = rt.getOutputImage()
					images.append(img)
					self.gui.setOutputPane(images)
		self.stop() 
		return self.lines[-1] #Otherwise nothing
		
	def getFileName(self, default, ext = ""): #Gets a filename from the user, using enter to select the default string
		#Get the files from the current path
		Root_Path = globals.get("Root Path")
		items = os.listdir(Root_Path)

		fileList = []

		for name in items: #Peel off the files with the extension
			if name.endswith(ext):
				fileList.append(name)
		#select one of the files
		for cnt, fileName in enumerate(fileList, 1):
			sys.stdout.write("[%d] %s\n\r" % (cnt, fileName))
		
		fileSelected = self.enumerateAndSelect(fileList)
		fileSelected = Root_Path + fileSelected[0]
		return fileSelected

	def getString(self, promptText):
		self.prompt(promptText)
		ret = self.nextLine()
		return ret
	def getColor(self, defaults):
		self.prompt("Enter Red, Green, Blue for a color")
		(dR,dG,dB) = defaults
		red = self.getInteger("Enter red value", 0, 255, dR)
		green = self.getInteger("Enter green value", 0, 255, dG)
		blue = self.getInteger("Enter blue value", 0, 255, dB)
		return (red, green, blue)
	def getInteger(self, promptText, min, max, current):
		invalid = True
		ret = None
		self.oneTouchKeys = []
		self.output = ""
		while invalid:
			self.prompt("{}({}). {}-{}".format(promptText,current, min, max))
			userInput = self.nextLine()
			try:
				ret = int(userInput)
				if ret < min:
					self.prompt("Value too low, minimum {}".format(min))
				elif ret > max:
					self.prompt("Value too high, maximum {}".format(max))
				else:
					invalid = False
			except Exception as e:
				if userInput == "Escape":
					self.prompt("Cancelling")
					invalid = False
				else:
					self.prompt("Invalid input not an integer, try again")
		return ret

	def updatePrompt(self):
		while self.gui.drawingScreen(): #Its drawing wait until its done then update the buffer and make it draw again
			pass
		self.gui.updatingBuffer(True) #Tell the gui its drawing the buffer dont do anything
		#See if self.prompttext is longer than the screen, if so, write it across enough lines to show all the text
		text = "{}> {}".format(self.promptText, self.output)
		promptLength = len(text)
		#Now put the text into
		# code to pad spaces in string
		padding_size = self.gui.numberOfColumns
		res = text + " "*(padding_size - len(text))
		promptRow = self.gui.divideLineInputVOutput - 1
		self.gui.addToBuffer(0, promptRow, res)
		self.gui.updatingBuffer(False) #No longer updating, the GUI thread is clear to redraw the screen

	def prompt(self, message):
		#Clear the one touch keys as this isnt a menu option
		#self.oneTouchKeys = []
		#self.lines.append(self.output) #Recheck this, is this entering in a line, or is it just updating the prompt at the bottom of the input area?
		#self.output = ""
		#self.enterLine = False
		#Update the prompt message
		self.promptText = message

	def confirmAction(self, confirmText):
		self.prompt("Press Enter to confirm {}".format(confirmText))
		line = self.nextLine()
		if line == "":
			return True
		return False

	def shutdown(self): #Shut down the input/output threads
		self.gui.stop()
		self.stop()

	def anyKey(self, message):
		self.oneTouchKeys = ['ALL'] #A little flag to let the key press processory know to return a line with any key press
		if message == None:
			self.prompt("Press any key to continue")
		else:
			self.prompt(message)
		anykey = self.nextLine()
		self.oneTouchKeys = [] #Reset them so it doesnt keep doing anykey
		return anykey #Might be useful to know which key was pressed
	
	def clearImage(self):
		self.gui.clearImages()

	def getlastOutput(self):
		return self.gui.outputList
