import sys, pygame
from pygame.locals import *

#---------------------------------
# Initialization
#---------------------------------
pygame.init()
DISPLAYSURF = pygame.display.set_mode((400, 300))
pygame.display.set_caption('Hello World!')


FPS = 30 # frames per second to update the screen


#---------------------------------
# MAIN 
#---------------------------------
def main():
	
	soundObj = pygame.mixer.Sound('bubble_pop.wav')
	soundObj.play()
	
	while True:
		for event in pygame.event.get():
			if event.type == QUIT:
				pygame.quit()
				sys.exit()
		pygame.display.update()
	
	soundObj.stop()


if __name__ == '__main__':
	main()