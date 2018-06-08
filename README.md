# Overview [![Docker Image Status][docker-image]][docker] [![License][license-image]][license]

A cognitive assistant to aid in the assembly of an Ikea lamp. Click below for the demo video.

[![Demo Video](https://img.youtube.com/vi/qDPuvBWNIUs/0.jpg)](https://www.youtube.com/watch?v=qDPuvBWNIUs)

[docker-image]: https://img.shields.io/docker/build/cmusatyalab/gabriel-ikea.svg
[docker]: https://hub.docker.com/r/cmusatyalab/gabriel-ikea

[license-image]: http://img.shields.io/badge/license-Apache--2-blue.svg?style=flat
[license]: LICENSE

# Installation
Running the application using Docker is advised. If you want to install from source, please see [Dockerfile](Dockerfile) for details.

# How to Run
## Client
Run Gabriel's [legacy Android Client](https://github.com/cmusatyalab/gabriel/tree/master/client/legacy-android-client). You'll need Android Studio to compile and install the apk.
Make sure to change IP address of GABRIEL_IP variable at src/edu/cmu/cs/gabriel/Const.java to point to your server.

## Server
### Container
```bash
nvidia-docker run --rm -it --name ikea \
-p 0.0.0.0:9098:9098 -p 0.0.0.0:9111:9111 -p 0.0.0.0:22222:22222 \
-p 0.0.0.0:8080:8080 \
cmusatyalab/gabriel-ikea:latest
```

# Test the trained DNN Object Detector Only
Please see [img.py](img.py). The model can be downloaded from [here](https://owncloud.cmusatyalab.org/owncloud/index.php/s/00HicjwH27mZpv8/download).
