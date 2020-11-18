#
# Instructions for Ikea task
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

import os
import instruction_pb2
from gabriel_protocol import gabriel_pb2


ENGINE_NAME = "instruction"


# Class indexes come from the following code:
# LABELS = ["base", "pipe", "shade", "shadetop", "buckle", "blackcircle",
#           "lamp", "bulb", "bulbtop"]
# with open(os.path.join('model', 'labels.txt')) as f:
#     idx = 1
#     for line in f:
#         line = line.strip()
#         print(line.upper(), '=', idx)
#         idx += 1
SHADETOP = 1
BULBTOP = 2
BUCKLE = 3
LAMP = 4
PIPE = 5
BLACKCIRCLE = 6
BASE = 7
SHADE = 8
BULB = 9

# The DNN will output the following classes
DONE = 10

IMAGE_FILENAMES = {
    BASE: 'base.PNG',
    PIPE: 'pipe.PNG',
    SHADE: 'shade.PNG',
    SHADETOP: 'buckle.PNG',
    BUCKLE: 'buckle.PNG',
    BLACKCIRCLE: 'blackcircle.PNG',
    LAMP: 'lamp.PNG',
    BULB: 'bulb.PNG',
    BULBTOP: 'lamptop.PNG',
    DONE: 'lamp.PNG',
}

INSTRUCTIONS = {
    BASE: 'Put the base on the table.',
    PIPE: 'Screw the pipe on top of the base.',
    SHADE: 'Good job. Now find the shade cover and expand it.',
    SHADETOP: 'Insert the iron wires to support the shade. Then show the top '
            'view of the shade',
    BUCKLE: 'You have inserted one wire. Now insert the second wire to '
              'support the shade.',
    BLACKCIRCLE: 'Great. Now unscrew the black ring out of the pipe, and put '
                 'it on the table.',
    LAMP: 'Now put the shade on top of the base, and screw the black ring'
          ' back.',
    BULB: 'Find the bulb and put it on the table.',
    BULBTOP: 'Good. Last step. Screw in the bulb and show me the top view.',
    DONE: 'Congratulations. You have finished assembling the lamp.',
}

IMAGES = {
    cls_idx: open(os.path.join('images_feedback', filename), 'rb').read()
    for cls_idx, filename in IMAGE_FILENAMES.items()
}


def _result_without_update(engine_fields):
    result_wrapper = gabriel_pb2.ResultWrapper()
    result_wrapper.engine_fields.Pack(engine_fields)
    return result_wrapper


def _result_with_update(cls_idx, engine_fields):
    engine_fields.update_count += 1
    result_wrapper = _result_without_update(engine_fields)

    result = gabriel_pb2.ResultWrapper.Result()
    result.payload_type = gabriel_pb2.PayloadType.IMAGE
    result.engine_name = ENGINE_NAME
    result.payload = IMAGES[cls_idx]
    result_wrapper.results.append(result)

    result = gabriel_pb2.ResultWrapper.Result()
    result.payload_type = gabriel_pb2.PayloadType.TEXT
    result.engine_name = ENGINE_NAME
    result.payload = INSTRUCTIONS[cls_idx].encode(encoding="utf-8")
    result_wrapper.results.append(result)

    return result_wrapper


def _start_result(engine_fields):
    engine_fields.ikea.state = instruction_pb2.Ikea.State.NOTHING
    return _result_with_update(BASE, engine_fields)


def _nothing_result(dets_for_class, engine_fields):
    if len(dets_for_class[BASE]) == 0:
        return _result_without_update(engine_fields)

    engine_fields.ikea.state = instruction_pb2.Ikea.State.BASE
    return _result_with_update(PIPE, engine_fields)


def _base_result(dets_for_class, engine_fields):
    bases = dets_for_class[BASE]
    pipes = dets_for_class[PIPE]
    if (len(bases) == 0) or (len(pipes) == 0):
        return _result_without_update(engine_fields)

    for base in bases:
        base_center = ((base[0] + base[2]) / 2, (base[1] + base[3]) / 2)
        base_width = base[2] - base[0]
        base_height = base[3] - base[1]
        for pipe in pipes:
            pipe_center = ((pipe[0] + pipe[2]) / 2, (pipe[1] + pipe[3]) / 2)
            pipe_height = pipe[3] - pipe[1]
            if pipe_center[1] > base_center[1]:
                continue
            if pipe_center[0] < base_center[0] - base_width * 0.25 or (
                    pipe_center[0] > base_center[0] + base_width * 0.25):
                continue
            if pipe_height / base_height < 1.5:
                continue
            engine_fields.ikea.state = instruction_pb2.Ikea.State.PIPE
            return _result_with_update(SHADE, engine_fields)

    return _result_without_update(engine_fields)


def _pipe_result(dets_for_class, engine_fields):
    if len(dets_for_class[SHADE]) > 0:
        engine_fields.ikea.state = instruction_pb2.Ikea.State.SHADE
        return _result_with_update(SHADETOP, engine_fields)

    return _result_without_update(engine_fields)


def _count_buckles(shadetops, buckles):
    for shadetop in shadetops:
        shadetop_center = ((shadetop[0] + shadetop[2]) / 2,
                           (shadetop[1] + shadetop[3]) / 2)
        shadetop_width = shadetop[2] - shadetop[0]
        shadetop_height = shadetop[3] - shadetop[1]

        left_buckle = False
        right_buckle = False
        for buckle in buckles:
            buckle_center = ((buckle[0] + buckle[2]) / 2,
                             (buckle[1] + buckle[3]) / 2)
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


