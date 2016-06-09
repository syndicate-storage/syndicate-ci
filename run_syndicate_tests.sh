#!/usr/bin/env bash
# Runs syndicate tests in PATHDIR, puts TAP results in TESTDIR

PATHDIR=./tests
RESULTDIR=./results
BASH=/bin/bash

SYNDICATE_ADMIN="syndicate-ms@example.com"
SYNDICATE_MS="http://ms:8080"
SYNDICATE_MS_KEYDIR=/opt/ms
SYNDICATE_MS_ROOT=/opt/ms
SYNDICATE_PRIVKEY_PATH=./ms_src/admin.pem

SYNDICATE_RG_ROOT=/usr/bin/
SYNDICATE_UG_ROOT=/usr/bin/
SYNDICATE_AG_ROOT=/usr/bin/
SYNDICATE_PYTHON_ROOT=/usr/lib/python2.7/dist-packages/

SYNDICATE_TOOL=/usr/bin/syndicate

# Start testing
echo "Start Time: `date +'%F %T'`"
start_t=`date +%s`
echo "Working in: '`pwd`'"

# remove old results
rm -f ${RESULTDIR}/*.tap

# run the tests
for test in ${PATHDIR}/*.sh; do
  testname=${test##*/}
  echo "Running test: '${test}'"
  ${BASH} ${test} > ${RESULTDIR}/${testname%.*}.tap
done

echo "End Time:   `date +'%F %T'`"
end_t=`date +%s`
echo "Elapsed Time: $((${end_t} - ${start_t}))s"

