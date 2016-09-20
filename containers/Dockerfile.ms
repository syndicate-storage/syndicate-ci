# Syndicate CI Test MS Dockerfile

FROM syndicate-ci-base
MAINTAINER Zack Williams <zdw@cs.arizona.edu>

ENV MS_PORT 8080
ENV GAE_SDK google_appengine_1.9.40.zip

# Install Syndicate MS
RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install -y --force-yes\
    syndicate-ms \
    unzip

# setup GAE
WORKDIR $HOME
COPY $GAE_SDK $GAE_SDK
RUN unzip -q $GAE_SDK && \
    rm -f $GAE_SDK

# Expose the MS port
EXPOSE $MS_PORT

# Create a storage location, change write permissions on /usr/src/syndicate/ms/
RUN mkdir $HOME/datastore && \
    chown -R syndicate $HOME/datastore && \
    chown -R syndicate /usr/src/syndicate/ms/

# Switch to being the syndicate user
USER syndicate

# run the MS under GAE
CMD ["google_appengine/dev_appserver.py","--admin_host=0.0.0.0", "--host=0.0.0.0", "--storage_path=/home/syndicate/datastore", "--skip_sdk_update_check=true", "/usr/src/syndicate/ms"]

