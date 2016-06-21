# Makefile for Syndicate CI Test

WORKSPACE ?= .
CONTAINER_DIR ?= ${WORKSPACE}/containers
RESULT_DIR ?= ${WORKSPACE}/results
OUTPUT_DIR ?= ${WORKSPACE}/output
NO_DOCKER_CACHE ?= false

DOCKER ?= docker
DOCKER_COMPOSE ?= docker-compose -f $(CONTAINER_DIR)/docker-compose.yml

GAE_SDK := $(CONTAINER_DIR)/google_appengine_1.9.36.zip

$(GAE_SDK):
	curl -o $@ https://storage.googleapis.com/appengine-sdks/featured/$(@F)

# For configuring the MS
BUILD_MS := $(CONTAINER_DIR)/ms
CONFIG_DIR := $(CONTAINER_DIR)/ms
include configure_ms.mk

cleanbuild:
	docker build -f $(CONTAINER_DIR)/Dockerfile.base --no-cache=true --rm -t syndicate-ci-base $(CONTAINER_DIR)

build:
	docker build -f $(CONTAINER_DIR)/Dockerfile.base --no-cache=${NO_DOCKER_CACHE} --rm -t syndicate-ci-base $(CONTAINER_DIR)

tests:
	bash run_syndicate_tests.sh

full_test: docker_test rmi

docker_test: up
	$(DOCKER_COMPOSE) run test /opt/run_syndicate_tests.sh

# sleep is to let the MS start up
up: $(GAE_SDK) cleanbuild $(CONTAINER_DIR)/ms/app.yaml
	$(DOCKER_COMPOSE) build
	$(DOCKER_COMPOSE) up --timeout 1 -d
	sleep 10

stop:
	$(DOCKER_COMPOSE) stop

rm: stop
	$(DOCKER_COMPOSE) rm --force

rmi: rm
	$(DOCKER) rmi `docker images | grep "^<none>" | awk '{print $$3}'`

manual_test: up
	$(DOCKER_COMPOSE) run test bash

enter:
	$(DOCKER) exec -it syndicate-ci-ms bash

showlogs:
	$(DOCKER_COMPOSE) logs

clean: clean_certs
	rm -f $(RESULT_DIR)/*.tap
	rm -rf $(OUTPUT_DIR)/*

