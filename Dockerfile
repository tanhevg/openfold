# Make sure CUDA versions in the two lines below are in sync.
# Available cuda image versions can be checked on https://hub.docker.com/r/nvidia/cuda
# Also check CUDA versions that are supported by Pytorch - not all of them are
FROM nvidia/cuda:11.3.1-cudnn8-runtime-ubuntu18.04
ARG CUDA=11.3

# Use bash to support string substitution.
SHELL ["/bin/bash", "-c"]

RUN apt-key del 7fa2af80
RUN apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64/7fa2af80.pub
RUN apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64/3bf863cc.pub

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    build-essential \
    libxml2 \
    cmake \
    cuda-command-line-tools-${CUDA/./-} \
    libcusparse-dev-${CUDA/./-} \
    libcublas-dev-${CUDA/./-} \
    libcusolver-dev-${CUDA/./-} \
    git \
    hmmer \
    kalign \
    tzdata \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Compile HHsuite from source.
RUN git clone --branch v3.3.0 https://github.com/soedinglab/hh-suite.git /tmp/hh-suite \
    && mkdir /tmp/hh-suite/build \
    && pushd /tmp/hh-suite/build \
    && cmake -DCMAKE_INSTALL_PREFIX=/opt/hhsuite .. \
    && make -j 4 && make install \
    && ln -s /opt/hhsuite/bin/* /usr/bin \
    && popd \
    && rm -rf /tmp/hh-suite

# Install Miniconda package manager.
RUN wget -q -P /tmp \
  https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh \
    && bash /tmp/Miniconda3-latest-Linux-x86_64.sh -b -p /opt/conda \
    && rm /tmp/Miniconda3-latest-Linux-x86_64.sh

ENV PATH="/opt/conda/bin:$PATH"

# Install conda packages.
RUN conda update -n base -c defaults conda
RUN mkdir /tmp/conda_env
COPY ./docker/environment_template.yml /tmp/conda_env/
RUN sed "s/<CUDA_VER>/${CUDA}/" /tmp/conda_env/environment_template.yml > /tmp/conda_env/environment.yml \
    && grep cudatoolkit /tmp/conda_env/environment.yml \
    && conda env update -n base -f /tmp/conda_env/environment.yml \
    && conda clean --all && rm -rf /tmp/conda_env && conda list -n base

COPY . /opt/openfold
RUN wget -q -P /opt/openfold/openfold/resources \
  https://git.scicore.unibas.ch/schwede/openstructure/-/raw/7102c63615b64735c4941278d92b554ec94415f8/modules/mol/alg/src/stereo_chemical_props.txt
RUN patch -p0 -d /opt/conda/lib/python3.7/site-packages/ < /opt/openfold/lib/openmm.patch

WORKDIR /opt/openfold
RUN python3 setup.py install