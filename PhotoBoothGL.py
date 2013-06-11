import pygame
from rpigl import glesutils, transforms
from rpigl.gles2 import *
#from pygame.locals import *
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


# A GLSL (GL Shading Language)  program consists of at least two shaders:
# a vertex shader and a fragment shader.
# Here is the vertex shader.
vertex_glsl = """
uniform mat4 mvp_mat; // a uniform is an input to the shader which is the same for all vertices
uniform mat4 scale_mat;
uniform mat4 trans_mat;
attribute vec2 vertex_attrib; // an attribute is a vertex-specific input to the vertex shader
attribute vec2 texcoord_attrib; // an attribute is a vertex-specific input to the vertex shader

varying vec2 texcoord_var;  // a varying is output to the vertex shader and input to the fragment shader

void main(void) {
  gl_Position = mvp_mat * scale_mat * trans_mat * vec4(vertex_attrib, 0.0, 1.0);
  texcoord_var = texcoord_attrib;
}
"""

fragment_glsl = """
uniform sampler2D texture; // access the texture
varying vec2 texcoord_var;
void main(void) {
  gl_FragColor = texture2D(texture, texcoord_var);
}
"""
# The array spec: names and formats of the per-vertex attributes
#   vertex_attrib:2h  = two signed short integers  
#   color_attrib:3Bn  = three unsigned bytes, normalized (i.e. shader scales number 0..255 back to a float in range 0..1)
array_spec = glesutils.ArraySpec("vertex_attrib,texcoord_attrib:2h")

pink = (255,0, 200)
green = (0, 253, 0)

class Texture:
	def __init__(self, img, booth):
		self.img = img
		self.booth = booth

		if type(img) == pygame.Surface:
			self.h = img.get_height()
			self.w = img.get_width()
			### for some reason we need to flip surface
			mirrored = pygame.transform.flip(img, True, False)
			texture_data = glesutils.TextureData.from_surface(mirrored)
		elif type(img) == np.ndarray:
			self.w = img.shape[0]
			self.h = img.shape[1]
			format = GL_RGB if img.shape[2] == 3 else GL_RGBA
			texture_data = glesutils.TextureData(img.ctypes.data, img.shape[0], img.shape[1], format)
		else:
			raise Exception("unknown type: %s" % type(img))

		self.texture = glesutils.Texture.from_data(texture_data)
	### cx, cy are center coordinates
	### scale is size relative to whole window
	def draw(self):

		### preserve aspect ratio of image
		aspect = float(self.booth.height)*float(self.w)/(float(self.h)*float(self.booth.width))
		### a scale value of 2 covers whole window
		sx = 2.0#/float(scale)
		sy = 2.0#/(float(scale)*aspect)

		#tx = float(cx)/float(self.booth.width)
		#ty = float(cy)/float(self.booth.height)

		self.booth.trans_mat.value = transforms.translation((-0.5, -0.5, 0.0))
		self.booth.scale_mat.value = transforms.stretching(2.0, 2.0/aspect,1)
		#print("Texture size: %dx%d" % (texture_data.width, texture_data.height))
		self.booth.program.use()
		self.texture.bind(self.booth.program.uniform.texture.value)
		self.booth.drawing.draw()

def position_full(surf, pos, size):
	full_screen_surf = pygame.Surface(size, pygame.SRCALPHA, 32)
	px = int(pos[0] - surf.get_width()/2.0)
	py = int(pos[1] - surf.get_height()/2.0)
	full_screen_surf.blit(surf.convert_alpha(), (px, py))
	return full_screen_surf

