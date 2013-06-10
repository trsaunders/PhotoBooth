import pygame
import threading
import Queue
import time
import os
import SuperBooth
import math
import numpy as np

class Snappy(threading.Thread):
	snap = None
	preview_queue = None

	picture_queue = None
	picture_output = None

	picture_resize = None
	picture_resize_out = None

	preview_sem = None
	def __init__(self):
		self.snap = SuperBooth.PySnapper()
		self.preview_queue = Queue.Queue()
		self.picture_queue = Queue.Queue()
		self.picture_output = Queue.Queue()

		self.picture_resize = Queue.Queue()
		self.picture_resize_out = Queue.Queue()

		self.preview_sem = threading.Semaphore()

		threading.Thread.__init__(self)
		self.daemon = True
	def run(self):
		while 1:
			if self.picture_queue.qsize() > 0:
				queued = self.picture_queue.get()
				name, path, size = self.snap.takePicture()
				self.picture_output.put((name, path, size))
				continue

			if self.picture_resize.qsize() > 0:
				r = self.picture_resize.get()
				img = self.snap.downloadResizePicture(r[0], r[1], r[2], r[3])
				self.picture_resize_out.put(img)

			if self.preview_sem.acquire(blocking=False):
				img = self.snap.capturePreview()
				self.preview_queue.put(img)
				self.preview_sem.release()
			### always sleep a little
			time.sleep(0.05)

	def get_preview(self):
		#while self.preview_queue.qsize() > 1:
		#	print "Queue size: %d" % self.preview_queue.qsize()
		#	self.preview_queue.get(True, 3)
		return self.preview_queue.get(True, 3)
	def preview_available(self):
		return True if self.preview_queue.qsize() > 0 else False

	def take_photo(self):
		self.picture_queue.put(1)
		return self.picture_output.get()

	def get_resized(self, name, folder, width, height):
		self.picture_resize.put((name, folder, width, height))
		return self.picture_resize_out.get()
	def disable_preview(self):
		self.preview_sem.acquire(blocking=True)
		### clear any remaining frames
		with self.preview_queue.mutex:
			self.preview_queue.queue.clear()

	def enable_preview(self):
		self.preview_sem.release()

