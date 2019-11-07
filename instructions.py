import ikea_pb2


# The objects(states) which can be detected
LABELS = ["base", "pipe", "shade", "shadetop", "buckle", "blackcircle", "lamp",
          "bulb", "bulbtop"]


def _check_pipe(objects):
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
            return True
    return False


def _check_buckle(objects):
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


def _check_bulbtop(objects):
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
            return True

    return False


def start_result():



def get_instruction(state, objects):
    if state == ikea_pb2.EngineFields.State.START:
        return _start_result()

    if len(objects.shape) < 2:
        return _nothing_detected(state)

    # get the count of detected objects
    object_counts = [sum(objects[:, -1] == i) for i in range(len(LABELS))]

    if state == ikea_pb2.EngineFields.State.NOTHING:
        return _nothing_result(objects, object_counts)
    elif state == ikea_pb2.EngineFields.State.BASE:
        return _base_result(objects, object_counts)
    elif state == ikea_pb2.EngineFields.State.PIPE:
        return _pipe_result(objects, object_counts)
    elif state == ikea_pb2.EngineFields.State.SHADE:
        return _shade_result(objects, object_counts)
    elif state == ikea_pb2.EngineFields.State.BUCKLE:
        return _buckle_result(objects, object_counts)
    elif state == ikea_pb2.EngineFields.State.BLACK_CIRCLE:
        return _black_circle_result(objects, object_counts)
    elif state == ikea_pb2.EngineFields.State.SHADE_BASE:
        return _shade_base_result(objects, object_counts)
    elif state == ikea_pb2.EngineFields.State.BULB:
        return _bulb_result(objects, object_counts)
