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
		unsigned char retries;
		unsigned int im_h, im_w;

#ifdef RPI
		JPEG *jpeg;
		Logger *pLogger;
#endif
	public:
		Snapper();
		~Snapper();
		int connect();
		void disconnect();
		bool valid();
		void downloadPicture(char *, char *, char **, unsigned int *);
		void downloadResizePicture(char *name, char *folder, unsigned int *size, char **pic, Epeg_Image **img);
		void setTargetCard();
		void takePicture(char *name, char *folder, unsigned int *size);
		void capturePreview(char **out, unsigned int *size);
		void decodeJPEG(const char *jpeg, unsigned long int jpeg_len, char **out, unsigned int *size);
	};
}

#endif