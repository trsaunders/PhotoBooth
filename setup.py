from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext
import platform

### detect if we're building this on rpi or otherwise
is_pi = True if platform.machine() == 'armv6l' else False

lib_pi = [
	"GLESv2",
	"EGL",
	"openmaxil",
	"bcm_host",
	"vcos",
	"vchiq_arm",
	"pthread",
	"rt",
	]
lib_all = ['gphoto2', 'jpeg', 'epeg']
lib_pi.extend(lib_all)

src_pi = [	
	"jpeg/Event.cpp",
	"jpeg/JPEG.cpp",
	"jpeg/Locker.cpp",
	"jpeg/Logger.cpp",
	"jpeg/OMXComponent.cpp",
	"jpeg/OMXCore.cpp",
]

src_all = [
	"SuperBooth.pyx",
	"Snapper.cpp",
]

src_pi.extend(src_all)

inc_pi = [
	"./jpeg",
	"/opt/vc/include",
	"/opt/vc/include/interface/vcos/pthreads",
	"/opt/vc/include/interface/vmcs_host/linux",
]
inc_all = [
	".",
]
inc_pi.extend(inc_all)

lib_dirs_pi = [
	"/opt/vc/lib",
]
lib_dirs_all = []
lib_dirs_pi.extend(lib_dirs_all)

def_pi = [
	('RPI', None),
	('STANDALONE', None),
	('__STDC_CONSTANT_MACROS', None),
	('__STDC_LIMIT_MACROS', None),
	('TARGET_POSIX', None),
	('_LINUX', None),
	('PIC', None),
	('_REENTRANT', None),
	('_LARGEFILE64_SOURCE', None),
	('_FILE_OFFSET_BITS', 64),
	('HAVE_LIBOPENMAX', '2'),
	('OMX', None),
	('OMX_SKIP64BIT', None),
	('USE_EXTERNAL_OMX', None),
	('HAVE_LIBBCM_HOST', None),
	('USE_EXTERNAL_LIBBCM_HOST', None),
	('USE_VCHIQ_ARM', None),
]

def_all = []

def_pi.extend(def_all)

if is_pi:
	lib = lib_pi
	src = src_pi
	inc = inc_pi
	lib_dirs = lib_dirs_pi
	defines = def_pi
else:
	lib = lib_all
	src = src_all
	inc = inc_all
	lib_dirs = lib_dirs_all
	defines = def_all

setup(
	ext_modules=[
		Extension("SuperBooth", 
			src,
			include_dirs=  inc,
			language = "c++",
			library_dirs = lib_dirs,
			libraries = lib,
			define_macros = defines),
	],
      cmdclass = {'build_ext': build_ext})