class PhotoBooth:
	screen = None;
	s_w = 0;
	s_h = 0;
	snappy = None;
	last_button = None;

	button_events = None;
	main_surface = None;

	def __init__(self):
		pygame.init()

		### set screen size
		size = self.s_w, self.s_h, = 1280, 1024

		self.screen = pygame.display.set_mode(size)

		self.init_booth()

	def set_screen_preview(self):
		size = self.s_w, self.s_h
		self.screen = pygame.display.set_mode(size)
	def set_screen_image(self):
		size = self.s_w, self.s_h
		self.screen = pygame.display.set_mode(size)

	def init_booth(self):
		# Clear the screen to start
		self.screen.fill((0, 255, 0))

		pygame.font.init()
		# Render the screen
		pygame.display.update()
		### create Snappy object with preview disabled
		self.snappy = Snappy()
		self.snappy.disable_preview()
		self.snappy.start()

	def get_button(self, button):
		if self.button_events == None:
			self.button_events = pygame.event.get()
			if len(self.button_events) == 0:
				self.button_events = None
				return False

		for event in self.button_events:
			if event.type == pygame.KEYDOWN and event.key == button:
				return True
		return False
	### reset cached button events
	### called after handling a button event
	def clear_button_events(self):
		self.button_events = None
	def one_photo_button(self):
		return self.get_button(pygame.K_SPACE)
	def multi_photo_button(self):
 		return self.get_button(pygame.K_RETURN)
 	def exit_button(self):
 		return self.get_button(pygame.K_ESCAPE)

 	def center_text(self, text, y):
 		self.main_surface.blit(
			text,
			(
				int(self.s_w/2 - text.get_width()/2),
				int(y - text.get_height()/2)
			)
		)
 	def run(self):
 		self.main_surface = pygame.display.get_surface()

 		### cache count down numbers
 		font_file = "%s/font.ttf" % os.path.dirname(os.path.realpath(__file__))
		numfont = pygame.font.Font(font_file, 200)
		cd = []
		for i in range(10):
			cd.append(numfont.render("%d" % i, 0, (0, 255, 0), (255, 0, 255)))

		### cache info texts
		info_font = pygame.font.Font(font_file, 60)
		text_press_a_button = info_font.render(
			"* PRESS BUTTON TO EXIT *", 
			0, (0, 255, 0), (255, 0, 255))
		small_info_font = pygame.font.Font(font_file, 25)
		text_website = small_info_font.render(
			"PHOTOS ONLINE @ HTTP://EMMAISGOINGTOMARRY.ME BY 1ST OF JULY", 
			0, (0, 255, 0), (255, 0, 255))
		### enable the preview
		self.snappy.enable_preview()

		to_take = 0
		taken = 0

		count_down = 0
		count_start = 0

		white = (255, 255, 255)

		print "Running"
		while True:
			update_screen = False
			if self.snappy.preview_available():
				try:
					img = self.snappy.get_preview()
				except queue.Empty:
					print "queue empty"
					break

				buf = np.getbuffer(img)

				if img.shape[2] == 4:
					imgs = pygame.image.frombuffer(buf,
						 (img.shape[0], img.shape[1]), 'RGBA')
				else:
					imgs = pygame.image.frombuffer(buf,
							 (img.shape[0], img.shape[1]), 'RGB')

				### centre the image
				px = int((self.s_w - img.shape[0])/2.0)
				py = int((self.s_h - img.shape[1])/2.0)
				self.main_surface.blit(imgs, (px, py))
				
				update_screen = True

			if count_down > 0:
				### reset taken count
				taken = 0

				### Hack: clear button events
				self.one_photo_button()
				self.multi_photo_button()

				### how long have we been counting down for?
				te = time.time() - count_start
				count_value = int(math.ceil(count_down - te))
				if count_value > 0:
					self.center_text(cd[count_value], self.s_h/2)
					pygame.display.flip()
					continue
				else:
					### reset count down
					count_down = 0
					### disable live preview
					self.snappy.disable_preview()
					### display last frame
					pygame.display.flip()
					continue

			if update_screen:
				pygame.display.flip()

			if count_down == 0 and (taken < to_take):
				if taken == 0:
					self.set_screen_image()
					self.main_surface.fill((255,0,255))


				pygame.display.flip()
				name, folder, size = self.snappy.take_photo()
				print "took photo %s saved to %s" % (name, folder)

				ratio = float(size[0])/float(size[1])
				### resize image based on number of photos in sequence
				t_w = int(self.s_w/math.sqrt(to_take))
				t_h = int(t_w/ratio)
				### calculate padding at top and bottom
				p_y = int((self.s_h-(t_h*math.sqrt(to_take)))/2)


				img = self.snappy.get_resized(name, folder, t_w, t_h)
				imgs = pygame.image.frombuffer(np.getbuffer(img),
					 (img.shape[0], img.shape[1]), 'RGB')

				### work out where the image should be blitted based on the current number
				i_x = taken % math.sqrt(to_take)
				i_y = math.floor(taken/math.sqrt(to_take))

				self.main_surface.blit(imgs, (i_x*t_w, p_y + i_y*t_h))
				pygame.display.update(pygame.Rect(i_x*t_w, p_y + i_y*t_h, t_w, t_h))
				taken += 1

				if taken == to_take:
					### blit info text
					self.center_text(text_press_a_button, int(self.s_h - p_y/2))
					self.center_text(text_website, int(p_y/2))
					pygame.display.update()

					while not self.one_photo_button() and not self.multi_photo_button() and not self.exit_button():
						self.clear_button_events()

					### clear again
					self.clear_button_events()

					self.set_screen_preview()
					
					self.snappy.enable_preview()
					self.main_surface.fill((0,255,0))
					pygame.display.flip()

			if self.one_photo_button():
				to_take = 1
				count_down = 3
				count_start = time.time()
			elif self.multi_photo_button():
				to_take = 4
				count_down = 3
				count_start = time.time()
			elif self.exit_button():
				break
			self.clear_button_events()

if __name__ == "__main__":
	booth = PhotoBooth()
	booth.run()