#include "Snapper.h"

#include <cstdio>
#include <unistd.h>
#include <fstream>

#include <stdio.h>
#include <jpeglib.h>
#include <stdlib.h>


#include <gphoto2/gphoto2-camera.h>
#include <gphoto2/gphoto2-file.h>

#ifdef RPI
#include "JPEG.h"
#endif

#include "Epeg.h"

using namespace SuperBooth;

int gphoto(int code);
 
Snapper::Snapper() : 
	camera(NULL),
	context(NULL),
	cfile(NULL),
	preview_data(NULL),
	retries(5) {
	gphoto(gp_camera_new (&camera));
	context = gp_context_new();

	int ret = gp_camera_init(camera, context);
	if (ret < GP_OK) {
	 printf("No camera auto detected.\n");
	 gp_camera_free(camera);
	 camera = NULL;
	 return;
	}

#ifdef RPI
	pLogger = new Logger();
	jpeg = new JPEG((ILogger *)pLogger);
#endif
}
 
Snapper::~Snapper() {
	//if(cfile)
	//	gp_file_unref(cfile);

#ifdef RPI
	delete jpeg;
#endif
	gp_camera_unref(camera);
	gp_context_unref(context);
}


bool Snapper::valid() {
	return camera ? true : false;
}
/*void Snapper::transferPreview(unsigned int **out, unsigned int *size) {
	
}*/

// create a file on the camera with string as its contents
// save to folder/path
void Snapper::uploadFile(char *name, const char *folder, char *string) {
	CameraFile *file;
	gphoto(gp_file_new(&file));

	// append the data from string into the file
	gphoto(gp_file_append(file, string, strlen(string)));
	printf("appended\n");
	// upload the file
	//#gphoto(gp_camera_folder_put_file(camera, folder, name, GP_FILE_TYPE_NORMAL, file, context));
	gphoto(gp_filesystem_put_file(camera->fs, folder, name, GP_FILE_TYPE_NORMAL, file, context));
	printf("uploaded %s to %s\n", name, folder);
	// free the file
	gphoto(gp_file_unref(file));
}

void Snapper::setTargetCard() {
	CameraWidget *rootwidget, *mainwidget, *settingswidget, *capturetargetwidget; 
    gphoto(gp_camera_get_config(camera, &rootwidget, NULL)); 

    gphoto(gp_widget_get_child_by_name(rootwidget, 
    	"main", &mainwidget));
    
    gphoto(gp_widget_get_child_by_name(mainwidget, 
    	"settings", &settingswidget));
    gphoto(gp_widget_get_child_by_name (
    	settingswidget, "capturetarget", &capturetargetwidget));

    gphoto(gp_widget_set_value (capturetargetwidget, "Memory card"));
    gphoto(gp_camera_set_config(camera, rootwidget, NULL));
}

/* download a photo from camera */
void Snapper::downloadPicture(char *name, char *folder, unsigned int *size, char **pic) {
	if(cfile)
		gp_file_unref(cfile);

	gphoto(gp_file_new(&cfile));

	gphoto(gp_camera_file_get(camera, folder, name, GP_FILE_TYPE_NORMAL, cfile, context));

	unsigned long int pic_size;
	const char *pic_data;

	gphoto(gp_file_get_data_and_size(cfile, &pic_data, &pic_size));

	printf("downloaded picture. %d bytes\n", pic_size);
}

void Snapper::downloadResizePicture(char *name, char *folder, 
	unsigned int *size, char **pic, Epeg_Image **img) {
	if(cfile)
		gp_file_unref(cfile);

	gphoto(gp_file_new(&cfile));

	gphoto(gp_camera_file_get(camera, folder, name, GP_FILE_TYPE_NORMAL, cfile, context));

	unsigned long int pic_size;
	const char *pic_data;

	gphoto(gp_file_get_data_and_size(cfile, &pic_data, &pic_size));

	Epeg_Image *im = epeg_memory_open((unsigned char*)pic_data, pic_size);

	epeg_decode_size_set(im, size[0], size[1]);
	epeg_decode_colorspace_set(im, EPEG_RGB8);

	*pic = (char *)epeg_pixels_get(im, 0, 0, size[0], size[1]);
	*img = im;
}

