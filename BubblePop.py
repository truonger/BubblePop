import sys, pygame, time
from pygame.locals import *

"""
	BUBBLE POP!
	by Mike Truong (mike.truong@gmail.com)
	
	This is a k-pop clone of DDR. This is my mini-hackathon 
	project to learn python better for a job interview.
	
	LOG:
		10/31/13 - 11:30 pm -  3:30 am (4 hrs)
		11/01/13 - 12:00 pm -  8:00 pm (8 hrs)
		11/02/13 -  8:00 am - 10:30 am (2.5 hrs)
		11/02/13 -  1:00 pm -  4:30 pm (3.5 hrs)
		11/02/13 -  6:30 pm -     ? pm
"""

#----------------------------------------------------------
# BPSprite class
#----------------------------------------------------------
class BPSprite(object):
	"""
		Basic sprite class. Sprites handle their own
		animations. Animations are handled as simple
		actions in a queue and can be blended together.
		All tweens are linear interpolations (no easing).
	"""
	context = None
	data = None
	pos = None
	imgObj = []
	curImg = None
	actions = []
	terminated = False
	alpha = 255
	imgBackup = None
	
	# COMMON
	ACTION_IDENTIFIER = "action"			# action identifier
	ACTION_START_TIME = "start_time"		# start_time of action (defaults to now)
	ACTION_DURATION = "duration"			# in seconds (defaults to now)
	ACTION_BLEND = "blend"					# blend with current actions (defaults to False)
	
	# POSITION
	ACTION_POSITION = "position"			# position action
	ACTION_POSITION_TARGET = "pos_target"	# target position
	ACTION_POSITION_ORIGIN = "pos_origin"	# origin position (defaults to current)
	
	# TERMINATE
	ACTION_TERMINATE = "terminate"			# terminate action
	ACTION_TERMINATE_DELEGATE = "delegate"	# terminate delegate (passes self as param)
	
	# ALPHA
	ACTION_ALPHA = "alpha"					# alpha animation
	ACTION_ALPHA_TARGET = "alpha_target"	# target alpha
	ACTION_ALPHA_ORIGIN = "alpha_origin"	# origin alpha (defaults to current)
	
	# CALLBACK
	ACTION_CALLBACK = "callback"			# callback action
	ACTION_CALLBACK_FUNCTION = "cb_func"	# callback function
	
	def __init__(self, context, data, pos, imgObj, curImg = 0):
		"""
			init() method
			
			Pass in the initial position of the object
			as a tuple, its images as a list, and the
			current img frame.
		"""
		self.context = context
		self.data = data
		self.pos = pos
		self.imgObj = imgObj
		self.curImg = curImg
		self.actions = []
		self.terminated = False
		self.alpha = 255
		self.imgBackup = None
		
	def draw(self):
		if self.terminated == True: return
		
		# Resolve alpha for the image on a copy of the original image
		img = self.imgObj[self.curImg].copy()
		img.fill((0, 0, 0, 255 - self.alpha), None, BLEND_RGBA_SUB)
		
		self.context['surfDisp'].blit(img, self.pos)
		
	def queueAction(self, action):
		"""
			Pushes an action into the queue in sorted order.
			Pass in a dictionary for the action parameter.
		"""
		if self.terminated == True: return
		
		# Default values for actions
		if self.ACTION_START_TIME not in action.keys():
			action[self.ACTION_START_TIME] = time.time()
		if self.ACTION_BLEND not in action.keys():
			action[self.ACTION_BLEND] = False
		if self.ACTION_POSITION_ORIGIN not in action.keys():
			action[self.ACTION_POSITION_ORIGIN] = self.pos
		if self.ACTION_DURATION not in action.keys():
			action[self.ACTION_DURATION] = 0
		if self.ACTION_ALPHA_ORIGIN not in action.keys():
			action[self.ACTION_ALPHA_ORIGIN] = self.alpha

		# Insert the action in sorted order according to start time
		inserted = False
		for i in range(len(self.actions)):
			if action[self.ACTION_START_TIME] < self.actions[i][self.ACTION_START_TIME]:
				self.actions.insert(i, action)
				inserted = True
				break
		if inserted == False: 
			self.actions.append(action)
		
	def handleAction(self, action):
		"""
			All possible actions for this class are dealt with 
			here
		"""
		if self.terminated == True: return
		
		elapsed = time.time() - action[self.ACTION_START_TIME]
		percElapsed = 0
		if action[self.ACTION_DURATION] == 0:
			percElapsed = 100
		else:
			percElapsed = elapsed / action[self.ACTION_DURATION]
		
		if action[self.ACTION_IDENTIFIER] == self.ACTION_POSITION:
			dx = action[self.ACTION_POSITION_TARGET][0] - action[self.ACTION_POSITION_ORIGIN][0]
			dy = action[self.ACTION_POSITION_TARGET][1] - action[self.ACTION_POSITION_ORIGIN][1]
			tx = action[self.ACTION_POSITION_ORIGIN][0] + (percElapsed * dx)
			ty = action[self.ACTION_POSITION_ORIGIN][1] + (percElapsed * dy)
			self.pos = (tx, ty)
		elif action[self.ACTION_IDENTIFIER] == self.ACTION_ALPHA:
			self.imgObj[self.curImg] = self.imgObj[self.curImg].copy()
			delta = (action[self.ACTION_ALPHA_TARGET] - action[self.ACTION_ALPHA_ORIGIN]) * percElapsed
			self.alpha = max(min(action[self.ACTION_ALPHA_ORIGIN] + delta, 255), 0)
		elif action[self.ACTION_IDENTIFIER] == self.ACTION_CALLBACK:
			if self.ACTION_CALLBACK_FUNCTION in action.keys():
				action[self.ACTION_CALLBACK_FUNCTION](self)
		elif action[self.ACTION_IDENTIFIER] == self.ACTION_TERMINATE:
			self.terminated = True
			if self.ACTION_TERMINATE_DELEGATE in action.keys():
				action[self.ACTION_TERMINATE_DELEGATE](self)
				
		if percElapsed >= 1:
			self.actions.remove(action)
		
	def update(self):
		"""
			Update the sprite based on all the actions in 
			the queue. 
		"""
		if self.terminated == True: return
		
		for action in list(self.actions):
			if time.time() >= action[self.ACTION_START_TIME] and (action == self.actions[0] or 
				action[self.ACTION_BLEND] == True or action[self.ACTION_IDENTIFIER] == self.ACTION_TERMINATE):
				self.handleAction(action)
		
	
