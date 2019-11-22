#
# Cloudlet Infrastructure for Mobile Computing
#   - Task Assistance
#
#   Author: Zhuo Chen <zhuoc@cs.cmu.edu>
#           Roger Iyengar <iyengar@cmu.edu>
#
#   Copyright (C) 2011-2019 Carnegie Mellon University
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#

import numpy as np
import logging
from gabriel_server import cognitive_engine
from gabriel_protocol import gabriel_pb2
import instruction_pb2
import instructions
import sys
import os
import cv2

faster_rcnn_root = os.getenv('FASTER_RCNN_ROOT', '.')
sys.path.append(os.path.join(faster_rcnn_root, "tools"))
import _init_paths # this is necessary
from fast_rcnn.config import cfg as faster_rcnn_config
from fast_rcnn.test import im_detect
from fast_rcnn.nms_wrapper import nms
sys.path.append(os.path.join(faster_rcnn_root, "python"))
import caffe


PROTOTXT = 'model/faster_rcnn_test.pt'
CAFFEMODEL = 'model/model.caffemodel'

# Max image width and height
IMAGE_MAX_WH = 640

CONF_THRESH = 0.5
NMS_THRESH = 0.3


if not os.path.isfile(CAFFEMODEL):
    raise IOError(('{:s} not found.').format(CAFFEMODEL))


faster_rcnn_config.TEST.HAS_RPN = True  # Use RPN for proposals

logger = logging.getLogger(__name__)


def reorder_objects(result):
    # build a mapping between faster-rcnn recognized object order to a
    # standard order
    object_mapping = [-1] * len(instructions.LABELS)
    with open(os.path.join('model', 'labels.txt')) as f:
        lines = f.readlines()
        for idx, line in enumerate(lines):
            line = line.strip()
            object_mapping[idx] = instructions.LABELS.index(line)

    for i in range(result.shape[0]):
        result[i, -1] = object_mapping[int(result[i, -1] + 0.1)]

    return result


class IkeaEngine(cognitive_engine.Engine):
    def __init__(self, cpu_only):
        if cpu_only:
            caffe.set_mode_cpu()
        else:
            caffe.set_mode_gpu()

            # 0 is the default GPU ID
            caffe.set_device(0)
            faster_rcnn_config.GPU_ID = 0

        self.net = caffe.Net(PROTOTXT, CAFFEMODEL, caffe.TEST)

        # Warmup on a dummy image
        img = 128 * np.ones((300, 500, 3), dtype=np.uint8)
        for i in range(2):
            _, _= im_detect(self.net, img)
        logger.info("Caffe net has been initilized")

    def _detect_object(self, img):
        scores, boxes = im_detect(self.net, img)

        result = None
        for cls_idx in range(len(instructions.LABELS)):
            cls_idx += 1 # because we skipped background
            cls_boxes = boxes[:, 4 * cls_idx : 4 * (cls_idx + 1)]
            cls_scores = scores[:, cls_idx]

            # dets: detected results, each line is in
            #       [x1, y1, x2, y2, confidence] format
            dets = np.hstack((cls_boxes, cls_scores[:, np.newaxis])).astype(
                np.float32)

            # non maximum suppression
            keep = nms(dets, NMS_THRESH)
            dets = dets[keep, :]

            # filter out low confidence scores
            inds = np.where(dets[:, -1] >= CONF_THRESH)[0]
            dets = dets[inds, :]

            # now change dets format to [x1, y1, x2, y2, confidence, cls_idx]
            dets = np.hstack(
                (dets, np.ones((dets.shape[0], 1)) * (cls_idx - 1)))

            # combine with previous results (for other classes)
            if result is None:
                result = dets
            else:
                result = np.vstack((result, dets))

        return result


    def handle(self, from_client):
        if from_client.payload_type != gabriel_pb2.PayloadType.IMAGE:
            return cognitive_engine.wrong_input_format_error(
                from_client.frame_id)

        engine_fields = cognitive_engine.unpack_engine_fields(
            instruction_pb2.EngineFields, from_client)

        img_array = np.asarray(bytearray(from_client.payload), dtype=np.int8)
        img = cv2.imdecode(img_array, -1)

        if max(img.shape) > IMAGE_MAX_WH:
            resize_ratio = float(IMAGE_MAX_WH) / max(img.shape[0], img.shape[1])

            img = cv2.resize(img, (0, 0), fx=resize_ratio, fy=resize_ratio,
                             interpolation=cv2.INTER_AREA)
            objects = self._detect_object(img)
            if objects is not None:
                objects[:, :4] /= resize_ratio
        else:
            objects = self._detect_object(img)

        objects = reorder_objects(objects)

        logger.info("object detection result: %s", objects)
        result_wrapper = instructions.get_instruction(engine_fields, objects)
        result_wrapper.frame_id = from_client.frame_id
        result_wrapper.status = gabriel_pb2.ResultWrapper.Status.SUCCESS

        return result_wrapper
