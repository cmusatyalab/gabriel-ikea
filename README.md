# Overview [![Docker Image Status][docker-image]][docker] [![License][license-image]][license]

A cognitive assistant to help assemble an Ikea lamp. Watch a demo video
[here](https://www.youtube.com/watch?v=qDPuvBWNIUs). This assistant requires
[this](https://www.amazon.com/Ikea-502-422-47-Magnarp-Table-Natural/dp/B00R3LSFII)
lamp. If you don't have this lamp, you can test the assistant using
[these](https://docs.google.com/document/d/1iJXZDOzd6BLsI_0_IQXCHqgezkNBmTOY_2WlOos0L7o)
images.

[docker-image]: https://img.shields.io/docker/build/cmusatyalab/gabriel-ikea.svg
[docker]: https://hub.docker.com/r/cmusatyalab/gabriel-ikea

[license-image]: http://img.shields.io/badge/license-Apache--2-blue.svg?style=flat
[license]: LICENSE

# Installation

## Client

An Android client is available on
[Google Play](https://play.google.com/store/apps/details?id=edu.cmu.cs.gabrielclient).
The source code is available
[here](https://github.com/cmusatyalab/gabriel-instruction/tree/master/android).

## Server

We recommend running the server using Docker. If you want to run the code
directly, please see our [Dockerfile](Dockerfile) for details.

# How to Run

## Client

Add servers by name and IP/domain from the main activity. This activity also
contains a toggle to show subtitles with instructions. Subtitles are useful for
devices that may not have integrated speakers (such as the ODG R-7). Connect to
a server by pressing the button to the left of its name.

## Server

### Container

```bash
docker run --rm -it --gpus all -p 9099:9099 cmusatyalab/gabriel-ikea:latest
```

# Standalone Object Detector

You can run the object detector by itself using [test.py](test.py). The model
can be downloaded from
[here](https://owncloud.cmusatyalab.org/owncloud/index.php/s/00HicjwH27mZpv8/download).
