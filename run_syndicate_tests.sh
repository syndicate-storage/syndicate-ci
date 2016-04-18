#!/usr/bin/env bash
# Runs syndicate tests in PATHDIR, puts TAP results in TESTDIR

PATHDIR=./tests
RESULTDIR=./results

# remove old results
rm -f ${RESULTDIR}/*.tap

# run the tests
for test in ${PATHDIR}/*.sh; do
  testname=${test##*/}
  echo "running test ${test}"
  bash ${test} > ${RESULTDIR}/${testname%.*}.tap
done

