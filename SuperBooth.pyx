import cython

from libc.stdlib cimport free
from cpython cimport PyObject, Py_INCREF

import numpy as np
cimport numpy as np

# Numpy must be initialized. When using numpy from C or Cython you must
# _always_ do that, or you will have segfaults
np.import_array()

cdef extern from "gphoto2/gphoto2-camera.h":
    struct CameraFilePath:
        char name[128]
        char folder[1024]

cdef extern from "Epeg.h":
    struct _Epeg_Image:
        pass
    ctypedef _Epeg_Image Epeg_Image
    void epeg_pixels_free(Epeg_Image *, const void *)
    void epeg_close(Epeg_Image *)

cdef extern from "Snapper.h" namespace "SuperBooth":
    cdef cppclass Snapper:
        Snapper()
        #int x0, y0, x1, y1
        #int getLength()
        void downloadPicture(char *, char *, unsigned int *, char **)
        void downloadResizePicture(char *, char *, unsigned int *, char **, Epeg_Image**)
        void takePicture(char *, char *, unsigned int*)
        void capturePreview(unsigned char **, unsigned int *)
        void startCapturePreview(unsigned int *)
        void finishCapturePreview(char **raw_image)


cdef class ArrayWrapper:
    cdef void* data_ptr
    cdef int h
    cdef int w
    cdef int c
 
    cdef set_data(self, int w, int h, int c, void* data_ptr):
        """ Set the data of the array
 
        This cannot be done in the constructor as it must recieve C-level
        arguments.
 
        Parameters:
        -----------
        size: int
            Length of the array.
        data_ptr: void*
            Pointer to the data            
 
        """
        self.data_ptr = data_ptr
        self.h = h
        self.w = w
        self.c = c
 
    def __array__(self):
        """ Here we use the __array__ method, that is called when numpy
            tries to get an array from the object."""
        cdef np.npy_intp shape[3]
        shape[0] = <np.npy_intp> self.w
        shape[1] = <np.npy_intp> self.h
        shape[2] = <np.npy_intp> self.c
        # Create a 1D array, of length 'size'
        ndarray = np.PyArray_SimpleNewFromData(3, shape,
                                               np.NPY_BYTE, self.data_ptr)
        return ndarray
 
    def __dealloc__(self):
        """ Frees the array. This is called by Python when all the
        references to the object are gone. """
        free(<void*>self.data_ptr)

cdef class EPEGWrapper:
    cdef void* data_ptr
    cdef Epeg_Image* im
    cdef int h
    cdef int w
    cdef int c

 
    cdef set_data(self, int w, int h, int c, void* data_ptr, Epeg_Image* im_ptr):
        """ Set the data of the array
 
        This cannot be done in the constructor as it must recieve C-level
        arguments.
 
        Parameters:
        -----------
        size: int
            Length of the array.
        data_ptr: void*
            Pointer to the data            
 
        """
        self.data_ptr = data_ptr
        self.h = h
        self.w = w
        self.c = c
        self.im = im_ptr
 
    def __array__(self):
        """ Here we use the __array__ method, that is called when numpy
            tries to get an array from the object."""
        cdef np.npy_intp shape[3]
        shape[0] = <np.npy_intp> self.w
        shape[1] = <np.npy_intp> self.h
        shape[2] = <np.npy_intp> self.c
        # Create a 1D array, of length 'size'
        ndarray = np.PyArray_SimpleNewFromData(3, shape,
                                               np.NPY_BYTE, self.data_ptr)
        return ndarray
 
    def __dealloc__(self):
        """ Frees the array. This is called by Python when all the
        references to the object are gone. """
        epeg_pixels_free(self.im, self.data_ptr)
        epeg_close(self.im)
        #free(<void*>self.data_ptr)

cdef class PySnapper:
    cdef Snapper *snapper      # hold a C++ instance which we're wrapping
    def __cinit__(self):
        self.snapper = new Snapper()
    def __dealloc__(self):
        del self.snapper
    def takePicture(self):
        cdef char name[128]
        cdef char folder[1024]
        cdef unsigned int size[2]
        self.snapper.takePicture(name, folder, size)
        cdef bytes py_name = name
        cdef bytes py_folder = folder
        return py_name, py_folder, (size[0], size[1])
    def downloadPicture(self, name, folder):
        cdef char* py_name = name
        cdef char* py_folder = folder
        cdef char *out
        cdef unsigned int size[2]
        self.snapper.downloadPicture(name, folder, size, &out)
    def downloadResizePicture(self, name, folder, width, height):
        cdef char* py_name = name
        cdef char* py_folder = folder
        cdef char *out
        cdef Epeg_Image *img
        cdef unsigned int size[2]
        size[0] = width
        size[1] = height
        self.snapper.downloadResizePicture(name, folder, size, &out, &img)

        cdef np.ndarray ndarray
        array_wrapper = EPEGWrapper()
        #array_wrapper.set_data(size[0], size[1], 4, <void*> out) 
        array_wrapper.set_data(size[0], size[1], 3, <void*> out, img) 
        ndarray = np.array(array_wrapper, copy=False)
        # Assign our object to the 'base' of the ndarray object
        ndarray.base = <PyObject*> array_wrapper
        # Increment the reference count, as the above assignement was done in
        # C, and Python does not know that there is this additional reference
        Py_INCREF(array_wrapper)
        return ndarray

    def capturePreview(self):
        cdef unsigned int size[3]
        self.snapper.startCapturePreview(size)
        cdef char *out
        self.snapper.finishCapturePreview(&out)

        cdef np.ndarray ndarray
        array_wrapper = ArrayWrapper()
        #array_wrapper.set_data(size[0], size[1], 4, <void*> out) 
        array_wrapper.set_data(size[0], size[1], size[2], <void*> out) 
        ndarray = np.array(array_wrapper, copy=False)
        # Assign our object to the 'base' of the ndarray object
        ndarray.base = <PyObject*> array_wrapper
        # Increment the reference count, as the above assignement was done in
        # C, and Python does not know that there is this additional reference
        Py_INCREF(array_wrapper)
        return ndarray
        #self.snapper.capturePreview(NULL, NULL)