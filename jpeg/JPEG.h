// Written by Matt Ownby, August 2012
// You are free to use this for educational/non-commercial use

#ifdef RPI

#ifndef JPEG_H
#define JPEG_H

#include "OMXComponent.h"
#include "ILogger.h"
#include <vector>	// for memory buffers
#include "OMXCore.h"

class JPEG
{
public:
	JPEG(ILogger *pLogger);
	~JPEG();
	static unsigned int RefreshTimer();
	int decode(const char* data, unsigned int length, char **out, unsigned int *height, unsigned int *width);

private:

	//
	unsigned int *width_out;
	unsigned int *height_out;
	int init();
	int finish();
	void OnDecoderOutputChanged();

	void OnDecoderOutputChangedAgain();

	///////
	IOMXCoreSPtr core;
	IOMXCore *pCore;
	OMX_PORT_PARAM_TYPE port;
	OMX_IMAGE_PARAM_PORTFORMATTYPE imagePortFormat;
	OMX_PARAM_PORTDEFINITIONTYPE portdef;




	IOMXComponent *m_pCompDecode, *m_pCompResize;
	ILogger *m_pLogger;
	int m_iInPortDecode, m_iOutPortDecode;
	int m_iInPortResize, m_iOutPortResize;
	void *m_pBufOutput;
	OMX_BUFFERHEADERTYPE *m_pHeaderOutput;

	vector<OMX_BUFFERHEADERTYPE *> vpBufHeaders;	// vector to hold all of the buffer headers
	int iBufferCount;
};

#endif // JPEG_H
#endif