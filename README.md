# Syndicate CI Tests

This repo contains the framework for testing Syndicate under Jenkins CI.

## Test Process

 - Syndicate binary packages are built with Jenkins, triggering the CI process
 - Jenkins grabs the most recent set of tests from this repo, and runs the
   `run_syndicate_tests.sh` script
 - Script builds a docker image, which installs the Syndicate binary packages
 - Docker instance is created from image
 - Tests are run, output is collected and reported back to Jenkins
 - Docker instance is torn down and image destroyed

## Adding tests

Add tests as shell scripts to the `tests` folder.

Name the scripts in the format `###_description.sh`.

Tests should write their results in the [Test Anything
Protocol](http://testanything.org/) format to standard output, and exit with
status 0.

If you need additional software installed, that should be done to the Docker
container.

