FROM nvidia/cuda:10.1-cudnn7-devel-ubuntu18.04
MAINTAINER Satyalab, satya-group@lists.andrew.cmu.edu

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y \
    --no-install-recommends \
    apt-utils

RUN apt-get install -y \
    build-essential \
    libopencv-dev \
    python3 \
    python3-dev \
    python3-pip \
    libprotobuf-dev \
    libleveldb-dev \
    libsnappy-dev \
    libhdf5-serial-dev \
    libatlas-base-dev \
    protobuf-compiler \
    libboost-all-dev \
    libgflags-dev \
    libgoogle-glog-dev \
    liblmdb-dev

# fix bug for hdf5 for Caffe. See https://github.com/NVIDIA/DIGITS/issues/156
RUN cd /usr/lib/x86_64-linux-gnu && ln -s libhdf5_serial.so libhdf5.so && \
    ln -s libhdf5_serial_hl.so libhdf5_hl.so

RUN python3 -m pip install --upgrade pip

COPY . /gabriel-ikea

WORKDIR /gabriel-ikea
RUN python3 -m pip install -r requirements.txt

ENV FASTER_RCNN_ROOT /gabriel-ikea/py-faster-rcnn

# install python dependencies
WORKDIR /gabriel-ikea/py-faster-rcnn/caffe-fast-rcnn/python
RUN python3 -m pip install -r requirements.txt

# compile py-faster-rcnn
WORKDIR /gabriel-ikea/py-faster-rcnn
RUN cd lib && \
    make -j$(nproc)
RUN cd caffe-fast-rcnn && \
    make -j$(nproc) && \
    make -j$(nproc) pycaffe

# download/extract model for ikea
WORKDIR /gabriel-ikea/model
RUN wget https://owncloud.cmusatyalab.org/owncloud/index.php/s/00HicjwH27mZpv8/download -O ikea_model.tar.gz
RUN tar -xvzf ikea_model.tar.gz

EXPOSE 9099
ENTRYPOINT ["./main.py"]
