#!/usr/bin/env bash
# Runs syndicate tests in PATHDIR, puts TAP results in TESTDIR

TESTDIR=./tests
RESULTDIR=./results
OUTPUTDIR=./output
BASH=/bin/bash

export SYNDICATE_ADMIN="syndicate-ms@example.com"

export SYNDICATE_MS="http://ms:8080"
export SYNDICATE_MS_KEYDIR=/opt/ms
export SYNDICATE_MS_ROOT=/opt/ms
export SYNDICATE_PRIVKEY_PATH=${SYNDICATE_MS_KEYDIR}/admin.pem

export SYNDICATE_TOOL=/usr/bin/syndicate
export SYNDICATE_RG_ROOT=/usr/bin/
export SYNDICATE_UG_ROOT=/usr/bin/
export SYNDICATE_AG_ROOT=/usr/bin/
export SYNDICATE_PYTHON_ROOT=/usr/lib/python2.7/dist-packages/

# Start testing
echo "Start Time: `date +'%F %T'`"
start_t=`date +%s`
echo "Working in: '`pwd`'"

# remove old results
rm -f ${RESULTDIR}/*.tap

# run the tests
for test in $(ls ${TESTDIR}/[0-9][0-9][0-9]_*.sh ); do
  testname=${test##*/}
  echo "Running test: '${testname}'"
  ${BASH} ${test} > ${RESULTDIR}/${testname%.*}.tap
  echo "Copying logs..."
  cp -r /tmp/syndicate-test-*  $OUTPUTDIR
  chmod a+rX -R $OUTPUTDIR
done

echo "End Time:   `date +'%F %T'`"
end_t=`date +%s`
echo "Elapsed Time: $((${end_t} - ${start_t}))s"

