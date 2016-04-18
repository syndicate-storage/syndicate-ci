# Makefile for Syndicate CI Test

WORKSPACE ?= .
CONTAINER_DIR ?= ${WORKSPACE}/containers
RESULT_DIR ?= ${WORKSPACE}/results
NO_DOCKER_CACHE ?= true

DOCKER ?= docker
DOCKER_COMPOSE ?= docker-compose -f $(CONTAINER_DIR)/docker-compose.yml

GAE_SDK := $(CONTAINER_DIR)/google_appengine_1.9.35.zip

$(GAE_SDK):
	curl -o $@ https://storage.googleapis.com/appengine-sdks/featured/$(@F)

.PHONY: tests
tests:
	bash run_syndicate_tests.sh

clean:
	rm -f $(RESULT_DIR)/*.tap

# For configuring the MS
BUILD_MS := $(CONTAINER_DIR)/ms
MS_FILES:= $(CONTAINER_DIR)/ms
include configure_ms.mk

.PHONY: build
build:
	sudo docker build -f $(CONTAINER_DIR)/Dockerfile.base --no-cache=${NO_DOCKER_CACHE} --rm -t syndicate-ci-base $(CONTAINER_DIR)
	sudo docker build -f $(CONTAINER_DIR)/Dockerfile.ms --no-cache=${NO_DOCKER_CACHE} --rm -t syndicate-ci-ms $(CONTAINER_DIR)
	sudo docker build -f $(CONTAINER_DIR)/Dockerfile.test --no-cache=${NO_DOCKER_CACHE} --rm -t syndicate-ci-test $(CONTAINER_DIR)

.PHONY: build
build:
	docker build --no-cache=${NO_DOCKER_CACHE} --rm -t ci-syndicate $(CONTAINER_DIR)

docker_test: $(GAE_SDK) up rm

up: $(GAE_SDK) $(CONTAINER_DIR)/ms/app.yaml
	sudo $(DOCKER_COMPOSE) build
	sudo $(DOCKER_COMPOSE) up --timeout 1 --no-build -d
	sleep 10

stop:
	sudo $(DOCKER_COMPOSE) stop

rm: stop
	sudo $(DOCKER_COMPOSE) rm --force

enter:
	sudo $(DOCKER) exec -it syndicate_ci_1 bash

showlogs:
	sudo $(DOCKER_COMPOSE) logs

