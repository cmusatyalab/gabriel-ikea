import json
import multiprocessing
import os
import Queue
import select
import socket
import struct
import sys
import threading
import time
import webbrowser

if os.path.isdir("../../gabriel/server"):
    sys.path.insert(0, "../../gabriel/server")
import gabriel
LOG = gabriel.logging.getLogger(__name__)


class VideoHandler(gabriel.network.CommonHandler):
    def setup(self):
        super(VideoHandler, self).setup()

    def __repr__(self):
        return "Video Server"

    def handle(self):
        LOG.info("New Ikea app connected")
        super(VideoHandler, self).handle()

    def _handle_input_data(self):
        ## receive data
        data_size = struct.unpack("!I", self._recv_all(4))[0]
        data = self._recv_all(data_size)
        webbrowser.open(data)

    def terminate(self):
        LOG.info("Pingpong app disconnected")
        super(VideoHandler, self).terminate()

class VideoServer(gabriel.network.CommonServer):
    def __init__(self, port, handler):
        gabriel.network.CommonServer.__init__(self, port, handler) # cannot use super because it's old style class
        LOG.info("* Video server(%s) configuration" % str(self.handler))
        LOG.info(" - Open TCP Server at %s" % (str(self.server_address)))
        LOG.info(" - Disable nagle (No TCP delay)  : %s" %
                str(self.socket.getsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY)))
        LOG.info("-" * 50)

    def terminate(self):
        gabriel.network.CommonServer.terminate(self)

def main():
    video_server = VideoServer(5699, VideoHandler)
    video_thread = threading.Thread(target = video_server.serve_forever)
    video_thread.daemon = True

    try:
        video_thread.start()
        while True:
            time.sleep(100)
    except KeyboardInterrupt as e:
        sys.stdout.write("Exit by user\n")
        video_server.terminate()
        sys.exit(1)
    except Exception as e:
        sys.stderr.write(str(e))
        video_server.terminate()
        sys.exit(1)
    else:
        video_server.terminate()
        sys.exit(0)


if __name__ == '__main__':
    main()