#----------------------------------------------------------
# BPController class
#----------------------------------------------------------
class BPController(object):
	"""
		The template object for game state controllers
		
		Controllers are organized in a linked list stack.
		Each controller has a pointer to its parent and
		child controllers. Events/messages are passed up
		the stack. Parent controllers are notified of
		child controller actions via direct method calls.
		
		Inherit from this class and override the handlers.
		
		TODO (mike.truong@gmail.com):
		Implement a message queue instead of making
		direct method calls through parent/child
		pointers. The callstack might get really 
		big if we ever get into complex state flows.
		
		TODO (mike.truong@gmail.com):
		Pass in pointers to whatever you need from the
		sys and pygame libraries so we can break out
		the controllers into their own module
	"""
	context = None		# Game Context
	prevState = None	# Previous State
	state = None		# Current State
	parent = None		# Parent Controller
	child = None		# Child Controller
	
	def __init__(self, parent, context):
		self.parent = parent
		self.context = context
		self.prevState = None
		self.state = None
		self.child = None

	#--- Be careful about overriding methods in this section
	
	def launchChild(self, child):
		self.child = child
		child.start()
		
	def exit(self):
		if self.parent != None:
			self.parent.onChildExit()
			
	def changeState(self, state):
		self.prevState = self.state
		self.state = state
		
	def onUpdate(self):
		if self.child == None:
			self.handleUpdate()
		else:
			self.child.onUpdate()
		
	def onEvent(self, event):
		if self.child == None:
			self.handleEvent(event)
		else:
			self.child.onEvent(event)
		
	def onChildExit(self):
		self.child = None
		self.handleChildExit()	
		
	#--- Begin Handlers (override these as you please)
	
	def start(self):
		pass
		
	def handleChildExit(self):
		pass
		
	def handleEvent(self, event):
		pass
		
	def handleUpdate(self):
		pass

