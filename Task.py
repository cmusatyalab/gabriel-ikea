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

import cv2
import math

import config

OBJECTS = config.LABELS # ["base", "pipe", "shade", "shadetop", "buckle", "blackcircle", "lamp", "bulb", "bulbtop"]
STATES = ["start", "nothing", "base", "pipe", "shade", "buckle", "blackcircle", "shadebase", "bulb", "bulbtop"]
VIDEO_URL_PRE = "http://typhoon.elijah.cs.cmu.edu/ikea/"


class Task:
    def __init__(self):
        # build a mapping between faster-rcnn recognized object order to a standard order
        self.current_state = "start"

        self.one_buckle_frame_counter = 0
        self.two_buckle_frame_counter = 0

    def _check_pipe(self, objects):
        bases = []
        pipes = []
        for i in xrange(objects.shape[0]):
            if int(objects[i, -1] + 0.1) == 0:
                bases.append(objects[i, :])
            if int(objects[i, -1] + 0.1) == 1:
                pipes.append(objects[i, :])

        for base in bases:
            base_center = ((base[0] + base[2]) / 2, (base[1] + base[3]) / 2)
            base_width = base[2] - base[0]
            base_height = base[3] - base[1]
            for pipe in pipes:
                pipe_center = ((pipe[0] + pipe[2]) / 2, (pipe[1] + pipe[3]) / 2)
                pipe_height = pipe[3] - pipe[1]
                if pipe_center[1] > base_center[1]:
                    continue
                if pipe_center[0] < base_center[0] - base_width * 0.25 or pipe_center[0] > base_center[0] + base_width * 0.25:
                    continue
                if pipe_height / base_height < 1.5:
                    continue
                return True
        return False

    def _check_buckle(self, objects):
        shadetops = []
        buckles = []
        for i in xrange(objects.shape[0]):
            if int(objects[i, -1] + 0.1) == 3:
                shadetops.append(objects[i, :])
            if int(objects[i, -1] + 0.1) == 4:
                buckles.append(objects[i, :])

        for shadetop in shadetops:
            shadetop_center = ((shadetop[0] + shadetop[2]) / 2, (shadetop[1] + shadetop[3]) / 2)
            shadetop_width = shadetop[2] - shadetop[0]
            shadetop_height = shadetop[3] - shadetop[1]

            left_buckle = False
            right_buckle = False
            for buckle in buckles:
                buckle_center = ((buckle[0] + buckle[2]) / 2, (buckle[1] + buckle[3]) / 2)
                if buckle_center[1] < shadetop[1] or buckle_center[1] > shadetop[3]:
                    continue
                if buckle_center[0] < shadetop[0] or buckle_center[0] > shadetop[2]:
                    continue
                if buckle_center[0] < shadetop_center[0]:
                    left_buckle = True
                else:
                    right_buckle = True
            if left_buckle and right_buckle:
                break

        return int(left_buckle) + int(right_buckle)

    def _check_bulbtop(self, objects):
        shadetops = []
        bulbtops = []
        for i in xrange(objects.shape[0]):
            if int(objects[i, -1] + 0.1) == 3:
                shadetops.append(objects[i, :])
            if int(objects[i, -1] + 0.1) == 8:
                bulbtops.append(objects[i, :])

        for shadetop in shadetops:
            shadetop_center = ((shadetop[0] + shadetop[2]) / 2, (shadetop[1] + shadetop[3]) / 2)
            shadetop_width = shadetop[2] - shadetop[0]
            shadetop_height = shadetop[3] - shadetop[1]

            for bulbtop in bulbtops:
                bulbtop_center = ((bulbtop[0] + bulbtop[2]) / 2, (bulbtop[1] + bulbtop[3]) / 2)
                if bulbtop_center[1] < shadetop[1] or bulbtop_center[1] > shadetop[3]:
                    continue
                if bulbtop_center[0] < shadetop[0] or bulbtop_center[0] > shadetop[2]:
                    continue
                if bulbtop_center[0] < shadetop_center[0] - shadetop_width * 0.25 or bulbtop_center[0] > shadetop_center[0] + shadetop_width * 0.25:
                    continue
                if bulbtop_center[1] < shadetop_center[1] - shadetop_height * 0.25 or bulbtop_center[1] > shadetop_center[1] + shadetop_height * 0.25:
                    continue
                return True

        return False

    def _get_holo_location(self, objects, label_idx = -1, pos_paras = [10000, 0.5, 0.5]):
        dist_para, x_para, y_para = pos_paras
        objects = objects[objects[:, -1] == label_idx, :]
        x1, y1, x2, y2 = objects[0, :4]
        x = x1 * (1 - x_para) + x2 * x_para
        y = y1 * (1 - y_para) + y2 * y_para
        area = (y2 - y1) * (x2 - x1)
        return {'x': x, 'y': y, 'depth': math.sqrt(dist_para / float(area))}

    def get_instruction(self, objects):
        # @objects format: [x1, y1, x2, y2, confidence, cls_idx]

        result = {'status' : "success"}

        # the start
        if self.current_state == "start":
            result['speech'] = "Put the base on the table."
            image_path = "images_feedback/base.PNG"
            result['image'] = cv2.imread(image_path) if image_path else None
            if config.VIDEO_GUIDANCE:
                result['video'] = VIDEO_URL_PRE + "base.mp4"
            self.current_state = "nothing"
            return result

        if len(objects.shape) < 2: # nothing detected
            return result

        # get the count of detected objects
        object_counts = []
        for i in xrange(len(OBJECTS)):
            object_counts.append(sum(objects[:, -1] == i))

        if self.current_state == "nothing":
            if object_counts[0] > 0 and object_counts[1] > 0:
                if self._check_pipe(objects):
                    result['speech'] = "Good job. Now find the shade cover and expand it"
                    image_path = "images_feedback/shade.PNG"
                    result['image'] = cv2.imread(image_path) if image_path else None
                    result['video'] = VIDEO_URL_PRE + "shade.mp4"
                    self.current_state = "pipe"
            elif object_counts[0] > 0:
                result['speech'] = "Screw the pipe on top of the base"
                image_path = "images_feedback/pipe.PNG"
                result['image'] = cv2.imread(image_path) if image_path else None
                result['video'] = VIDEO_URL_PRE + "pipe.mp4"
                result['holo_object'] = "pipe"
                result['holo_location'] = self._get_holo_location(objects, label_idx = 0, pos_paras = config.holo_pos_paras['pipe'])
                self.current_state = "base"

        elif self.current_state == "base":
            if object_counts[0] > 0 and object_counts[1] > 0:
                if self._check_pipe(objects):
                    result['speech'] = "Good job. Now find the shade cover and expand it"
                    image_path = "images_feedback/shade.PNG"
                    result['image'] = cv2.imread(image_path) if image_path else None
                    result['video'] = VIDEO_URL_PRE + "shade.mp4"
                    self.current_state = "pipe"
            elif object_counts[0] > 0:
                result['holo_object'] = "pipe"
                result['holo_location'] = self._get_holo_location(objects, label_idx = 0, pos_paras = config.holo_pos_paras['pipe'])

        elif self.current_state == "pipe":
            if object_counts[2] > 0:
                result['speech'] = "Put the iron wires to support the shade. And show the top view of the shade"
                image_path = "images_feedback/buckle.PNG"
                result['image'] = cv2.imread(image_path) if image_path else None
                result['video'] = VIDEO_URL_PRE + "buckle.mp4"
                self.current_state = "shade"

        elif self.current_state == "shade":
            if object_counts[3] > 0 and object_counts[4] > 0:
                n_buckles = self._check_buckle(objects)
                if n_buckles == 2:
                    self.one_buckle_frame_counter = 0
                    self.two_buckle_frame_counter += 1
                    if self.two_buckle_frame_counter > 3:
                        result['speech'] = "Great. Now unscrew the black ring out of the pipe. And put it on the table"
                        image_path = "images_feedback/blackcircle.PNG"
                        result['image'] = cv2.imread(image_path) if image_path else None
                        result['video'] = VIDEO_URL_PRE + "blackcircle.mp4"
                        self.current_state = "buckle"
                if n_buckles == 1:
                    self.one_buckle_frame_counter += 1
                    self.two_buckle_frame_counter = 0
                    if self.one_buckle_frame_counter in [5, 500]:
                        result['speech'] = "You have attached one wire. Now find another one to support the shade"

        elif self.current_state == "buckle":
            if object_counts[5] > 0:
                result['speech'] = "Now put the shade on top of the base. And screw the black ring back"
                image_path = "images_feedback/lamp.PNG"
                result['image'] = cv2.imread(image_path) if image_path else None
                result['video'] = VIDEO_URL_PRE + "lamp.mp4"
                self.current_state = "blackcircle"

        elif self.current_state == "blackcircle":
            if object_counts[6] > 0:
                result['speech'] = "Find the bulb and put it on the table"
                image_path = "images_feedback/bulb.PNG"
                result['image'] = cv2.imread(image_path) if image_path else None
                result['video'] = VIDEO_URL_PRE + "bulb.mp4"
                self.current_state = "shadebase"

        elif self.current_state == "shadebase":
            if object_counts[7] > 0:
                result['speech'] = "Good. Last step. Screw the bulb and show me the top view"
                image_path = "images_feedback/lamptop.PNG"
                result['image'] = cv2.imread(image_path) if image_path else None
                result['video'] = VIDEO_URL_PRE + "lamptop.mp4"
                self.current_state = "bulb"

        elif self.current_state == "bulb":
            if object_counts[3] > 0 and object_counts[8] > 0:
                if self._check_bulbtop(objects):
                    result['speech'] = "Congratulations. You have finished assembling the lamp."
                    image_path = "images_feedback/lamp.PNG"
                    result['image'] = cv2.imread(image_path) if image_path else None
                    self.current_state = "bulbtop"

        if not config.VIDEO_GUIDANCE:
            if 'video' in result:
                del result['video']

        return result