void Snapper::takePicture(char *name, char *folder, unsigned int *size) {
	setTargetCard();

    CameraFilePath fpath;
	gphoto(gp_camera_capture(camera, GP_CAPTURE_IMAGE, &fpath, context));

	strcpy(name, fpath.name);
	strcpy(folder, fpath.folder);

	if(cfile)
		gp_file_unref(cfile);

	gphoto(gp_file_new(&cfile));

	CameraFileInfo info;

	gphoto(gp_camera_file_get_info(camera, folder, name, &info, context));
	size[0] = info.file.width;
	size[1] = info.file.height;
}

void Snapper::startCapturePreview(unsigned int *size) {
	if(cfile)
		gp_file_unref(cfile);

	gphoto(gp_file_new(&cfile));

	// this seems to fail first time, so retry
	if(gp_camera_capture_preview(camera, cfile, context)) {
		printf("retrying\n");
		usleep(50000);
		gphoto(gp_camera_capture_preview(camera, cfile, context));
	}

	gphoto(gp_file_get_data_and_size(cfile, &preview_data, &preview_size));

	// on ARM, call the accelerated routines to decode jpeg
	// otherwise, decode manually

#ifdef RPI
	jpeg->decode(preview_data, preview_size, &out, &im_h, &im_w);
	size[0] = im_w;
	size[1] = im_h;
	size[2] = 4;
#else
	// write to disk
	std::ofstream outfile ("preview.jpg",std::ofstream::binary);
	outfile.write (preview_data, preview_size);

	infile = fopen("preview.jpg", "rb" );

	struct jpeg_error_mgr jerr;
	/* here we set up the standard libjpeg error handler */
	cinfo.err = jpeg_std_error( &jerr );
	jpeg_create_decompress(&cinfo);
	jpeg_stdio_src( &cinfo, infile );
	jpeg_read_header(&cinfo, TRUE);
	jpeg_start_decompress(&cinfo);

	size[0] = im_w = cinfo.output_width;
	size[1] = im_h = cinfo.output_height;
	size[2] = cinfo.output_components;
#endif
} 

void Snapper::finishCapturePreview(char **raw_image) {
#ifdef RPI
#if 1
	*raw_image = out;
#else
	char *o = (char *)malloc(im_h*im_w*3);

	unsigned int x,y,z;
	for(x = 0; x < im_w; x++) {
		for(y = 0; y < im_h; y++) {
			for(z = 0; z < 3; z++) {
				o[x*im_h*3 + y*3 + z] = out[x*im_h*4 + y*4 + z];
			}
		}
	}
	*raw_image = o;
	free(out);
#endif
	return;
#else
	JSAMPROW row_pointer[1];
	unsigned long location = 0;
	int i = 0;

	row_pointer[0] = (unsigned char *)malloc( cinfo.output_width*cinfo.num_components );

	char *out = (char *)malloc(im_h*im_w*3);
	
	while( cinfo.output_scanline < cinfo.image_height ) {
		jpeg_read_scanlines( &cinfo, row_pointer, 1 );
		for( i=0; i<cinfo.image_width*cinfo.num_components;i++) 
			out[location++] = row_pointer[0][i];
	}

	*raw_image = out;

	/* wrap up decompression, destroy objects, free pointers and close open files */
	//jpeg_finish_decompress( &cinfo );
	jpeg_destroy_decompress( &cinfo );
	free( row_pointer[0] );
	fclose( infile );
#endif
}

void Snapper::capturePreview(unsigned char **out, unsigned int *size) {
	startCapturePreview(size);

	unsigned char *data = new unsigned char[cinfo.output_height * cinfo.output_width * cinfo.output_components];

}

int gphoto(int code) {
	if(code) {
		printf("ERROR: %s\n", gp_result_as_string(code));
	}
	return code;
}
