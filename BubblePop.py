import sys, pygame, time
from pygame.locals import *

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
	pos = None
	imgObj = []
	curImg = None
	actions = []
	terminated = False
	
	# COMMON
	ACTION_IDENTIFIER = "action"			# action identifier
	ACTION_START_TIME = "start_time"		# start_time of action
	ACTION_DURATION = "duration"			# in seconds
	ACTION_BLEND = "blend"					# blend with current actions
	
	# POSITION
	ACTION_POSITION = "position"			# position action
	ACTION_POSITION_TARGET = "pos_target"	# target position
	ACTION_POSITION_ORIGIN = "pos_origin"	# origin position
	
	# TERMINATE
	ACTION_TERMINATE = "terminate"			# terminate action
	ACTION_TERMINATE_DELEGATE = "delegate"	# terminate delegate (passes self as param)
	
	def __init__(self, context, pos, imgObj, curImg):
		"""
			init() method
			
			Pass in the initial position of the object
			as a tuple, its images as a list, and the
			current img frame.
		"""
		self.context = context
		self.pos = pos
		self.imgObj = imgObj
		self.curImg = curImg
		self.actions = []
		self.terminated = False
		
	def draw(self):
		if self.terminated == True: return
		self.context['surfDisp'].blit(self.imgObj[self.curImg], self.pos)
		
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
		
		if action[self.ACTION_IDENTIFIER] == self.ACTION_POSITION:
			elapsed = time.time() - action[self.ACTION_START_TIME]
			percElapsed = elapsed / action[self.ACTION_DURATION]
			dx = action[self.ACTION_POSITION_TARGET][0] - action[self.ACTION_POSITION_ORIGIN][0]
			dy = action[self.ACTION_POSITION_TARGET][1] - action[self.ACTION_POSITION_ORIGIN][1]
			tx = action[self.ACTION_POSITION_ORIGIN][0] + (percElapsed * dx)
			ty = action[self.ACTION_POSITION_ORIGIN][1] + (percElapsed * dy)
			self.pos = (tx, ty)
			if percElapsed >= 1:
				self.actions.remove(action)
		elif action[self.ACTION_IDENTIFIER] == self.ACTION_TERMINATE:
			print("Terminating!")
			self.terminated = True
			if self.ACTION_TERMINATE_DELEGATE in action.keys():
				action[self.ACTION_TERMINATE_DELEGATE](self)
			
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
		startImg = pygame.image.load('start.jpg').convert()			
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
	imgBG = None
	imgHUDArrows = []
	sprites = []
	keystrokes = []
	arrows = []
	spawned = []
	arrowType = 0
	
	KEYS = [K_j, K_k, K_i, K_l]		# Using ijkl as the keypad (bigger keys, easier to press)
	KEY_QUIT_RECORDING = K_SPACE	# Stops a recording session

	NUM_ARROW_DIRECTIONS = 4		# Left, Down, Up, Right
	NUM_ARROW_TYPES = 4				# Green, Orange, Pink, Blue
	NUM_ARROW_STATES = 4			# No fill, 1-bar fill, 2-bar fill, 3-bar fill
	
	IMG_ARROW_SIZE = { 'width':60, 'height':60 }	# Dimensions of the arrow images
	HUD_ARROW_START_POS = { 'x':352, 'y':50 }		# Start position for the HUD arrows
	ARROW_COLUMN_PAD = 5
	ARROW_TIMING_FILE = 'bubble_pop_arrow_timings.txt'	# File for arrow timings
	ARROW_TIMING_KEY_DOWN = 'down'	# Dictionary key
	ARROW_TIMING_KEY_UP = 'up'		# Dictionary key
	ARROW_TIMING_KEY_KEY = 'key'	# Dictionary key
	ARROW_TIME_BOTTOM_TO_TOP = 3	# Time for arrow to go from bottom of screen to top 
	
	#--- RECORDING MODE ---#
	RECORDING_MODE = False
	
	def __init__(self, parent, context):
		BPController.__init__(self, parent, context)
		
	def getColPosX(self, col):
		return self.HUD_ARROW_START_POS['x'] + (col * self.IMG_ARROW_SIZE['width']) + (col * self.ARROW_COLUMN_PAD)
		
	def drawBG(self):
		self.context['surfDisp'].blit(self.imgBG, (0, 0))
		for i in range(self.NUM_ARROW_DIRECTIONS):
			self.context['surfDisp'].blit(
				self.imgHUDArrows[i], 
				(self.getColPosX(i), self.HUD_ARROW_START_POS['y']))
		
	def drawSprites(self):
		for sprite in self.sprites:
			sprite.draw()
			
	def removeSprite(self, sprite):
		self.sprites.remove(sprite)
		
	def drawHUD(self):			
		pass

	def start(self):
		# Load the level data
		timingKeys = [self.ARROW_TIMING_KEY_DOWN, self.ARROW_TIMING_KEY_UP, self.ARROW_TIMING_KEY_KEY]
		with open(self.ARROW_TIMING_FILE, 'r') as f:
			for line in f:
				timingValues = line.split('\t')
				timingValues = [float(i) for i in timingValues]
				arrow = dict(zip(timingKeys, timingValues))
				arrow[self.ARROW_TIMING_KEY_KEY] = int(arrow[self.ARROW_TIMING_KEY_KEY])
				self.arrows.append(arrow)
				
				
		# Load the images
		self.imgBG = pygame.image.load('bg_gameplay.jpg').convert()
		
		for i in range(self.NUM_ARROW_DIRECTIONS):	# HUD arrows
			self.imgHUDArrows.append(pygame.image.load('arrow_hud_{0}.png'.format(i)).convert_alpha())
			
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

		self.keystrokes = []
		self.context['timeLevelStart'] = time.time()
			
	def handleUpdate(self):
		# Spawn arrows
		imgHeight = self.IMG_ARROW_SIZE['height']
		windowHeight = self.context['windowSize']['height']
		pixelsPerSecond =  (windowHeight + imgHeight) / self.ARROW_TIME_BOTTOM_TO_TOP
		secondsPerPixel = 1 / pixelsPerSecond
		pixelsToHitZone = windowHeight - self.HUD_ARROW_START_POS['y']
		timeToHitZone = pixelsToHitZone * secondsPerPixel
		curTime = time.time() - self.context['timeLevelStart']
		unspawned = []
		
		for arrow in self.arrows:	# check for arrows to spawn
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
					(colPosX, startY),
					self.imgArrows[self.arrowType][curKey], 0)
				arrowSprite.queueAction(	# Animate past top of screen
					{	
						BPSprite.ACTION_IDENTIFIER:BPSprite.ACTION_POSITION,
						BPSprite.ACTION_POSITION_TARGET:(colPosX, -1 * imgHeight),
						BPSprite.ACTION_DURATION:duration
					})
				arrowSprite.queueAction(	# Terminate
					{
						BPSprite.ACTION_IDENTIFIER:BPSprite.ACTION_TERMINATE,
						BPSprite.ACTION_TERMINATE_DELEGATE:self.removeSprite,
						BPSprite.ACTION_START_TIME:time.time() + duration
					})
				self.sprites.append(arrowSprite)
				self.spawned.append(arrow)
			else:
				unspawned.append(arrow)
		self.arrows = unspawned
		
		# Clear the display surface and update the sprites
		self.context['surfDisp'].fill((0, 0, 0))
		for sprite in list(self.sprites):
			sprite.update()
		
		# Draw all the elements
		self.drawBG()
		if self.RECORDING_MODE == False:
			self.drawSprites()
		self.drawHUD()
		
	def recordKeys(self, event):
		if self.RECORDING_MODE == False: return
		if event.type not in (KEYDOWN, KEYUP): return
		
		if event.key in self.KEYS:
			keyIndex = self.KEYS.index(event.key)
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
		elif event.key == self.KEY_QUIT_RECORDING:
			with open(self.ARROW_TIMING_FILE, 'w') as f:
				for keystroke in self.keystrokes:
					f.write('{0}\t{1}\t{2}\n'.format(
						keystroke[self.ARROW_TIMING_KEY_DOWN], keystroke[self.ARROW_TIMING_KEY_UP], keystroke[self.ARROW_TIMING_KEY_KEY]))
			
	def handleEvent(self, event):
		self.recordKeys(event)
		
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
	bpContext['windowSize'] = { 'width':960, 'height':540 }
	bpContext['musicFile'] = 'bubble_pop.wav'
	bpContext['title'] = 'Bubble Pop!'
	bpContext['musicEnabled'] = True
	
	bpContext['clockFPS'] = pygame.time.Clock()
	bpContext['surfDisp'] = pygame.display.set_mode((bpContext['windowSize']['width'], bpContext['windowSize']['height']))
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

