# Syndicate CI Test MS Dockerfile

FROM syndicate.base
MAINTAINER Zack Williams <zdw@cs.arizona.edu>

ENV MS_PORT 8080
ENV GAE_SDK google_appengine_1.9.35.zip

# Install Syndicate MS
RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install -y --force-yes\
    syndicate-ms \
    wget \
    unzip

# setup GAE
RUN wget -nv https://storage.googleapis.com/appengine-sdks/featured/$GAE_SDK
RUN unzip -q $GAE_SDK

# Expose the MS port
EXPOSE $MS_PORT

# Create a storage location
RUN mkdir $HOME/datastore

# run the MS under GAE
CMD $HOME/google_appengine/dev_appserver.py --admin_host=0.0.0.0 --host=0.0.0.0 --storage_path=$HOME/datastore --skip_sdk_update_check=true /usr/src/syndicate/ms