#----------------------------------------------------------
# BPLaunchController class
#----------------------------------------------------------
class BPLaunchController(BPController):
	"""
		Renders the start screen and waits for a keypress.
	"""
	def __init__(self, parent, context):
		BPController.__init__(self, parent, context)
		
	def start(self):
		startImg = pygame.image.load('bg_start.jpg').convert()			
		self.context['surfDisp'].blit(startImg, (0, 0))
		
	def handleEvent(self, event):
		if event.type == KEYDOWN:
			self.exit()
			
#----------------------------------------------------------
# BPGameplayController class
#----------------------------------------------------------
class BPGameplayController(BPController):
	"""
		The main gameplay state controller. 
	"""
	levelData = []
	imgArrows = []
	imgHUDArrows = []
	imgTextFlashers = []
	imgScoreNums = []
	imgBG = None
	imgHitFlasher = None
	imgMissFlasher = None
	sprites = []
	flashers = []
	scoreDigits = []
	keystrokes = []
	arrowData = []
	arrowType = 0
	score = 0
	
	KEYS = [K_j, K_k, K_i, K_l]		# Using ijkl as the keypad (bigger keys, easier to press)
	KEY_QUIT_RECORDING = K_SPACE	# Stops a recording session

	NUM_ARROW_DIRECTIONS = 4		# Left, Down, Up, Right
	NUM_ARROW_TYPES = 4				# Green, Orange, Pink, Blue
	NUM_ARROW_STATES = 4			# No fill, 1-bar fill, 2-bar fill, 3-bar fill
	
	IMG_ARROW_SIZE = (60, 60)		# Dimensions of the arrow images
	HUD_ARROW_START_POS = (352, 50)	# Start position for the HUD arrows
	ARROW_COLUMN_PAD = 5
	ARROW_TIMING_FILE = 'bubble_pop_arrow_timings.txt'	# File for arrow timings
	ARROW_TIMING_KEY_DOWN = 'down'	# Dictionary key
	ARROW_TIMING_KEY_UP = 'up'		# Dictionary key
	ARROW_TIMING_KEY_KEY = 'key'	# Dictionary key
	ARROW_TIME_BOTTOM_TO_TOP = 3	# Time for arrow to go from bottom of screen to top 
	ARROW_FADE_TIME = 0.2			# Time to fade arrow to 0 alpha after past hit zone
	
	HIT_THRESHOLDS = (0.05, 0.1, 0.15)		# Hit thresholds for scoring
	HIT_FLASHER_FADE_TIME = 0.25			# Hit flasher fade time
	NUM_HIT_TEXT_FLASHERS = 4				# Num hit text flasher images
	HIT_TEXT_FLASHER_SIZE = (81, 15)		# Size of hit flasher text images
	
	MISS_FLASHER_SIZE = (269, 49)
	MISS_FLASHER_Y = 290					# y-coord for miss flasher
	MISS_FLASHER_FADE_TIME = 0.5			# miss flasher fade time
	MISS_FLASHER_INDICATOR = 'miss'			# how we remember which flashers are miss flashers
	
	NUM_SCORE_DIGITS = 6					# number of digits in our score
	SCORE_VALUES = [10, 5, 1]				# score values for each hit threshold
	SCORE_DIGIT_OFFSET = (10, 10)			# offset from the top right for first score digit
	SCORE_DIGIT_SIZE = (54, 54)				# size of each score digit image	
	SCORE_DIGIT_PAD = 5		 
	
	#--- RECORDING MODE ---#
	RECORDING_MODE = False
	
	def __init__(self, parent, context):
		BPController.__init__(self, parent, context)
		self.levelData = []
		self.imgArrows = []
		self.imgHUDArrows = []
		self.imgTextFlashers = []
		self.imgScoreNums = []
		self.imgMissFlasher = None
		self.imgBG = None
		self.imgHitFlasher = None
		self.sprites = []
		self.flashers = []
		self.keystrokes = []
		self.arrowData = []
		self.arrowType = 0
		self.score = 0
		
	def getColPosX(self, col):
		return self.HUD_ARROW_START_POS[0] + (col * self.IMG_ARROW_SIZE[0]) + (col * self.ARROW_COLUMN_PAD)
		
	def drawBG(self):
		self.context['surfDisp'].blit(self.imgBG, (0, 0))
		for i in range(self.NUM_ARROW_DIRECTIONS):
			self.context['surfDisp'].blit(
				self.imgHUDArrows[i], 
				(self.getColPosX(i), self.HUD_ARROW_START_POS[1]))
			
	def removeSprite(self, sprite):
		self.sprites.remove(sprite)
		
	def removeFlasher(self, sprite):
		self.flashers.remove(sprite)
		
	def drawHUD(self):
		for digit in self.scoreDigits:
			digit.draw()

	def start(self):
		# Load the level data
		timingKeys = [self.ARROW_TIMING_KEY_DOWN, self.ARROW_TIMING_KEY_UP, self.ARROW_TIMING_KEY_KEY]
		with open(self.ARROW_TIMING_FILE, 'r') as f:
			for line in f:
				timingValues = line.split('\t')
				timingValues = [float(i) for i in timingValues]
				arrow = dict(zip(timingKeys, timingValues))
				arrow[self.ARROW_TIMING_KEY_KEY] = int(arrow[self.ARROW_TIMING_KEY_KEY])
				self.arrowData.append(arrow)
						
		# Load the images
		self.imgBG = pygame.image.load('bg_gameplay.jpg').convert()	
		self.imgHitFlasher = pygame.image.load('hit.png').convert_alpha()
		self.imgMissFlasher = pygame.image.load('text_flasher_miss.png').convert_alpha()
		for i in range(self.NUM_ARROW_DIRECTIONS):	# HUD arrows
			self.imgHUDArrows.append(pygame.image.load('arrow_hud_{0}.png'.format(i)).convert_alpha())		
		for i in range(self.NUM_HIT_TEXT_FLASHERS): # Hit text flashers
			self.imgTextFlashers.append(pygame.image.load('text_flasher_{0}.png'.format(i)).convert_alpha())
		for i in range(10): 		# Score digits
			self.imgScoreNums.append(pygame.image.load('num_{0}.png'.format(i)).convert_alpha())
		for i in range(self.NUM_ARROW_TYPES):		# Gameplay arrows
			self.imgArrows.append([])
			for j in range(self.NUM_ARROW_DIRECTIONS):
				self.imgArrows[i].append([])
				for k in range(self.NUM_ARROW_STATES):
					self.imgArrows[i][j].append(
						pygame.image.load('arrow_{0}_{1}_{2}.png'.format(i, j, k)).convert_alpha())
		
		# Start the music
		if self.context['musicEnabled'] == True:
			self.context['musicObj'].play()
			
		# Create the score digit sprites
		self.spawnScoreDigits()

		self.keystrokes = []
		self.context['timeLevelStart'] = time.time()
		
	def arrowMissDelegate(self, sprite):
		self.sprites.remove(sprite)
		self.spawnMissFlasher()
		
	def spawnScoreDigits(self):
		cx = self.context['windowSize'][0] - self.SCORE_DIGIT_OFFSET[0]
		for i in range(self.NUM_SCORE_DIGITS):
			cx = cx - self.SCORE_DIGIT_SIZE[0]
			sprite = BPSprite(
				self.context, 
				None,
				(cx, self.SCORE_DIGIT_OFFSET[1]),
				self.imgScoreNums)
			self.scoreDigits.append(sprite)
			cx = cx - self.SCORE_DIGIT_PAD
		
	def spawnArrows(self):
		imgHeight = self.IMG_ARROW_SIZE[1]
		windowHeight = self.context['windowSize'][1]
		pixelsPerSecond =  (windowHeight + imgHeight) / self.ARROW_TIME_BOTTOM_TO_TOP
		secondsPerPixel = 1 / pixelsPerSecond
		pixelsToHitZone = windowHeight - self.HUD_ARROW_START_POS[1]
		timeToHitZone = pixelsToHitZone * secondsPerPixel
		curTime = time.time() - self.context['timeLevelStart']
		unspawned = []
		
		for arrow in self.arrowData:	# check for arrows to spawn
			keyTime = arrow[self.ARROW_TIMING_KEY_DOWN]
			spawnTime = keyTime - timeToHitZone
			if curTime >= spawnTime:	# if it's time to spawn this arrow
				curKey = arrow[self.ARROW_TIMING_KEY_KEY]
				colPosX = self.getColPosX(curKey)
				timeAdjustment = curTime - spawnTime
				duration = self.ARROW_TIME_BOTTOM_TO_TOP - timeAdjustment
				startY = windowHeight - (pixelsPerSecond * timeAdjustment)
				arrowSprite = BPSprite(
					self.context, 
					arrow,
					(colPosX, startY),
					self.imgArrows[self.arrowType][curKey], 0)
				arrowSprite.queueAction(	# Animate past top of screen
					{	
						BPSprite.ACTION_IDENTIFIER:BPSprite.ACTION_POSITION,
						BPSprite.ACTION_POSITION_TARGET:(colPosX, -1 * imgHeight),
						BPSprite.ACTION_DURATION:duration
					})
				arrowSprite.queueAction(	# Fade past hit zone
					{	
						BPSprite.ACTION_IDENTIFIER:BPSprite.ACTION_ALPHA,
						BPSprite.ACTION_ALPHA_TARGET:0,
						BPSprite.ACTION_START_TIME:time.time() + timeToHitZone,
						BPSprite.ACTION_DURATION:self.ARROW_FADE_TIME,
						BPSprite.ACTION_BLEND:True
					})
				arrowSprite.queueAction(	# Callback to controller on miss
					{	
						BPSprite.ACTION_IDENTIFIER:BPSprite.ACTION_CALLBACK,
						BPSprite.ACTION_CALLBACK_FUNCTION:self.arrowMissDelegate,
						BPSprite.ACTION_START_TIME:time.time() + timeToHitZone + self.HIT_THRESHOLDS[2],
						BPSprite.ACTION_BLEND:True
					})
				arrowSprite.queueAction(	# Terminate
					{
						BPSprite.ACTION_IDENTIFIER:BPSprite.ACTION_TERMINATE,
						BPSprite.ACTION_TERMINATE_DELEGATE:self.removeSprite,
						BPSprite.ACTION_START_TIME:time.time() + duration
					})
				self.sprites.append(arrowSprite)
			else:
				unspawned.append(arrow)
		self.arrowData = unspawned
		
	def spawnHitFlasher(self, col, txtIdx):
		# kill any miss flashers
		self.flashers = [f for f in self.flashers if f.data != self.MISS_FLASHER_INDICATOR]
			
		# spark sprite
		sprite = BPSprite(
			self.context, 
			None,
			(self.getColPosX(col), self.HUD_ARROW_START_POS[1]),
			[self.imgHitFlasher])
		sprite.queueAction(	# Fade 
			{	
				BPSprite.ACTION_IDENTIFIER:BPSprite.ACTION_ALPHA,
				BPSprite.ACTION_ALPHA_TARGET:0,
				BPSprite.ACTION_START_TIME:time.time(),
				BPSprite.ACTION_DURATION:self.HIT_FLASHER_FADE_TIME
			})
		sprite.queueAction(	# Terminate
			{
				BPSprite.ACTION_IDENTIFIER:BPSprite.ACTION_TERMINATE,
				BPSprite.ACTION_TERMINATE_DELEGATE:self.removeFlasher,
				BPSprite.ACTION_START_TIME:time.time() + self.HIT_FLASHER_FADE_TIME
			})
		self.flashers.append(sprite)
		
		# text sprite
		xOffset = (self.IMG_ARROW_SIZE[0] - self.HIT_TEXT_FLASHER_SIZE[0]) / 2
		yOffset = (self.IMG_ARROW_SIZE[1] - self.HIT_TEXT_FLASHER_SIZE[1]) / 2
		txtSprite = BPSprite(
			self.context, 
			None,
			(self.getColPosX(col) + xOffset, self.HUD_ARROW_START_POS[1] + yOffset),
			[self.imgTextFlashers[txtIdx]])
		txtSprite.queueAction(	# Fade 
			{	
				BPSprite.ACTION_IDENTIFIER:BPSprite.ACTION_ALPHA,
				BPSprite.ACTION_ALPHA_TARGET:0,
				BPSprite.ACTION_START_TIME:time.time(),
				BPSprite.ACTION_DURATION:self.HIT_FLASHER_FADE_TIME
			})
		txtSprite.queueAction(	# Terminate
			{
				BPSprite.ACTION_IDENTIFIER:BPSprite.ACTION_TERMINATE,
				BPSprite.ACTION_TERMINATE_DELEGATE:self.removeFlasher,
				BPSprite.ACTION_START_TIME:time.time() + self.HIT_FLASHER_FADE_TIME
			})
		self.flashers.append(txtSprite)
		
	def spawnMissFlasher(self):
		sprite = BPSprite(
			self.context, 
			self.MISS_FLASHER_INDICATOR,
			((self.context['windowSize'][0] / 2) - (self.MISS_FLASHER_SIZE[0] / 2), self.MISS_FLASHER_Y),
			[self.imgMissFlasher])
		sprite.queueAction(	# Fade 
			{	
				BPSprite.ACTION_IDENTIFIER:BPSprite.ACTION_ALPHA,
				BPSprite.ACTION_ALPHA_TARGET:0,
				BPSprite.ACTION_START_TIME:time.time(),
				BPSprite.ACTION_DURATION:self.MISS_FLASHER_FADE_TIME
			})
		sprite.queueAction(	# Terminate
			{
				BPSprite.ACTION_IDENTIFIER:BPSprite.ACTION_TERMINATE,
				BPSprite.ACTION_TERMINATE_DELEGATE:self.removeFlasher,
				BPSprite.ACTION_START_TIME:time.time() + self.MISS_FLASHER_FADE_TIME
			})
		self.flashers.append(sprite)
		
	def updateScoreDigitSprites(self):
		for i in range(len(self.scoreDigits)):
			self.scoreDigits[i].curImg = int(str(self.score).zfill(self.NUM_SCORE_DIGITS)[-1 * (i + 1)])
		
	def handleUpdate(self):
		# Spawn
		self.spawnArrows()
		self.updateScoreDigitSprites()
		
		# Update
		for sprite in list(self.sprites):
			sprite.update()
		for flasher in list(self.flashers):
			flasher.update()
		for digit in self.scoreDigits:
			digit.update()
		
		# Draw
		self.drawBG()
		if self.RECORDING_MODE == False:
			for sprite in self.sprites: sprite.draw()
			for flasher in self.flashers: flasher.draw()
		self.drawHUD()
		
	def getKeyIndex(self, event):
		if (event.type == KEYDOWN or event.type == KEYUP) and event.key in self.KEYS:
			return self.KEYS.index(event.key)
		return -1
		
	def recordKeys(self, event):
		if self.RECORDING_MODE == False: return
		
		if event.key == self.KEY_QUIT_RECORDING:
			with open(self.ARROW_TIMING_FILE, 'w') as f:
				for keystroke in self.keystrokes:
					f.write('{0}\t{1}\t{2}\n'.format(
						keystroke[self.ARROW_TIMING_KEY_DOWN], keystroke[self.ARROW_TIMING_KEY_UP], keystroke[self.ARROW_TIMING_KEY_KEY]))
			return
						
		keyIndex = self.getKeyIndex(event)
		if keyIndex >= 0:
			eventTime = time.time() - self.context['timeLevelStart']
			if event.type == KEYDOWN:
				self.keystrokes.append(
					{	
						self.ARROW_TIMING_KEY_DOWN:eventTime,
						self.ARROW_TIMING_KEY_KEY:keyIndex
					})
			elif event.type == KEYUP:
				for keystroke in self.keystrokes:
					if keystroke[self.ARROW_TIMING_KEY_KEY] == keyIndex and self.ARROW_TIMING_KEY_UP not in keystroke.keys():
						keystroke[self.ARROW_TIMING_KEY_UP] = eventTime
			
	def handleEvent(self, event):
		self.recordKeys(event)
		curLevelTime = time.time() - self.context['timeLevelStart']
		keyIndex = self.getKeyIndex(event)
		if event.type == KEYDOWN and keyIndex >= 0 and len(self.sprites) > 0:
			arrowData = self.sprites[0].data
			hit = False
			if arrowData[self.ARROW_TIMING_KEY_KEY] == keyIndex:
				for i in range(len(self.HIT_THRESHOLDS)):
					delta = arrowData[self.ARROW_TIMING_KEY_DOWN] - curLevelTime
					if abs(delta) <= self.HIT_THRESHOLDS[i]:
						hit = True
						self.score = min(self.score + self.SCORE_VALUES[i], (10 ** self.NUM_SCORE_DIGITS) - 1)
						txtIdx = i
						if i >= 2 and delta < 0: txtIdx = txtIdx + 1
						self.sprites.pop(0)
						self.spawnHitFlasher(keyIndex, txtIdx)
						break
			if hit == False:
				self.spawnMissFlasher()
				pass
				
		
