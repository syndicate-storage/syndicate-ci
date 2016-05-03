# Syndicate CI Test MS Dockerfile

FROM syndicate-ci-base
MAINTAINER Zack Williams <zdw@cs.arizona.edu>

ENV MS_PORT 8080
ENV GAE_SDK google_appengine_1.9.36.zip

# Install Syndicate MS
RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install -y --force-yes\
    syndicate-ms \
    unzip

# setup GAE
WORKDIR $HOME
COPY $GAE_SDK $GAE_SDK
RUN unzip -q $GAE_SDK
RUN rm -f $GAE_SDK

# Expose the MS port
EXPOSE $MS_PORT

# Switch to being the syndicate user
USER syndicate

# Create a storage location
RUN mkdir $HOME/datastore

# run the MS under GAE
CMD ["google_appengine/dev_appserver.py","--admin_host=0.0.0.0", "--host=0.0.0.0", "--storage_path=/home/syndicate/datastore", "--skip_sdk_update_check=true", "/usr/src/syndicate/ms"]

