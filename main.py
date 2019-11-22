#!/usr/bin/env python3
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

from gabriel_server.local_engine import runner
from ikea_engine import IkeaEngine
from instructions import ENGINE_NAME
import logging
import argparse

DEFAULT_PORT = 9099
DEFAULT_NUM_TOKENS = 2
INPUT_QUEUE_MAX_SIZE = 60

logging.basicConfig(level=logging.INFO)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-t", "--tokens", type=int, default=DEFAULT_NUM_TOKENS,
        help="number of tokens")
    parser.add_argument(
        "-c",
        "--cpu-only",
        action="store_true",
        help="Pass this flag to prevent the GPU from being used.")
    parser.add_argument(
        "-p", "--port", type=int, default=DEFAULT_PORT, help="Set port number")
    args = parser.parse_args()

    def engine_setup():
        return IkeaEngine(args.cpu_only)

    runner.run(
        engine_setup, ENGINE_NAME, INPUT_QUEUE_MAX_SIZE, args.port, args.tokens)


if __name__ == "__main__":
    main()
