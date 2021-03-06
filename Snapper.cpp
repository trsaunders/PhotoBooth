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
	retries(5) {

	if(!connect())
		return;

#ifdef RPI
	pLogger = new Logger();
	jpeg = new JPEG((ILogger *)pLogger);
#endif
}
 
Snapper::~Snapper() {
#ifdef RPI
	delete jpeg;
#endif
	gp_camera_unref(camera);
	gp_context_unref(context);
}


bool Snapper::valid() {
	return camera ? true : false;
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
void Snapper::downloadPicture(char *name, char *folder, char **out, unsigned int *out_size) {
	connect();

	CameraFile *download_file;

	gphoto(gp_file_new(&download_file));

	gphoto(gp_camera_file_get(camera, folder, name, GP_FILE_TYPE_NORMAL, download_file, context));

	unsigned long int pic_size;
	const char *pic_data;

	gphoto(gp_file_get_data_and_size(download_file, &pic_data, &pic_size));

	decodeJPEG(pic_data, pic_size, out, out_size);

	gphoto(gp_file_unref(download_file));
}

void Snapper::downloadResizePicture(char *name, char *folder, 
	unsigned int *size, char **pic, Epeg_Image **img) {
	connect();

	CameraFile *download_file;

	gphoto(gp_file_new(&download_file));

	gphoto(gp_camera_file_get(camera, folder, name, GP_FILE_TYPE_NORMAL, download_file, context));

	unsigned long int pic_size;
	const char *pic_data;

	gphoto(gp_file_get_data_and_size(download_file, &pic_data, &pic_size));

	Epeg_Image *im = epeg_memory_open((unsigned char*)pic_data, pic_size);

	epeg_decode_size_set(im, size[0], size[1]);
	epeg_decode_colorspace_set(im, EPEG_RGB8);

	*pic = (char *)epeg_pixels_get(im, 0, 0, size[0], size[1]);
	*img = im;

	gphoto(gp_file_unref(download_file));
}

void Snapper::takePicture(char *name, char *folder, unsigned int *size) {
	connect();

	setTargetCard();

    CameraFilePath fpath;
	gphoto(gp_camera_capture(camera, GP_CAPTURE_IMAGE, &fpath, context));

	strcpy(name, fpath.name);
	strcpy(folder, fpath.folder);

	CameraFileInfo info;

	gphoto(gp_camera_file_get_info(camera, folder, name, &info, context));
	size[0] = info.file.width;
	size[1] = info.file.height;
}


// read jpeg data from jpeg of length jpeg_len
// store pointer to decoded memory in out
// record size of image in size
void Snapper::decodeJPEG(const char *jpeg_data, unsigned long int jpeg_len, char **out, unsigned int *size) {
#ifdef RPI
	unsigned int width=0, height=0;

	if(jpeg->decode(jpeg_data, jpeg_len, out, &im_w, &im_h)) {
		printf("there was an error decoding the jpeg\n");
		*out = NULL;
	}

	size[0] = im_w;
	size[1] = im_h;
	size[2] = 4;
#else
	// write to disk
	std::ofstream outfile ("preview.jpg",std::ofstream::binary);
	outfile.write (jpeg_data, jpeg_len);

	FILE *infile = fopen("preview.jpg", "rb" );

	struct jpeg_error_mgr jerr;
	struct jpeg_decompress_struct cinfo;
	/* here we set up the standard libjpeg error handler */
	cinfo.err = jpeg_std_error( &jerr );
	jpeg_create_decompress(&cinfo);
	jpeg_stdio_src( &cinfo, infile );
	jpeg_read_header(&cinfo, TRUE);
	jpeg_start_decompress(&cinfo);

	size[0] = cinfo.output_width;
	size[1] = cinfo.output_height;
	size[2] = cinfo.output_components;
	JSAMPROW row_pointer[1];
	unsigned long location = 0;
	int i = 0;

	row_pointer[0] = (unsigned char *)malloc( cinfo.output_width*cinfo.num_components );

	char *o = (char *)malloc(size[0]*size[1]*3);
	
	while( cinfo.output_scanline < cinfo.image_height ) {
		jpeg_read_scanlines( &cinfo, row_pointer, 1 );
		for( i=0; i<cinfo.image_width*cinfo.num_components;i++) 
			o[location++] = row_pointer[0][i];
	}

	*out = o;

	/* wrap up decompression, destroy objects, free pointers and close open files */
	//jpeg_finish_decompress( &cinfo );
	jpeg_destroy_decompress( &cinfo );
	free( row_pointer[0] );
	fclose( infile );

#endif
}

void Snapper::capturePreview(char **out, unsigned int *size) {
	connect();

	const char* preview_data;
	unsigned long int preview_size;

	CameraFile *preview_file;

	gphoto(gp_file_new(&preview_file));

	// this seems to fail first time, so retry
	if(gp_camera_capture_preview(camera, preview_file, context)) {
		usleep(50000);
		gphoto(gp_camera_capture_preview(camera, preview_file, context));
	}

	gphoto(gp_file_get_data_and_size(preview_file, &preview_data, &preview_size));

	std::ofstream outfile ("preview.jpg",std::ofstream::binary);
	outfile.write (preview_data, preview_size);

	decodeJPEG(preview_data, preview_size, out, size);

	gp_file_unref(preview_file);
}

int Snapper::connect() {
	if(camera && context)
		return 1;

	gphoto(gp_camera_new (&camera));
	context = gp_context_new();

	int ret = gp_camera_init(camera, context);
	if (ret < GP_OK) {
	 printf("No camera auto detected.\n");
	 gp_camera_free(camera);
	 camera = NULL;
	 return 0;
	}

	return 1;
}

void Snapper::disconnect() {
	if(camera)
		gp_camera_unref(camera);
	if(context)
		gp_context_unref(context);

	camera = NULL;
	context = NULL;
}


int gphoto(int code) {
	if(code) {
		printf("ERROR: %s\n", gp_result_as_string(code));
	}
	return code;
}
