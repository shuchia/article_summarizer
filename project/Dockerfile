FROM nvidia/cuda:11.4.2-runtime-ubuntu20.04 
#CMD nvidia-smi

ENV TZ=US/Eastern
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# set working directory
WORKDIR /usr/src/app

# set environment varibles
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN rm /etc/apt/sources.list.d/cuda.list
RUN apt-key del 7fa2af80
RUN apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/7fa2af80.pub

# install system dependencies
RUN apt-get update \
  && apt-get -y install netcat gcc postgresql python3 python3-pip \
  && apt-get clean

# install python dependencies

RUN pip install --upgrade pip
COPY ./requirements.txt .
COPY ./requirements-dev.txt .
RUN pip  install -r requirements-dev.txt
#RUN pip install torch torchvision
# add app
COPY . .

# run entrypoint.sh
ENTRYPOINT ["/usr/src/app/entrypoint.sh"]
#ENTRYPOINT ["sh"]
#ENTRYPOINT ["tail"]
#CMD ["-f","/dev/null"]
