#!/usr/bin/env bash
# Runs syndicate tests in PATHDIR, puts TAP results in TESTDIR

PATHDIR=./tests
RESULTDIR=./results
BASH=/bin/bash

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

