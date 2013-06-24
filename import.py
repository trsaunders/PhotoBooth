from glob import glob
import argparse
import os, os.path
import csv
import numpy as np
from math import sqrt
from scipy.misc import imsave, imread, imresize

parser = argparse.ArgumentParser(description='Import + Process Photobooth images')
parser.add_argument('path', help='path containing data')

args = parser.parse_args();

pic_lists = glob("%s/pictures_*.txt" % args.path)

images = dict()
image_sets = []

for pl in pic_lists:
	stat = os.stat(pl)
	if not stat.st_size:
		continue

	reader = csv.reader(open(pl, 'rb'), delimiter='\t')

	im_set = []

	for row in reader:
		if row[0] == '':
			continue

		if not os.path.exists("%s/pics/%s" % (args.path, row[0])):
			continue

		images[row[0]] = len(image_sets)
		im_set.append(row[0])

		if int(row[1]) == (int(row[2]) - 1):
			image_sets.append(im_set)
			im_set = []

pics = glob("%s/pics/*.JPG" % args.path)

for pic in pics:
	ifn = os.path.basename(pic)
	try:
		im = images[ifn]
	except:
		print "No definition for %s" % ifn

border = 100

i = 1

for s in image_sets:
	I = [imread("%s/pics/%s" % (args.path, x)) for x in s]
	sc = int(sqrt(len(I)))

	O = np.zeros_like(I[0])
	h = O.shape[0]
	w = O.shape[1]
	j = 0
	print O.shape
	for x in range(sc):
		for y in range(sc):
			print "resizing by %2.3f" % (1.0/float(sc))
			R = imresize(I[j], 1.0/float(sc))
			print R.shape
			O[x*h/sc:(x+1)*h/sc, y*w/sc:(y+1)*w/sc, :] = R
			j += 1

	out_path = "%s/out/%s" % (args.path, s[0])
	imsave(out_path, O)

	print "[%d/%d] wrote to %s" % (i, len(image_sets), out_path)
	i += 1
