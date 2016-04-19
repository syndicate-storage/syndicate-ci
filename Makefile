# Makefile for Syndicate CI Test

WORKSPACE ?= .
CONTAINER_DIR ?= ${WORKSPACE}/containers
RESULT_DIR ?= ${WORKSPACE}/results
NO_DOCKER_CACHE ?= false

DOCKER ?= docker
DOCKER_COMPOSE ?= docker-compose -f $(CONTAINER_DIR)/docker-compose.yml

GAE_SDK := $(CONTAINER_DIR)/google_appengine_1.9.35.zip

$(GAE_SDK):
	curl -o $@ https://storage.googleapis.com/appengine-sdks/featured/$(@F)

# For configuring the MS
BUILD_MS := $(CONTAINER_DIR)/ms
CONFIG_DIR:= $(CONTAINER_DIR)/ms
include configure_ms.mk

build:
	sudo docker build -f $(CONTAINER_DIR)/Dockerfile.base --no-cache=${NO_DOCKER_CACHE} --rm -t syndicate-ci-base $(CONTAINER_DIR)

tests:
	bash run_syndicate_tests.sh

docker_test: up showlogs rm

up: $(GAE_SDK) build $(CONTAINER_DIR)/ms/app.yaml
	sudo $(DOCKER_COMPOSE) build
	sudo $(DOCKER_COMPOSE) up --timeout 1 -d
	sleep 5

stop:
	sudo $(DOCKER_COMPOSE) stop

rm: stop
	sudo $(DOCKER_COMPOSE) rm --force

enter:
	sudo $(DOCKER) exec -it syndicate_ci_1 bash

showlogs:
	sudo $(DOCKER_COMPOSE) logs

clean:
	rm -f $(RESULT_DIR)/*.tap


