# Copyright (c) General Electric Company, 2023.  All rights reserved.

FROM debian:bullseye-slim

# install Python 3 and Pip 3
RUN apt-get -y update && apt-get install -y $buildDeps --no-install-recommends \
    && apt-get install -y python3 python3-pip \
    && pip install --upgrade pip && hash -r

# install needed dependencies for Python 3
RUN pip install flask pika boto3 requests junit-xml pytest-cov \
    && pip install flask-restful flask-cors pydicom \
    && pip install --upgrade setuptools

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
