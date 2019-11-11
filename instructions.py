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

import instruction_pb2
import time
from gabriel_protocol import gabriel_pb2


ENGINE_NAME = "instruction"

# The objects(states) which can be detected
LABELS = ["base", "pipe", "shade", "shadetop", "buckle", "blackcircle", "lamp",
          "bulb", "bulbtop"]


def _count_buckles(objects):
    shadetops = []
    buckles = []
    for i in xrange(objects.shape[0]):
        if int(objects[i, -1] + 0.1) == 3:
            shadetops.append(objects[i, :])
        if int(objects[i, -1] + 0.1) == 4:
            buckles.append(objects[i, :])

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


def _result_with_update(image_path, instruction, engine_fields):
    engine_fields.update_count += 1
    result_wrapper = _result_without_update(engine_fields)

    result = gabriel_pb2.ResultWrapper.Result()
    result.payload_type = gabriel_pb2.PayloadType.IMAGE
    result.engine_name = ENGINE_NAME
    with open(image_path, 'rb') as f:
        result.payload = f.read()
    result_wrapper.results.append(result)

    result = gabriel_pb2.ResultWrapper.Result()
    result.payload_type = gabriel_pb2.PayloadType.TEXT
    result.engine_name = ENGINE_NAME
    result.payload = instruction.encode(encoding="utf-8")
    result_wrapper.results.append(result)

    return result_wrapper


def _result_without_update(engine_fields):
    result_wrapper = gabriel_pb2.ResultWrapper()
    result_wrapper.engine_fields.Pack(engine_fields)
    return result_wrapper


def _start_result(engine_fields):
    engine_fields.ikea.state = instruction_pb2.Ikea.State.NOTHING
    engine_fields.update_count += 1
    return _result_with_update(
        "images_feedback/base.PNG", "Put the base on the table.", engine_fields)


def _nothing_result(objects, object_counts, engine_fields):
    if object_counts[0] == 0:
        return _result_without_update(engine_fields)

    if object_counts[1] == 0:
        engine_fields.ikea.state = instruction_pb2.Ikea.State.BASE
        return _result_with_update(
                "images_feedback/pipe.PNG", "Screw the pipe on top of the "
                "base.", engine_fields)

    return _result_without_update(engine_fields)


def _base_result(objects, object_counts, engine_fields):
    if object_counts[0] == 0 or object_counts[1] == 0:
        return _result_without_update(engine_fields)

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
            if pipe_center[0] < base_center[0] - base_width * 0.25 or (
                    pipe_center[0] > base_center[0] + base_width * 0.25):
                continue
            if pipe_height / base_height < 1.5:
                continue
            engine_fields.ikea.state = instruction_pb2.Ikea.State.PIPE
            return _result_with_update(
                "images_feedback/shade.PNG", "Good job. Now find the shade "
                "cover and expand it.", engine_fields)

    return _result_without_update(engine_fields)


def _pipe_result(objects, object_counts, engine_fields):
    if object_counts[2] > 0:
        engine_fields.ikea.state = instruction_pb2.Ikea.State.SHADE
        return _result_with_update(
            "images_feedback/buckle.PNG", "Insert the iron wires to support "
            "the shade. Then show the top view of the shade.", engine_fields)

    return _result_without_update(engine_fields)


def _shade_result(objects, object_counts, engine_fields):
    if object_counts[3] == 0 or object_counts[4] == 0:
        return _result_without_update(engine_fields)

    update = False
    n_buckles = self._count_buckles(objects)
    if n_buckles == 2:
        engine_fields.ikea.frames_with_one_buckle = 0
        engine_fields.ikea.frames_with_two_buckles += 1
        update = True

        if engine_fields.ikea.frames_with_two_buckles > 3:
            engine_fields.ikea.state = instruction_pb2.Ikea.State.BUCKLE
            return _result_with_update(
                "images_feedback/blackcircle.PNG", "Great. Now unscrew the "
                "black ring out of the pipe, and put it on the table.",
                engine_fields)
    if n_buckles == 1:
        engine_fields.ikea.frames_with_one_buckle += 1
        engine_fields.ikea.frames_with_two_buckles = 0
        update = True

        if engine_fields.ikea.frames_with_one_buckle > 4:
            return _result_with_update(
                "images_feedback/buckle.PNG", "You have inserted one wire. "
                "Now insert the second wire to support the shade.",
                engine_fields)

    if update:
        engine_fields.update_count += 1
    return _result_without_update(engine_fields)


def _buckle_result(objects, object_counts, engine_fields):
    if object_counts[5] > 0:
        engine_fields.ikea.state = instruction_pb2.Ikea.State.BLACK_CIRCLE
        return _result_with_update(
            "images_feedback/lamp.PNG", "Now put the shade on top of the base, "
            "and screw the black ring back.", engine_fields)

    return _result_without_update(engine_fields)


def _black_circle_result(objects, object_counts, engine_fields):
    if object_counts[6] > 0:
        engine_fields.ikea.state = instruction_pb2.Ikea.State.SHADE_BASE
        return _result_with_update(
            "images_feedback/bulb.PNG", "Find the bulb and put it on the "
            "table.", engine_fields)

    return _result_without_update(engine_fields)


def _shade_base_result(objects, object_counts, engine_fields):
    if object_counts[7] > 0:
        engine_fields.ikea.state = instruction_pb2.Ikea.State.BULB
        return _result_with_update(
            "images_feedback/lamptop.PNG", "Good. Last step. Screw in the bulb "
            "and show me the top view.", engine_fields)

    return _result_without_update(engine_fields)

def _bulb_result(objects, object_counts, engine_fields):
    if object_counts[3] == 0 or object_counts[8] == 0:
        return _result_without_update(engine_fields)

    shadetops = []
    bulbtops = []
    for i in xrange(objects.shape[0]):
        if int(objects[i, -1] + 0.1) == 3:
            shadetops.append(objects[i, :])
        if int(objects[i, -1] + 0.1) == 8:
            bulbtops.append(objects[i, :])

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
            return _result_with_update(
                "images_feedback/lamp.PNG", "Congratulations. You have "
                "finished assembling the lamp.", engine_fields)

    return _result_without_update(engine_fields)


def get_instruction(engine_fields, objects):
    state = engine_fields.ikea.state

    if state == instruction_pb2.Ikea.State.START:
        return _start_result(engine_fields)

    if len(objects.shape) < 2:
        return _result_without_update(engine_fields)

    # get the count of detected objects
    object_counts = [sum(objects[:, -1] == i) for i in range(len(LABELS))]

    if state == instruction_pb2.Ikea.State.NOTHING:
        return _nothing_result(objects, object_counts, engine_fields)
    elif state == instruction_pb2.Ikea.State.BASE:
        return _base_result(objects, object_counts, engine_fields)
    elif state == instruction_pb2.Ikea.State.PIPE:
        return _pipe_result(objects, object_counts, engine_fields)
    elif state == instruction_pb2.Ikea.State.SHADE:
        return _shade_result(objects, object_counts, engine_fields)
    elif state == instruction_pb2.Ikea.State.BUCKLE:
        return _buckle_result(objects, object_counts, engine_fields)
    elif state == instruction_pb2.Ikea.State.BLACK_CIRCLE:
        return _black_circle_result(objects, object_counts, engine_fields)
    elif state == instruction_pb2.Ikea.State.SHADE_BASE:
        return _shade_base_result(objects, object_counts, engine_fields)
    elif state == instruction_pb2.Ikea.State.BULB:
        return _bulb_result(objects, object_counts, engine_fields)