class PhotoBoothGL (glesutils.GameWindow):
	framerate = 20
	snappy = None;

	button_events = None;

	preview_texture = None;

	photos = []
	to_take = 0
	taken = 0
	count_down = 0
	count_start = 0

	def scrsize(self):
		return (self.width, self.height)
	def init(self):
		self.start()

	def start(self):
		#pygame.mouse.set_visible(False)
		# compile vertex and fragment shaders
		vertex_shader = glesutils.VertexShader(vertex_glsl)
		fragment_shader = glesutils.FragmentShader(fragment_glsl)
		# link them together into a program
		self.program = glesutils.Program(vertex_shader, fragment_shader)

		# set the background to RGBA = (1, 0, 0, 1) 
		glClearColor(green[0]/255.0, green[1]/255.0, green[2]/255.0, 1)

		# set up pre-multiplied alpha
		glEnable(GL_BLEND)
		glBlendFunc(GL_ONE, GL_ONE_MINUS_SRC_ALPHA)
		# load uniforms
		self.mvp_mat = self.program.uniform.mvp_mat
		self.scale_mat = self.program.uniform.scale_mat
		self.trans_mat = self.program.uniform.trans_mat
		self.mvp_mat.value = transforms.rotation_degrees(180, "z")
		self.scale_mat.value = transforms.stretching(1,1,1)
		self.trans_mat.value = transforms.translation((-0.5, -0.5, 0.0))

		# bind uniform named "texture" to texture unit 1
		# normally, when using only one texture, 0 would be more logical,
		# but this is just for demo purposes
		self.program.uniform.texture.value = 1 # bind texture to texture unit 1
		positions = ((0, 0), (0, 1), (1, 1), (1, 0))
		elements = (0, 1, 2, 0, 2, 3)

		# create an array buffer from the spec
		# note: all buffer objects are automatically bound on creation
		self.drawing = array_spec.make_drawing(vertex_attrib=positions, elements=elements)
		### cache count down numbers
 		font_file = "%s/font.ttf" % os.path.dirname(os.path.realpath(__file__))
		numfont = pygame.font.Font(font_file, 200)
		self.cd = []
		for i in range(4):
			surf = numfont.render("%d" % (i), 0, green, pink)
			pos = (self.width/2, self.height/2)
			self.cd.append(Texture(position_full(surf, pos, self.scrsize()), self))

		gap = int((self.height - (self.width/1.5))/4)
		### cache info texts
		info_font = pygame.font.Font(font_file, 60)
		surf_text_press_button = info_font.render(
			"* PRESS BUTTON TO EXIT *", 
			0, green, pink)
		self.text_press_button = Texture(
			position_full(surf_text_press_button, (self.width/2, self.height-gap), (self.width, self.height)), self)

		small_info_font = pygame.font.Font(font_file, 25)
		surf_text_website = small_info_font.render(
			"PHOTOS ONLINE @ HTTP://EMMAISGOINGTOMARRY.ME BY 1ST OF JULY", 
			0, green, pink)
		self.text_website = Texture(
			position_full(surf_text_website, (self.width/2, gap), (self.width, self.height)), self)

		self.init_booth()

		### create Snappy object with preview disabled
		self.snappy = Snappy()
		self.snappy.disable_preview()
		self.snappy.start()

		### enable the preview
		self.snappy.enable_preview()
	def init_booth(self):
		### nothing to do
		return

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

	def loop(self):
		#print "to take: %d taken: %d count down: %d" % (self.to_take, self.taken, self.count_down)
		if self.snappy.preview_available():
			try:
				img = self.snappy.get_preview()
			except queue.Empty:
				print "queue empty"
				return False

			self.preview_texture = Texture(img, self)

		if self.preview_texture != None:
			self.preview_texture.draw()

		### draw the count down timer
		if self.count_down > 0:
			### reset taken count
			self.taken = 0

			### Hack: clear button events
			self.one_photo_button()
			self.multi_photo_button()

			### how long have we been counting down for?
			te = time.time() - self.count_start
			remaining = self.count_down - te
			#print "counting down: %2.3f" % remaining
			count_value = int(math.ceil(remaining))
			self.cd[count_value].draw()
			if remaining > 0:
				return True
			### reset count down
			self.count_down = 0
			### disable live preview
			self.snappy.disable_preview()
			### set background to pink
			glClearColor(pink[0]/255.0, pink[1]/255.0, pink[2]/255.0, 1)
			### delete live preview
			self.preview_texture = None
			self.photos = []

			return True

		### take the pictures
		if self.count_down == 0 and (self.taken < self.to_take):
			name, folder, size = self.snappy.take_photo()
			print "took photo %s saved to %s" % (name, folder)

			### number of images across
			na = math.sqrt(self.to_take)
			ratio = float(size[0])/float(size[1])
			### resize image based on number of photos in sequence
			t_w = int(self.width/na)
			t_h = int(t_w/ratio)
			### calculate padding at top and bottom
			p_y = int((self.height-(t_h*na))/2)

			img = self.snappy.get_resized(name, folder, t_w, t_h)
			imgs = pygame.image.frombuffer(np.getbuffer(img),
				 (img.shape[0], img.shape[1]), 'RGB')

			### work out where the image should be blitted based on the current number
			i_x = self.taken % na
			i_y = math.floor(self.taken/na)

			#self.main_surface.blit(imgs, (i_x*t_w, p_y + i_y*t_h))
			pos = (i_x*t_w+int(t_w/2), p_y + i_y*t_h + int(t_h/2))
			print "placing photo at %d,%d" % pos
			img_surf = position_full(imgs, pos, self.scrsize())

			self.photos.append(Texture(img_surf, self))

			### draw this and any previous photos
			for ph in self.photos:
				ph.draw()

			self.taken += 1

			if self.taken == self.to_take:
				### blit info text
				self.text_website.draw()
				self.text_press_button.draw()
				self.swap_buffers()
				while not self.one_photo_button() and not self.multi_photo_button() and not self.exit_button():
					self.clear_button_events()

				### clear again
				self.clear_button_events()

				### reset background colour to green
				glClearColor(green[0]/255.0, green[1]/255.0, green[2]/255.0, 1)

				self.photos = []
				self.to_take = 0
				self.taken = 0

				self.snappy.enable_preview()
		ob = self.one_photo_button()
		mb = self.multi_photo_button()
		if ob or mb:
			self.count_down = 3
			self.count_start = time.time()

			if ob:
				self.to_take = 1
			elif mb:
				self.to_take = 4
		if self.exit_button():
			return False

		self.clear_button_events()
		return True

	def draw(self):
		if not self.loop():
			self.done = True
	#def on_frame(self, time):
	#	print "frame"

if __name__ == "__main__":
	booth = PhotoBoothGL(1280, 1024, pygame.RESIZABLE).run()