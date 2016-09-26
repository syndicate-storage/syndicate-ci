# Syndicate CI Tests

This repo contains the framework for testing Syndicate under Jenkins CI.

## Makefile/Docker-based Test Process

 - Syndicate binary packages are built with Jenkins, triggering the CI process
 - Script builds a docker image, which installs the Syndicate binary packages
 - Docker instance is created from image
 - Tests are run with the `testwrapper.sh` script, output is collected and
   reported back to Jenkins
 - Docker instance is torn down and image destroyed

## Running tests manually

The tests are run with `testrunner.py`, which reads YAML files (syntax below),
runs the tests and generates output.

This requires that `pyyaml` be installed.  Usually available as `python-yaml`
or similar from your friendly package manager.

There's a convenience script, `testwrapper.sh` that will run all the tests
matching `tests/*.yml`, put their TAP output in `results` and the output of the
commands in `output`

## Adding tests

Add tests to the `tests` folder, named in the format `###_description.yml`,
using the test syntax specified below.

## Tests file syntax

The syntax of the testing files has two block types, `setup` and `tasks`.

### Setup blocks

```


```


Setup is used to define variables, create testing directories, and files with
random contents.

There are two types of variables, scalars and arrays.  Scalars can be used in a
variety of contexts, arrays can only be used with the `loop_on` construct for
task blocks. Scalars are accessed with the familiar `$var_name` syntax.

Scalars:

`tmpdirs` - Creates temporary directories prefixed with `name`, and assigned to
variable `varname`

`randfiles` - Creates a file at `path` with random contents that is `size`
bytes long.  Path specification can include other variables.

`randnames` - From the `name` given, assign a value `name-<random characters>`

`vars` - Assign `name` a value `value`.  `value` can include other variables.

Arrays:

`randloop` - loop version of `randnames` - generate `quantity` random names in
an array

`sequenceloop` - generate `quantity` numbers, with a selectable `start`
(default is `0`) and step (default is `1`) size.

`valuesloop` - use the `values` list supplied as an array

Note that while `setup` value assignments can be used immediately, they always
are evaluated in groups in the order shown above within a setup block.  For
example, running `tmpdirs` then using the variable defined there in `vars` will
work, but the opposite won't.  If you need to get around this, make multiple
setup blocks.


### Special Variables

There are some special variables that are set:

Global scope:

 - `$tasksf_dir` - directory that the tasks file is located in
 - `$tasksf_name` - filename (basename) of the tasks file.

Within a `loop_on` task:

 - `$loop_var` - set to the value of the array being looped on.
 - `$loop_index` - set to the index (starts with 0) of the array being looped on.

Within a task:

 - `$task_name` - name of the current task

### Task blocks

Task blocks are used to run commands come in 3 types, `sequential`, `parallel`,
and `daemon`.

Task blocks are executed in the sequence they appear in the task file.

`sequential` tasks are run in order within a task block. Each task will be
executed after the previous task has terminated.  The task block will complete
after the last task has completed

`parallel` tasks are started in parallel, and the task block is completed
after every task within it has exited.

`daemon` tasks are started in parallel, but are left running while subsequent
task blocks are run. If the daemon process is still running after all other
task blocks have completed, the tasks within are are terminated with `SIGTERM`.

The `command:` directive specifies the command to run. Variables can be
interpolated here, but as this is not run in a sub-shell, piping or redirection
is not supported - see `saveout` and `saveerr` below.

#### Looping

`loop_on` can be included in a task block to cause multiple copies of the same
command to be run, when provided an array of values to loop over.

There are two variables set each time the loop is run, `$loop_var` and
`$loop_index`, which correspondingly have a value from the array and the
current loop number (starting at 0).

### Command Tests

`exit` - The exit code that the command should exit with, if it's not the
default of `0`.  Fail test if the command's exit code is not this value, or if
`exit` isn't specified, if the exit code isn't `0`.

`checkout` and `checkerr` - compare the `stdout` and `stderr` streams to the
contents of a file. Fail test if it contents don't match.

`saveout` and `saveerr` - not tests, but these save the `stdout` and
`stderr` streams to a file.  Doesn't affect job success/failure.

### Output


