# Syndicate Continuous Integration testing framework

This repo contains the framework for testing Syndicate under Jenkins CI.

Tests to be run have been split out into the
[syndicate-tests](https://github.com/syndicate-storage/syndicate-tests/) repo.

## Makefile/Docker-based Test Process

 - Syndicate binary packages are built with Jenkins, triggering the CI process
   to start the test process.
 - Test scripts are checked out from the `syndicate-tests` repo.
 - `make full_test` is run by Jenkins, which builds docker images for a `base`,
   `ms`, and `test` containers and installs the Syndicate binary packages
 - Docker instances are created per `containers/docker-compose.yml`
 - Tests are run with the `testwrapper.sh` script - Docker instances and images
   are deleted
 - Jenkins collects the contents of the `output` and `results` directories as
   artifacts and process the TAP files in the results directory.

