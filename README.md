# Overview [![Docker Image Status][docker-image]][docker] [![License][license-image]][license]

A cognitive assistant to aid in the assembly of an Ikea lamp. Click below for the demo video.

[![Demo Video](https://img.youtube.com/vi/qDPuvBWNIUs/0.jpg)](https://www.youtube.com/watch?v=qDPuvBWNIUs)

[docker-image]: https://img.shields.io/docker/build/cmusatyalab/gabriel-ikea.svg
[docker]: https://hub.docker.com/r/cmusatyalab/gabriel-ikea

[license-image]: http://img.shields.io/badge/license-Apache--2-blue.svg?style=flat
[license]: LICENSE

# Installation
## Client
An Android client is available on [Google Play](https://play.google.com/store/apps/details?id=edu.cmu.cs.gabrielclient). The source code is available [here](https://github.com/cmusatyalab/gabriel/tree/new-gabriel/android-client).

## Server
Running the server application using Docker is advised. If you want to install from source, please see [Dockerfile](Dockerfile) for details.


# How to Run
## Client
From the main activity one can add servers by name and IP/domain. Subtitles for audio feedback can also been toggled. This option is useful for devices that may not have integrated speakers(like ODG R-7).
Pressing the 'Play' button next to a server will initiate a connection to the Gabriel server at that address.

## Server
### Container
```bash
docker run --rm -it --gpus all -p 9099:9099 cmusatyalab/gabriel-ikea:latest
```

# Run the trained DNN Object Detector Only
Please see [test.py](test.py). The model can be downloaded from [here](https://owncloud.cmusatyalab.org/owncloud/index.php/s/00HicjwH27mZpv8/download).
