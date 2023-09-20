# take the tensorflow gpu image
FROM tensorflow/tensorflow:2.14.0rc1-gpu

# Workdir
WORKDIR /src/mineseg

# copy
COPY ./requirements.txt /src/mineseg

# Install application dependencies
RUN pip install -r requirements.txt


