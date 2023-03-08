import threading
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import datetime
import cv2
from globals import threads
from workerthreads import workerThread
import time
import math 
import string
"""
-----------------
|options        |
|               |
|               |
|               |
-----------------
|Output         |
|               |
|               |
-----------------

text in the big portion
below is an output section, or set to monitor 
"""
class GUIThread(workerThread): #Run the gui in a separate thread
	def __init__(self, *args, **kwargs):
		super(GUIThread, self).__init__("GUI", **kwargs)
		columns = args[0]
		rows = args[1]
		self._stop = threading.Event()
		self.running = True
		self.promptColor = (255,255,255)
		self.menuColor = (255,255,255)
		self.backgroundColor = (0,0,32)
		self.numberOfColumns = columns
		self.numberOfRows = rows
		self.divideLineInputVOutput = rows #We'll start the division between inputt&prompt from output to be the initial row size with output to put under it
		self.fontSize = 20
		self.resolution = (self.fontSize * self.numberOfColumns,self.fontSize * self.numberOfRows)
		self.img = Image.new("RGB", self.resolution, color = (67,98,122))
		self.setFontSize(19)
		self.screenRefreshes = 0
		curr_dt = datetime.datetime.now()
		timeStamp = int(round(curr_dt.timestamp()))
		self.startTime = timeStamp - 1
		self.text_color = (0,0,255)
		self.updateScreen = False
		#Maintain a list of images that are to be pasted ontop of the text
		self.images = {} # {(x,y):numpy image}
		self.drawLock = False #If the buffer is being updated, block the thread from drawing the screen until its done
		self.name = "GUI Thread"
		self.bufferUpdated = False #True if theres new info in the text buffer, False if nothings changed so dont redraw the screen  even if the buffer isnt updating
		self.outputDimensions = (0,0) #The size of the output the last executed function gave
		self.bufferUpdating = False #Were not updating the buffer right now
		self.screenDrawing = False #We're not drawing the screen right nowpa
		self.waitingCycles = 0 #Count how many buffer updates are sent while the screen is drawing
		self.bufferUpdates = {} #buffer the text buffer for updates while its drawing the screen

	def setOutputPane(self, items):
		if items == []: #No input means just the menu is printing
			self.resize(self.numberOfColumns,self.divideLineInputVOutput)
			return

		self.updatingBuffer(bufferUpdating = True) #Set the drawing and buffer locks
		countOfColumns = self.numberOfColumns
		countOfRows = self.divideLineInputVOutput #The current height of the input pane

		for (index, i) in enumerate(items):
			typer = str(type(i))
			if typer == "<class 'tuple'>": #change a group to a string
				i = str(i)
				typer = "<class 'str'>"
			if typer == "<class 'str'>":
				#Count how many lines it goes down and its max line length
				lines = 1 #Must be at least this one string
				width = 0 #Length of the longest line
				current_width = 0 #Length of the line being measured
				for c in list(i):
					if c == "\n": #newline
						lines += 1
						current_width = 0
					else: #
						current_width += 1
						countOfColumns = max(countOfColumns, current_width) #Dynamically size the output pane to hold everything supplied in the list
				countOfRows += lines
				countOfColumns = max(countOfColumns, current_width)
			if typer == "<class 'numpy.ndarray'>": #Convert numpy image array from cv2 to PIL image
				i = Image.fromarray(i)
				typer =  str(type(i))
				#Now replace this element
				items[index] = i
			if typer == "<class 'PIL.Image.Image'>": #Its an image
				size = i.size
				x = math.ceil(size[0] / self.fontSize)
				y = math.ceil(size[1] / self.fontSize)
				countOfColumns = max(x, countOfColumns)
				countOfRows += y

			#Now we have the dimensions of the output window lets add it to the size

		self.resize(countOfColumns,countOfRows)
		#Now draw the output portion at the bottom, run through the list of output items, print out the text
		#tile the images across, adjust the size of the output window to show it all
		#First calculate the dimensions that the output pane needs
		rowCount = self.divideLineInputVOutput
		for i in items:
			self.addToBuffer(0,rowCount,i)

		self.outputList = items
		self.updatingBuffer(False) #Done now draw the screen

	def __str__(self):
		ret = "CLI: Width {}, Height{}\n".format(self.numberOfColumns, self.numberOfRows)
		ret += "Font Size: {}\n".format(self.fontSize)
		ret += "Screen size(pixel){}\n".format(self.resolution)
		return ret

	def resize(self, cols, rows): #Resize the array but keep the existing data
		#self.screen = np.resize(self.screen, (cols,rows), )
		new_arr = np.zeros((cols,rows), dtype = np.uint8)
		#write in the old array
		for r in range(0,rows):
			for c in range(0,cols):
				try:
					new_arr[c][r] = self.screen[c][r]
				except:
					pass #If its out of bounds
		self.screen = new_arr
		self.numberOfColumns = cols
		self.numberOfRows = rows
		self.resolution = (self.fontSize * self.numberOfColumns,self.fontSize * self.numberOfRows)
		self.img = Image.new("RGB", self.resolution, color = self.backgroundColor)


	def setSize(self, newSize): #Change the text buffer array without losing any data
		self.numberOfColumns = newSize[0]
		self.numberOfRows = newSize[1]
		self.resolution = (self.fontSize * self.numberOfColumns,self.fontSize * self.numberOfRows)
		self.img = Image.new("RGB", self.resolution, color = self.backgroundColor)

	def setFontSize(self, newSize):
		self.fontSize = newSize
		self.font = ImageFont.truetype(r'.\fonts\Courier Prime\Courier Prime.ttf', self.fontSize + 1)
		self.resetScreens()

	def resetScreens(self):
		self.resolution = (self.fontSize * self.numberOfColumns,self.fontSize * self.numberOfRows)
		self.img = Image.new("RGB", self.resolution, color = self.backgroundColor)
		self.clearText()

	def clearText(self):
		self.screen = np.zeros((self.numberOfColumns,self.numberOfRows), dtype = np.uint8)
		self.images = {}
		self.bufferUpdated = True

	def drawScreen(self):
		if self.bufferUpdated == False: #Dont draw until theres something there
			return None
		if self.updatingBuffer(): #Wait for the buffer to be done updating
			return None

		self.drawingScreen(screenDrawing = True) #Set the drawing and buffer locks
		print("Drawing screen {}".format(self.screenRefreshes))
		#Once the screen buffer is constructed, print it out one character at a time after going up the screen height lines
		row = 0
		column = 0
		#self.img = Image.new("RGB", self.resolution, color = self.backgroundColor)
		self.img.paste( self.backgroundColor, [0,0,self.img.size[0],self.img.size[1]]) #Clear out the old image
		draw = ImageDraw.Draw(self.img)
		# specified font size
		#Print out a running fps account
		curr_dt = datetime.datetime.now()
		timeStamp = int(round(curr_dt.timestamp()))
		self.screenRefreshes += 1
		fps = "fps {}".format(self.screenRefreshes / (timeStamp - self.startTime))
		self.addToBuffer(self.numberOfColumns - len(fps),0,fps)
		#Print out the waiting Cycles
		screenDraws = "Buffer updates during screen drawing: {}".format(self.waitingCycles)
		self.addToBuffer(self.numberOfColumns - len(screenDraws),1,screenDraws)

		while row < self.numberOfRows:
			while column < self.numberOfColumns:
				character = self.screen[column][row] #Get the ascii number then change it to a character
				if character == 0 or character == 32:
					column +=1 
					continue
				surfaceY = row * self.fontSize
				surfaceX = column * self.fontSize
  
				# drawing text size
				color = self.screen[column][row]
				draw.text((surfaceX, surfaceY), chr(character), font = self.font, align ="center", color = self.text_color)
				column +=1
			row +=1 #Advance to next row
			column = 0

		for (x,y), image in self.images.items(): #Paste in the images on this screen
			#Start pasting in the images 
			x = self.fontSize * x
			y = self.fontSize * y
			self.img.paste(image, (x,y))

		#return self.numpyImage
		img2 = np.array(self.img)
		self.drawingScreen(screenDrawing = False) #Open for buffer updates now
		#Now thats done, add in the buffer that may have built up
		for key,value in self.bufferUpdates.items(): #If its done drawing now add the buffered updates
			(t,a,c) = value
			self.addToBuffer(t,a,c)
		print("{} buffer updates recorded while screen drawing".format(key))
		self.bufferUpdated = False #Definitely nothing new now, wait for the next keypress
		self.bufferUpdates = {}
		return img2

	def addImage(self,x,y,image):
		#as the final row number, without a number, extending the window if necessary to avoid any distortion
		#Place it in the lower rig, ht corner
		#get the dimensions in pixels of the image
		typer = str(type(image))
		if typer == "<class 'PIL.Image.Image'>":
			self.images[(x,y)] = image
		else:
			image = Image.fromarray(image)
			self.images[(x,y)] = image
		
		size = image.size
		y = math.ceil(size[1] / self.fontSize)
		self.bufferUpdated = True
		return y
		
	def clearImages(self):
		self.images = {}
		self.bufferUpdated = True

	def addToBuffer(self, x, y, text): #Need to merge addtobuffer and addimage
		#At position x,y add the text 
		#TODO text will be a numpy array for 2d text boxes
		
		typer = str(type(text))
		while self.drawingScreen(): #Wait until its done drawing itself
			self.bufferUpdates[self.waitingCycles] = (x,y,text)
			self.waitingCycles += 1
			#Still need to return the amount of lines it would've had
			if typer == "<class 'PIL.Image.Image'>":
				size = text.size
				numLines = math.ceil(size[1] / self.fontSize)
			else:
				text = str(text) #Just force everything into strings no matter what is sent to be rendered
				numLines = len(text.split("\n"))
			return numLines
		self.updatingBuffer(True) #Lets really drive home its being updated
		self.bufferUpdated = True #Flag that the buffer has updated information
		#Check if its an image, if so send it to addimage
		if text is None:
			return 0
			
		typer = str(type(text))
		if typer == "<class 'PIL.Image.Image'>":
			return self.addImage(x,y,text)
		elif typer == "<class 'numpy.ndarray'>": #Convert numpy image array from cv2 to PIL image
			i = Image.fromarray(text)
			return self.addImage(x,y,i)
		else:
			text = str(text) #If its not an image of some sort, we need it to be text
		length = len(text)
		counter = 0
		text = list(text)
		startX = x
		linesAdded = 1 #Count the number of lines added to the buffer for drawing purposes
		while counter < length:
			character = ord(text[counter])
			if character == 10:
				y += 1
				x = startX
				linesAdded += 1
			try:
				self.screen[x][y] = character
			except Exception as e:
				pass #Just in case its out of bounds 
			counter += 1
			x += 1
		return linesAdded

	# function using _stop function
	def stop(self):
		self.running = False
		self._stop.set()
 
	def stopped(self):
		return self._stop.isSet()

	def run(self):
		while self.running:
			frame = self.drawScreen()
			if frame is None:
				pass
			else:
				cv2.imshow("CLI", frame)
			cv2.waitKey(1)
		cv2.destroyWindow("CLI")

	def getImageThumbnailSize(self):
		ret = (self.fontSize * 2, self.fontSize *2) #Maybe two line max for images is nice?
		return ret

	def updatingBuffer(self, bufferUpdating = None):
		if bufferUpdating == None: #Not setting it, just requesting if the updating the buffer 
			return self.bufferUpdating
		if bufferUpdating == True or bufferUpdating == False: #Set the buffer to updating
			self.bufferUpdating = bufferUpdating
			print("Buffer is currently being updated:{}\nBuffer has an update: {}".format(self.bufferUpdating, self.bufferUpdated))
			return self.bufferUpdating
		return self.bufferUpdating

	def drawingScreen(self, screenDrawing = None):
		if screenDrawing == None: #Not setting it, just requesting if the updating the buffer 
			return self.screenDrawing
		if screenDrawing == True or screenDrawing == False: #Set the buffer to updating
			self.screenDrawing = screenDrawing
			print("Screen drawing change {}".format(self.screenDrawing))
			return self.screenDrawing
		return self.screenDrawing #Bad input just output the existing value
