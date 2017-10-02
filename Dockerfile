FROM debian:wheezy

# install dependencies
RUN buildDeps='python-pip' \
    && set -x \
    && apt-get -y update && apt-get install -y $buildDeps --no-install-recommends \
    && pip install flask flask-restful flask-cors requests boto3 pydicom junit-xml pytest-cov \
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
