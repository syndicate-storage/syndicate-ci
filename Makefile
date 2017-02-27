# Makefile for Syndicate CI Test

WORKSPACE ?= .
CONTAINER_DIR ?= ${WORKSPACE}/containers
RESULT_DIR ?= ${WORKSPACE}/results
OUTPUT_DIR ?= ${WORKSPACE}/output
NO_DOCKER_CACHE ?= false

DOCKER ?= docker
DOCKER_COMPOSE ?= docker-compose -f $(CONTAINER_DIR)/docker-compose.yml

GAE_SDK := $(CONTAINER_DIR)/google_appengine_1.9.40.zip

$(GAE_SDK):
	curl -o $@ https://storage.googleapis.com/appengine-sdks/featured/$(@F)

# For configuring the MS
BUILD_MS := $(CONTAINER_DIR)/ms
CONFIG_DIR := $(CONTAINER_DIR)/ms
# name of docker container w/ms in it
MS_APP_PUBLIC_HOST := ms
include configure_ms.mk

cleanbuild:
	docker build -f $(CONTAINER_DIR)/Dockerfile.base --no-cache=true --rm -t syndicate-ci-base $(CONTAINER_DIR)

build:
	docker build -f $(CONTAINER_DIR)/Dockerfile.base --no-cache=${NO_DOCKER_CACHE} --rm -t syndicate-ci-base $(CONTAINER_DIR)

syndicate-tests:
	git pull https://github.com/syndicate-storage/syndicate-tests

tests: syndicate-tests
	bash syndicate-tests/testwrapper.sh -c -m

full_test: docker_test docker_logs rmi

docker_test: up
	$(DOCKER_COMPOSE) run test /opt/syndicate-tests/testwrapper.sh

docker_logs:
	$(DOCKER_COMPOSE) logs -t --no-color ms > ${OUTPUT_DIR}/docker_logs 2>&1

# sleep is to let the MS start up
up: $(GAE_SDK) build $(CONTAINER_DIR)/ms/app.yaml
	chmod a+w output results
	$(DOCKER_COMPOSE) build
	$(DOCKER_COMPOSE) up --timeout 1 -d ms
	sleep 10

stop:
	$(DOCKER_COMPOSE) stop

rm: stop
	-$(DOCKER_COMPOSE) rm --force --all

rmi: rm
	-$(DOCKER) rmi `docker images | grep "^<none>" | awk '{print $$3}'`

manual_test: up
	$(DOCKER_COMPOSE) run test bash

enter:
	$(DOCKER) exec -it syndicate-ci-ms bash

showlogs:
	$(DOCKER_COMPOSE) logs

clean: clean_certs
	rm -f $(RESULT_DIR)/*.tap
	rm -rf $(OUTPUT_DIR)/*
