# take the tensorflow gpu image
FROM ubuntu:focal

# Workdir
WORKDIR /src/mineseg

# copy requirements file
COPY ./requirements.txt /src/mineseg

RUN apt update
RUN apt install wget -y

# install miniconda in silent mode
ENV CONDA_DIR /opt/conda
RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh && /bin/bash ~/miniconda.sh -b -p /opt/conda

# Put conda in path so we can use conda activate
ENV PATH=$CONDA_DIR/bin:$PATH

RUN conda init bash

# create new environment
RUN conda create --name mineseg python=3.9 -y

# make bash always start with activating the environment
RUN echo "conda activate mineseg" >> ~/.bashrc

# Make RUN commands use the new environment
SHELL ["conda", "run", "-n", "mineseg", "/bin/bash", "-c"]

# install system packages in container
RUN apt update && apt install ffmpeg libsm6 libxext6  -y

# install python packages
RUN conda install pytorch torchvision torchaudio pytorch-cuda=11.8 -c pytorch -c nvidia
RUN pip install -r requirements.txt



#########
# USAGE #
#########

# run this to create the docker container
# docker build -t mineseg:live .

# then run this command
# docker run -it --gpus all --name mineseg_live --ipc host -v $HOME/src/mineseg/:/src/mineseg/ mineseg:live "bash && conda activate mineseg"
