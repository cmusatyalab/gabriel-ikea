#!/usr/bin/env python
#
# Cloudlet Infrastructure for Mobile Computing
#   - Task Assistance
#
#   Author: Zhuo Chen <zhuoc@cs.cmu.edu>
#
#   Copyright (C) 2011-2013 Carnegie Mellon University
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
# This script is used for testing computer vision algorithms in the
# Lego Task Assistance project. It does processing for one image.
# Usage: python img.py <image-path>
#

'''
This script loads a single image from file, and try to generate relevant information of Ikea Assistant.
It is primarily used as a quick test tool for the computer vision algorithm.
'''

import argparse
import cv2
import json
import numpy as np
import socket
import struct
import sys
import time

sys.path.insert(0, "..")
import config
import zhuocv as zc

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file",
                        help = "The image to process",
                       )
    args = parser.parse_args()
    return (args.input_file)

def _recv_all(socket, recv_size):
    data = ''
    while len(data) < recv_size:
        tmp_data = socket.recv(recv_size - len(data))
        if tmp_data == None or len(tmp_data) == 0:
            raise Exception("Socket is closed")
        data += tmp_data
    return data

def reorder_result(result):
    # build a mapping between faster-rcnn recognized object order to a standard order
    object_mapping = [-1] * len(config.LABELS)
    with open("model/labels.txt") as f:
        lines = f.readlines()
        for idx, line in enumerate(lines):
            line = line.strip()
            object_mapping[idx] = config.LABELS.index(line)

    for i in xrange(result.shape[0]):
        result[i, -1] = object_mapping[int(result[i, -1] + 0.1)]

    return result

# set configs...
config.setup(is_streaming = False)
display_list = config.DISPLAY_LIST

# load test image
input_file = parse_arguments()
img = cv2.imread(input_file)
if max(img.shape) > config.IMAGE_MAX_WH:
    resize_ratio = float(config.IMAGE_MAX_WH) / max(img.shape[0], img.shape[1])
    img = cv2.resize(img, (0, 0), fx = resize_ratio, fy = resize_ratio, interpolation = cv2.INTER_AREA)

zc.check_and_display("input", img, display_list, resize_max = config.DISPLAY_MAX_PIXEL, wait_time = config.DISPLAY_WAIT_TIME)

# process image and get the symbolic representation
# GPU machine offloaded part
task_server_ip = config.TASK_SERVER_IP
task_server_port = config.TASK_SERVER_PORT
task_server_addr = (task_server_ip, task_server_port)
try:
    task_server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    task_server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    task_server_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    task_server_sock.connect(task_server_addr)
    print "connected to task server"
except socket.error as e:
    print "Failed to connect to task server at %s" % str(task_server_addr)

data = zc.cv_image2raw(img)
packet = struct.pack("!I%ds" % len(data), len(data), data)
task_server_sock.sendall(packet)
result_size = struct.unpack("!I", _recv_all(task_server_sock, 4))[0]
result = _recv_all(task_server_sock, result_size)

result = np.array(json.loads(result))
result = reorder_result(result)
img_object = zc.vis_detections(img, result, config.LABELS)
zc.check_and_display("object", img_object, display_list, resize_max = config.DISPLAY_MAX_PIXEL, wait_time = config.DISPLAY_WAIT_TIME)

task_server_sock.close()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt as e:
    sys.stdout.write("user exits\n")
