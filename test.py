import sys
import os
faster_rcnn_root = os.getenv('FASTER_RCNN_ROOT', '.')
sys.path.append(os.path.join(faster_rcnn_root, "tools"))
import _init_paths # this is necessary
from fast_rcnn.config import cfg as faster_rcnn_config
from fast_rcnn.test import im_detect
from fast_rcnn.nms_wrapper import nms
sys.path.append(os.path.join(faster_rcnn_root, "python"))
import caffe

faster_rcnn_config.TEST.HAS_RPN = True  # Use RPN for proposals
prototxt = '/gabriel-ikea/model/faster_rcnn_test.pt'
caffemodel = '/gabriel-ikea/model/model.caffemodel'

caffe.set_mode_gpu()
caffe.set_device(0)
faster_rcnn_config.GPU_ID = 0
net = caffe.Net(prototxt, caffemodel, caffe.TEST)

import cv2
img = cv2.imread('ikea-01046.jpeg', -1)

import sys
import numpy
numpy.set_printoptions(threshold=sys.maxsize)
print(im_detect(net, img))
