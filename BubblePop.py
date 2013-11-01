import sys, pygame
from pygame.locals import *

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
	
	ARROW_LEFT = 0
	ARROW_DOWN = 1
	ARROW_UP = 2
	ARROW_RIGHT = 3
	
	NUM_ARROW_DIRECTIONS = 4	# Left, Down, Up, Right
	NUM_ARROW_TYPES = 4			# Green, Orange, Pink, Blue
	NUM_ARROW_STATES = 4		# No fill, 1-bar fill, 2-bar fill, 3-bar fill
	
	IMG_ARROW_SIZE = { 'width':60, 'height':60 }	# Dimensions of the arrow images
	HUD_ARROW_START_POS = { 'x':352, 'y':50 }		# Start position for the HUD arrows
	ARROW_COLUMN_PAD = 5
	
	def __init__(self, parent, context):
		BPController.__init__(self, parent, context)
		
	def drawBG(self):
		self.context['surfDisp'].blit(self.imgBG, (0, 0))
		
	def drawHUD(self):
		for i in range(self.NUM_ARROW_DIRECTIONS):
			self.context['surfDisp'].blit(
				self.imgHUDArrows[i], 
				(self.HUD_ARROW_START_POS['x'] + (i * self.IMG_ARROW_SIZE['width']) + (i * self.ARROW_COLUMN_PAD), self.HUD_ARROW_START_POS['y']))

	def start(self):
		# Load the level data
		self.levelData.append([5, 5, self.ARROW_LEFT]);
		
		# Load the images
		self.imgBG = pygame.image.load('bg_gameplay.jpg').convert()
		for i in range(self.NUM_ARROW_DIRECTIONS):	
			self.imgHUDArrows.append(pygame.image.load('hud_arrow_{0}.png'.format(i)).convert_alpha())
		
		if self.context['musicEnabled'] == True:
			self.context['musicObj'].play()
			
	def handleUpdate(self):
		# Clear the display surface
		self.context['surfDisp'].fill((0, 0, 0))
		
		# Draw all the elements
		self.drawBG()
		self.drawHUD()
		
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
	bpContext['FPS'] = 30 
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

