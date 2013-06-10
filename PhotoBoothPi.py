import os
import pygame
import time
from PhotoBooth import PhotoBooth
import RPi.GPIO as GPIO
import Queue

class PhotoBoothPi(PhotoBooth):
	last_button = None;
	left_button_queue = None
	right_button_queue = None
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

		self.init_booth()

		### queue button inputs
		self.left_button_queue = Queue.Queue()
		self.right_button_queue = Queue.Queue()

	### Pi is slow. so use 8bit images to keep this fast
	def set_screen_preview(self):
		return
		#size = self.s_w, self.s_h
		# self.screen = pygame.display.set_mode(size, 
		# 	pygame.FULLSCREEN | pygame.DOUBLEBUF | pygame.HWSURFACE,
		# 	32
		# )
		# self.main_surface = pygame.display.get_surface()

	### when displaying captured (not live) images don't make 8bit
	def set_screen_image(self):
		return
		#print "setting screen to 32 bit"
		# #size = self.s_w, self.s_h
		# self.screen = pygame.display.set_mode(size, 
		# 	pygame.FULLSCREEN | pygame.DOUBLEBUF | pygame.HWSURFACE,
		# 	32
		# )
		# self.main_surface = pygame.display.get_surface()

	def button_test(self, but):
		return False
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
		return

	def left_button_pressed(self):
		self.left_button_queue.put(True)

	def right_button_pressed(self):
		self.right_button_queue.put(True)

	def one_photo_button(self):
		if self.left_button_queue.qsize() > 0:
			return self.left_button_queue.get()

		return False
	def multi_photo_button(self):
 		if self.right_button_queue.qsize() > 0:
 			return self.right_button_queue.get()
 		return False
 	def exit_button(self):
 		return False

booth = None
last_button = None
### minimum interval between button presses in seconds
but_int = 1

def button_callback(channel):
	global booth, last_button, but_int
	if last_button != None and (time.time() - last_button) < but_int:
		### ignore
		return

	last_button = time.time()

	if channel == 4:
		booth.left_button_pressed()
	elif channel == 17:
		booth.right_button_pressed()

if __name__ == "__main__":
	GPIO.setmode(GPIO.BCM)

	GPIO.setup(4, GPIO.IN, pull_up_down=GPIO.PUD_UP)
	GPIO.add_event_detect(4, GPIO.RISING, callback=button_callback)
	GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)
	GPIO.add_event_detect(17, GPIO.RISING, callback=button_callback)
	booth = PhotoBoothPi()
	booth.run()