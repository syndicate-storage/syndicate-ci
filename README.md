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


### testrunner.py command

```
$ python testrunner.py -h
usage: testrunner.py [-h] [-d] [-i] [-t TAP_FILE] [-f TIME_FORMAT]
                     tasks_file output_file

positional arguments:
  tasks_file            YAML tasks input filename
  output_file           muxed output/error filename

optional arguments:
  -h, --help            show this help message and exit
  -d, --debug           print debugging info
  -i, --immediate       immediately print subprocess stdout/err
  -t TAP_FILE, --tap_file TAP_FILE
                        TAP output filename
  -f TIME_FORMAT, --time_format TIME_FORMAT
                        specify a strftime() format
```

## Tests file syntax

The syntax of the testing files has two block types, `setup` and `tasks`.

### Setup Blocks

```
- name: setup_block
  type: setup
  tmpdirs:
    - name: myconfig
      varname: config
  randnames:
    - myvar
    - thatvar
  vars:
    - name: config_dir
      value: "$config/"
  randloop:
    - name: rand_ex
      quantity: 4
  seqloop:
    - name: seq_ex
      quantity: 5
      step: 1
      start: 14
  valueloop:
    - name: val_ex
      values:
        - larry
        - moe
        - curly
```

Setup is used to define variables, create testing directories, and files with
random contents.

#### Variables

There are two types of variables, scalars and arrays.  Scalars can be used in a
variety of contexts, arrays can only be used with the `loop_on` construct for
task blocks.

Scalars are accessed using `$var_name` or `${var_name}` syntax - the latter is
required if you have a word character immediately next to the variable.   

*Scalars:*

`tmpdirs` - Creates temporary directories prefixed with `name`, and assigned to
variable `varname`, in the system `/tmp` directory.

`randnames` - From the `name` given, assign a value `name-<random characters>`

`vars` - Assign `name` a value `value`.  `value` can include other variables.

*Arrays:*

`randloop` - loop version of `randnames` - generate `quantity` random names in
an array

`seqloop` - generate `quantity` numbers, with a selectable `start`
(default is `0`) and step (default is `1`) size.

`valueloop` - use the `values` list supplied as an array

Note that while `setup` value assignments can be used immediately, they always
are evaluated in groups in the order shown above within a setup block.  For
example, running `tmpdirs` then using the variable defined there in `vars` will
work, but the opposite won't.  If you need to get around this, make multiple
setup blocks.


#### Special Variables

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

```
- name: seqblock 
  type: sequential
  tasks:
    - name: exits_one
      command: failing command
      exit: 1
      saveout: $config/exit_one
      saveerr: $config/exit_one
    - name: check_output
      command: ./delay.sh bat
      checkout: ${tasksf_dir}/baz.out
      checkerr: ${tasksf_dir}/baz.err

- name: parloopblock
  type: parallel
  loop_on: val_ex
  tasks:
   - name: echo_names
     command: echo $loop_var
```

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

#### Looping

`loop_on` can be included in a task block to cause multiple copies of the same
command to be run, when provided an array of values to loop over.

There are two variables set each time the loop is run, `$loop_var` and
`$loop_index`, which correspondingly have a value from the array and the
current loop number (starting at 0).


### Task Definitions

Each task requires a `name` and one of `command` or `shell` to be defined in it.

`command:` - specifies the command to run. Variables can be interpolated here,
but as this is not run in a sub-shell, piping or redirection is not supported -
see `saveout` and `saveerr` below.

`shell` - works like command, but runs in a subshell. This was added mainly for
fileglobbing abilties and should be used sparingly and only when absolutely
needed.

`infile` - give a filename which will be supplied to stdin of the command.

`saveout` and `saveerr` - not tests, but these save the `stdout` and `stderr`
streams to a file.

#### Command Tests

These arguments perform the pass/fail test functionality. 

`exit` - The exit code that the command should exit with, if it's not the
default of `0`.  Fail test if the command's exit code is not this value, or if
`exit` isn't specified, if the exit code isn't `0`.

`checkout` and `checkerr` - compare the `stdout` and `stderr` streams to the
contents of a file. Fail test if it contents don't match.


