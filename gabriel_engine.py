import numpy as np
import logging
from gabriel_server import cognitive_engine
from gabriel_protocol import gabriel_pb2
import ikea_pb2
import ikea_cv
import instructions


# Max image width and height
IMAGE_MAX_WH = 640


logger = logging.getLogger(__name__)


def reorder_objects(result):
    # build a mapping between faster-rcnn recognized object order to a
    # standard order
    object_mapping = [-1] * len(instructions.LABELS)
    with open("labels.txt") as f:
        lines = f.readlines()
        for idx, line in enumerate(lines):
            line = line.strip()
            object_mapping[idx] = instructions.LABELS.index(line)

    for i in xrange(result.shape[0]):
        result[i, -1] = object_mapping[int(result[i, -1] + 0.1)]

    return result


class IkeaEngine(cognitive_engine.Engine):
    ENGINE_NAME = "ikea"

    def handle(self, from_client):
        if from_client.payload_type != gabriel_pb2.PayloadType.IMAGE:
            return cognitive_engine.wrong_input_format_error(
                from_client.frame_id)

        engine_fields = cognitive_engine.unpack_engine_fields(
            ikea_pb2.EngineFields, from_client)

        img_array = np.asarray(bytearray(raw_data), dtype=np.int8)
        img = cv2.imdecode(img_array, -1)

        if max(img.shape) > IMAGE_MAX_WH:
            resize_ratio = float(IMAGE_MAX_WH) / max(img.shape[0], img.shape[1])
            img = cv2.resize(img, (0, 0), fx=resize_ratio, fy=resize_ratio,
                             interpolation=cv2.INTER_AREA)
        else:
            resize_ratio = 1

        rtn_msg, state = ikea_cv.process(img, resize_ratio, display_list)

        objects = np.array(json.loads(objects_data))
        objects = reorder_objects(objects)

        logger.info("object detection result: %s", objects)
        instruction = _get_instruction(objects, engine_fields.state)
