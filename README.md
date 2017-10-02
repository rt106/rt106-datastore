# Datastore
[![Build Status](http://ideker.crd.ge.com:8888/buildStatus/icon?job=rt106/rt106-datastore/master)](http://ideker.crd.ge.com:8888/job/rt106/job/rt106-datastore/job/master/)

Base container for Rt 106 data stores.  This container defines the datastore API, and requires one of the datastore implementations.

### Docker container

To build the docker container for the front-end:

    $ docker build -t rt106/rt106-datastore:latest .

If you use HTTP proxies in your environment, you may need to build using

    $ docker build -t rt106/rt106-datastore:latest  --build-arg http_proxy=$http_proxy --build-arg https_proxy=$https_proxy --build-arg no_proxy=$no_proxy  .
