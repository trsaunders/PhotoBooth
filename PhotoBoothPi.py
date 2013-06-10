import os
import pygame
import time
from PhotoBooth import PhotoBooth
import RPi.GPIO as GPIO

class PhotoBoothPi(PhotoBooth):
	def __init__(self):
		disp_no = os.getenv("DISPLAY")
		if disp_no:
			print "I'm running under X display = {0}".format(disp_no)
		
		# Check which frame buffer drivers are available
		# Start with fbcon since directfb hangs with composite output
		drivers = ['fbcon', 'directfb', 'svgalib']
		found = False
		for driver in drivers:
			# Make sure that SDL_VIDEODRIVER is set
			if not os.getenv('SDL_VIDEODRIVER'):
				os.putenv('SDL_VIDEODRIVER', driver)
			try:
				pygame.display.init()
			except pygame.error:
				print 'Driver: {0} failed.'.format(driver)
				continue
			found = True
			break
	
		if not found:
			raise Exception('No suitable video driver found!')
		self.s_w = pygame.display.Info().current_w
		self.s_h = pygame.display.Info().current_h

		print "Framebuffer size: %d x %d" % (self.s_w, self.s_h)
		self.screen = pygame.display.set_mode((self.s_w, self.s_h), 
			pygame.FULLSCREEN | pygame.DOUBLEBUF | pygame.HWSURFACE,
			8
		)

		GPIO.setmode(GPIO.BCM)

		GPIO.setup(4, GPIO.IN, pull_up_down=GPIO.PUD_UP)
		GPIO.add_event_detect(4, GPIO.RISING)
		GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)
		GPIO.add_event_detect(17, GPIO.RISING)

		self.init_booth()
	def button_test(self, but):
		if self.last_button != None and (time.time() - self.last_button) < 5:
			### clear any events until then
			GPIO.event_detected(but)
			return False
		if GPIO.event_detected(but):
			self.last_button = time.time()
			#GPIO.remove_event_detect(but)
			return True
		return False
	def clear_button_events(self):
		self.button_events = None
	def one_photo_button(self):
		return self.button_test(4)
	def multi_photo_button(self):
 		return self.button_test(17)
 	def exit_button(self):
 		return False

if __name__ == "__main__":
	booth = PhotoBoothPi()
	booth.run()