import sys, pygame
from pygame.locals import *

#------------------------------
# BPController class
#------------------------------
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
	"""
	context = None		# Game Context
	prevState = None	# Previous State
	state = None		# Current State
	parent = None		# Parent Controller
	child = None		# Child Controller
	
	def __init__(self, parent, context):
		self.parent = parent
		self.context = context
		
	def launchChild(self, child):
		self.child = child
		child.start()
		
	def start(self):
		pass
		
	def exit(self):
		if self.parent != None:
			self.parent.onChildExit()
			
	def changeState(self, state):
		self.prevState = self.state
		self.state = state
		
	def onEvent(self, event):
		if self.child != None:
			self.child.onEvent(event)
		elif self.child == None:
			self.handleEvent(event)
		
	def onChildExit(self):
		self.handleChildExit()
		self.child = None		
		
	def handleChildExit(self):
		pass
		
	def handleEvent(self, event):
		pass

#------------------------------
# BPLaunchController class
#------------------------------
class BPLaunchController(BPController):
	"""
		Renders the start screen and waits for a keypress.
	"""
	def __init__(self, parent, context):
		BPController.__init__(self, parent, context)
		
	def start(self):
		startImg = pygame.image.load('start.jpg')			
		self.context['surfDisp'].blit(startImg, (0, 0))
		
	def handleEvent(self, event):
		if event.type == KEYDOWN:
			self.exit()
			
#------------------------------
# BPGameplayController class
#------------------------------
class BPGameplayController(BPController):
	"""
		The main gameplay state controller
	"""
	def __init__(self, parent, context):
		BPController.__init__(self, parent, context)

	def start(self):
		self.context['surfDisp'].fill((0, 0, 0))
		if self.context['musicEnabled'] == True:
			self.context['musicObj'].play()
	
#------------------------------
# BPGame class
#------------------------------
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
				
			pygame.display.update()

#------------------------------
# main() function
#------------------------------
def main():
	pygame.init()
	
	bpContext = {}
	bpContext['pygame'] = pygame
	bpContext['FPS'] = 30 
	bpContext['windowSize'] = { 'width':1280, 'height':720 }
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

#------------------------------
# Call main()
#------------------------------
if __name__ == '__main__':
	main()

