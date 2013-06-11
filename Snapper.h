#ifndef __SNAPPER_H__
#define __SNAPPER_H__

#include <gphoto2/gphoto2-camera.h>
#include <stdio.h>
#include <jpeglib.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>

#ifdef RPI
#include "JPEG.h"
#include "Logger.h"
#endif

#include "Epeg.h"

namespace SuperBooth {
	class Snapper {
	private:
		Camera *camera;
		GPContext *context;
		CameraFile *cfile;
		unsigned long int preview_size;
		const char *preview_data;
		unsigned char retries;
		struct jpeg_decompress_struct cinfo;
		FILE *infile;
		char *out;
		unsigned int im_h, im_w;
#ifdef RPI
		JPEG *jpeg;
		Logger *pLogger;
#endif
	public:
		Snapper();
		~Snapper();
		void downloadPicture(char *name, char *folder, unsigned int *size, char **pic);
		void downloadResizePicture(char *name, char *folder, unsigned int *size, char **pic, Epeg_Image **img);
		void setTargetCard();
		void takePicture(char *name, char *folder, unsigned int *size);
		void startCapturePreview(unsigned int *size);
		void finishCapturePreview(char **out);
		void capturePreview(unsigned char **out, unsigned int *size);
	};
}

#endif