def _shade_result(dets_for_class, engine_fields):
    shadetops = dets_for_class[SHADETOP]
    buckles = dets_for_class[BUCKLE]
    if (len(shadetops) == 0) or (len(buckles) == 0):
        return _result_without_update(engine_fields)

    update = False
    n_buckles = _count_buckles(shadetops, buckles)
    if n_buckles == 2:
        engine_fields.ikea.frames_with_one_buckle = 0
        engine_fields.ikea.frames_with_two_buckles += 1
        update = True

        if engine_fields.ikea.frames_with_two_buckles > 3:
            engine_fields.ikea.state = instruction_pb2.Ikea.State.BUCKLE
            return _result_with_update(BLACKCIRCLE, engine_fields)
    if n_buckles == 1:
        engine_fields.ikea.frames_with_one_buckle += 1
        engine_fields.ikea.frames_with_two_buckles = 0
        update = True

        # We only give this instruction when frames_with_one_buckle is
        # exactly 5 so it does not get repeated
        if engine_fields.ikea.frames_with_one_buckle == 5:
            return _result_with_update(BUCKLE, engine_fields)

    if update:
        engine_fields.update_count += 1
    return _result_without_update(engine_fields)


def _buckle_result(dets_for_class, engine_fields):
    if len(dets_for_class[BLACKCIRCLE]) > 0:
        engine_fields.ikea.state = instruction_pb2.Ikea.State.BLACK_CIRCLE
        return _result_with_update(LAMP, engine_fields)

    return _result_without_update(engine_fields)


def _black_circle_result(dets_for_class, engine_fields):
    if len(dets_for_class[LAMP]) > 0:
        engine_fields.ikea.state = instruction_pb2.Ikea.State.SHADE_BASE
        return _result_with_update(BULB, engine_fields)

    return _result_without_update(engine_fields)


def _shade_base_result(dets_for_class, engine_fields):
    if len(dets_for_class[BULB]) > 0:
        engine_fields.ikea.state = instruction_pb2.Ikea.State.BULB
        return _result_with_update(BULBTOP, engine_fields)

    return _result_without_update(engine_fields)

def _bulb_result(dets_for_class, engine_fields):
    shadetops = dets_for_class[SHADETOP]
    bulbtops = dets_for_class[BULBTOP]
    if (len(shadetops) == 0) or (len(bulbtops) == 0):
        return _result_without_update(engine_fields)

    for shadetop in shadetops:
        shadetop_center = ((shadetop[0] + shadetop[2]) / 2,
                           (shadetop[1] + shadetop[3]) / 2)
        shadetop_width = shadetop[2] - shadetop[0]
        shadetop_height = shadetop[3] - shadetop[1]

        for bulbtop in bulbtops:
            bulbtop_center = ((bulbtop[0] + bulbtop[2]) / 2,
                              (bulbtop[1] + bulbtop[3]) / 2)
            if bulbtop_center[1] < shadetop[1] or (
                    bulbtop_center[1] > shadetop[3]):
                continue
            if bulbtop_center[0] < shadetop[0] or (
                    bulbtop_center[0] > shadetop[2]):
                continue
            if (bulbtop_center[0] < shadetop_center[0] -
                shadetop_width * 0.25) or (
                    bulbtop_center[0] > shadetop_center[0] +
                    shadetop_width * 0.25):
                continue
            if (bulbtop_center[1] < shadetop_center[1] - shadetop_height *
                0.25) or (bulbtop_center[1] > shadetop_center[1] +
                          shadetop_height * 0.25):
                continue

            engine_fields.ikea.state = instruction_pb2.Ikea.State.BULB_TOP
            return _result_with_update(DONE, engine_fields)

    return _result_without_update(engine_fields)


def get_instruction(engine_fields, dets_for_class):
    state = engine_fields.ikea.state

    if state == instruction_pb2.Ikea.State.START:
        return _start_result(engine_fields)

    if state == instruction_pb2.Ikea.State.NOTHING:
        return _nothing_result(dets_for_class, engine_fields)
    elif state == instruction_pb2.Ikea.State.BASE:
        return _base_result(dets_for_class, engine_fields)
    elif state == instruction_pb2.Ikea.State.PIPE:
        return _pipe_result(dets_for_class, engine_fields)
    elif state == instruction_pb2.Ikea.State.SHADE:
        return _shade_result(dets_for_class, engine_fields)
    elif state == instruction_pb2.Ikea.State.BUCKLE:
        return _buckle_result(dets_for_class, engine_fields)
    elif state == instruction_pb2.Ikea.State.BLACK_CIRCLE:
        return _black_circle_result(dets_for_class, engine_fields)
    elif state == instruction_pb2.Ikea.State.SHADE_BASE:
        return _shade_base_result(dets_for_class, engine_fields)
    elif state == instruction_pb2.Ikea.State.BULB:
        return _bulb_result(dets_for_class, engine_fields)
    elif state == instruction_pb2.Ikea.State.BULB_TOP:
        return _result_without_update(engine_fields)

    raise Exception("Invalid state")
