import os
import pygame
import time
from PhotoBoothGL import PhotoBoothGL
import RPi.GPIO as GPIO
import Queue

class PhotoBoothGLPi(PhotoBoothGL):
	last_button = None;
	left_button_queue = None
	right_button_queue = None
	def init(self):
		### queue button inputs
		self.left_button_queue = Queue.Queue()
		self.right_button_queue = Queue.Queue()

		self.start()

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
		#global last_button
		#last_button = time.time()
		return

	def left_button_pressed(self):
		#with self.left_button_queue.mutex:
		if self.left_button_queue.qsize() == 0:
			self.left_button_queue.put(time.time())

	def right_button_pressed(self):
		#with self.right_button_queue.mutex:
		if self.right_button_queue.qsize() == 0:
			self.right_button_queue.put(time.time())

	def one_photo_button(self):
		if self.left_button_queue.qsize() > 0:
			### empty the queue
			while self.left_button_queue.qsize() > 0:
				self.left_button_queue.get()
			return True

		return False
	def multi_photo_button(self):
 		if self.right_button_queue.qsize() > 0:
 			while self.right_button_queue.qsize() > 0:
 				self.right_button_queue.get()
 			return True
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
		print "left button"
		booth.left_button_pressed()
	elif channel == 17:
		print "right button"
		booth.right_button_pressed()

if __name__ == "__main__":
	print "Starting RPi photobooth"
	GPIO.setmode(GPIO.BCM)

	GPIO.setup(4, GPIO.IN, pull_up_down=GPIO.PUD_UP)
	GPIO.add_event_detect(4, GPIO.RISING, callback=button_callback)
	GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)
	GPIO.add_event_detect(17, GPIO.RISING, callback=button_callback)

	booth = PhotoBoothGLPi(1280, 1024)
	booth.run()