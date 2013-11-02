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

	ACTION_IDENTIFIER = "action"			# action identifier
	ACTION_POSITION = "position"			# position action
	ACTION_POSITION_TARGET = "pos_target"	# target position
	ACTION_POSITION_ORIGIN = "pos_origin"	# origin position
	ACTION_START_TIME = "start_time"		# start_time of action
	ACTION_DURATION = "duration"			# in seconds
	ACTION_BLEND = "blend"					# blend with current actions
	
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
		
	def draw(self):
		self.context['surfDisp'].blit(self.imgObj[self.curImg], self.pos)
		
	def queueAction(self, action):
		"""
			Pushes an action into the queue in sorted order.
			Pass in a dictionary for the action parameter.
		"""
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
		if len(self.actions) == 0:
			self.actions.append(action)
		else:
			for i in len(self.actions):
				if action[self.ACTION_START_TIME] < self.actions[i][self.ACTION_START_TIME]:
					self.actions.insert(i, action)
		
	def handleAction(self, action):
		"""
			All possible actions for this class are dealt with 
			here
		"""
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
				self.handleActionDone(action)
				
	def handleActionDone(self, action):
		pass
			
	def update(self):
		"""
			Update the sprite based on all the actions in 
			the queue. 
		"""
		for i in range(len(self.actions)):
			if (i == 0 or self.actions[i][self.ACTION_BLEND] == TRUE) and self.actions[i][self.ACTION_START_TIME] <= time.time():
				self.handleAction(self.actions[i])
		
	
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
	
	KEYS = [K_j, K_k, K_i, K_l]		# Using ijkl as the keypad (bigger keys, easier to press)
	KEY_QUIT_RECORDING = K_SPACE	# Stops a recording session

	NUM_ARROW_DIRECTIONS = 4		# Left, Down, Up, Right
	NUM_ARROW_TYPES = 4				# Green, Orange, Pink, Blue
	NUM_ARROW_STATES = 4			# No fill, 1-bar fill, 2-bar fill, 3-bar fill
	
	IMG_ARROW_SIZE = { 'width':60, 'height':60 }	# Dimensions of the arrow images
	HUD_ARROW_START_POS = { 'x':352, 'y':50 }		# Start position for the HUD arrows
	ARROW_COLUMN_PAD = 5
	ARROW_TIMING_FILE = 'bubble_pop_arrow_timings.txt'	# File for arrow timings
	
	#--- RECORDING MODE ---#
	RECORDING_MODE = True
	
	def __init__(self, parent, context):
		BPController.__init__(self, parent, context)
		
	def drawBG(self):
		self.context['surfDisp'].blit(self.imgBG, (0, 0))
		for i in range(self.NUM_ARROW_DIRECTIONS):
			self.context['surfDisp'].blit(
				self.imgHUDArrows[i], 
				(self.HUD_ARROW_START_POS['x'] + (i * self.IMG_ARROW_SIZE['width']) + (i * self.ARROW_COLUMN_PAD), self.HUD_ARROW_START_POS['y']))
		
	def drawSprites(self):
		for sprite in self.sprites:
			sprite.draw()
		
	def drawHUD(self):			
		pass

	def start(self):
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
		
		arrowSprite = BPSprite(self.context, (352, 540), self.imgArrows[0][0], 0)
		arrowSprite.queueAction(
			{	
				BPSprite.ACTION_IDENTIFIER:BPSprite.ACTION_POSITION,
				BPSprite.ACTION_POSITION_TARGET:(352, -60),
				BPSprite.ACTION_DURATION:3
			})
		self.sprites.append(arrowSprite)
			
	def handleUpdate(self):
		# Clear the display surface and update the sprites
		self.context['surfDisp'].fill((0, 0, 0))
		for sprite in self.sprites:
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
						'down':eventTime,
						'key':keyIndex
					})
			elif event.type == KEYUP:
				for keystroke in self.keystrokes:
					if keystroke['key'] == keyIndex and 'up' not in keystroke.keys():
						keystroke['up'] = eventTime
		elif event.key == self.KEY_QUIT_RECORDING:
			f = open(self.ARROW_TIMING_FILE, 'w')
			for keystroke in self.keystrokes:
				f.write('{0}\t{1}\t{2}\n'.format(keystroke['down'], keystroke['up'], keystroke['key']))
			f.close()
			
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

