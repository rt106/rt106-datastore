# Datastore

[![CircleCI](https://circleci.com/gh/rt106/rt106-datastore.svg?style=svg)](https://circleci.com/gh/rt106/rt106-datastore)

_Copyright (c) General Electric Company, 2017.  All rights reserved._


Base container for Rt 106 data stores.  This container defines the datastore API, and requires one of the datastore implementations.

### Docker container

To build the docker container for the front-end:

    $ docker build -t rt106/rt106-datastore:latest .

If you use HTTP proxies in your environment, you may need to build using

    $ docker build -t rt106/rt106-datastore:latest  --build-arg http_proxy=$http_proxy --build-arg https_proxy=$https_proxy --build-arg no_proxy=$no_proxy  .
