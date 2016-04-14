# Makefile for Syndicate CI Test

CONTAINER_DIR ?= containers
RESULT_DIR ?= ./results

.PHONY: tests
tests:
	bash run_syndicate_tests.sh

clean:
	rm -f $(RESULT_DIR)/*.tap

include $(CONTAINER_DIR)/MS.mk
syndicate_ms_config: $(CONTAINER_DIR)/ms/admin_info.py $(CONTAINER_DIR)/ms/app.yaml

.PHONY: build
build:
	docker build --no-cache=${NO_DOCKER_CACHE} --rm -t ci-syndicate $(CONTAINER_DIR)

run:
	sudo docker-compose up -d

stop:
	sudo docker-compose stop

rm: stop
	sudo docker-compose rm --force

enter:
	sudo docker exec -it ci_syndicate_1 bash

showlogs:
	sudo docker-compose logs

