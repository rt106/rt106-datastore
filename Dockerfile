# Copyright (c) General Electric Company, 2023.  All rights reserved.

FROM ubuntu:22.04

ARG http_proxy
ARG https_proxy

# ENV ftp_proxy=http://proxy.research.ge.com
ENV http_proxy=$http_proxy
ENV https_prpxy=$https_proxy
ENV HTTP_PROXY=$http_proxy
ENV HTTP_PROXYS=$https_proxy

#RUN groupadd g01034722
#RUN useradd dp116731 -g g01034722 -d /home/dp116731 -s /bin/bash

# install Python 3 and Pip 3
RUN apt-get -y update && apt-get install -y $buildDeps --no-install-recommends \
    && apt-get install -y python3 python3-pip \
    && pip install --upgrade pip && hash -r

# install needed dependencies for Python 3
RUN pip install --proxy $http_proxy flask pika boto3 requests junit-xml pytest-cov \
    && pip install --proxy $http_proxy flask-restful flask-cors pydicom \
    && pip install --proxy $http_proxy --upgrade setuptools

# install datastore code
ADD entrypoint.sh dataServer.py /rt106/

# set permissions
RUN chmod a+x /rt106/entrypoint.sh

# set the working directory
WORKDIR /rt106

# establish the user
# create non-privileged user and group
RUN groupadd -r rt106 && useradd -r -g rt106 rt106 && chown -R rt106:rt106 /rt106
USER rt106:rt106

# configure the default port for the datastore, can be overriden in entrypoint
EXPOSE 5106

# entry point
CMD ["/rt106/entrypoint.sh"]