#----------------------------------------------------------
# BPGame class
#----------------------------------------------------------
class BPGame(BPController):
	"""
		The main game object. Also serves as the root controller.
		The main game loop is in the run() method, and all game data
		is stored in the context attribute.
	"""
	rootController = None	
	
	# CONTROLLER STATES
	BPSTATE_START		= "start"
	BPSTATE_GAMEPLAY 	= "gameplay"
	
	def __init__(self, context):
		BPController.__init__(self, None, context)
		self.rootController = self
		
	def handleChildExit(self):
		if self.state == self.BPSTATE_START:
			self.changeState(self.BPSTATE_GAMEPLAY)
			self.launchChild(BPGameplayController(self, self.context))
		
	def run(self):
		self.changeState(self.BPSTATE_START)
		self.launchChild(BPLaunchController(self, self.context))
		
		# MAIN GAME LOOP
		while True: 
			# Pass the input events up the controller stack
			for event in pygame.event.get():
				if event.type == QUIT:
					pygame.quit()
					sys.exit()
				else:
					self.rootController.onEvent(event)

			self.rootController.onUpdate()
			pygame.display.update()
			
			self.context['clockFPS'].tick(self.context['FPS'])

#----------------------------------------------------------
# main() function
#----------------------------------------------------------
def main():
	pygame.init()
	
	bpContext = {}
	bpContext['pygame'] = pygame
	bpContext['FPS'] = 60 
	bpContext['windowSize'] = (960, 540)
	bpContext['musicFile'] = 'bubble_pop.wav'
	bpContext['title'] = 'Bubble Pop!'
	bpContext['musicEnabled'] = True
	
	bpContext['clockFPS'] = pygame.time.Clock()
	bpContext['surfDisp'] = pygame.display.set_mode((bpContext['windowSize'][0], bpContext['windowSize'][1]))
	bpContext['fontTitle'] = pygame.font.Font('freesansbold.ttf', 18)
	bpContext['musicObj'] = pygame.mixer.Sound(bpContext['musicFile'])

	pygame.display.set_caption(bpContext['title'])
	bpGame = BPGame(bpContext)
	bpGame.run()

#----------------------------------------------------------
# Call main()
#----------------------------------------------------------
if __name__ == '__main__':
	main()

