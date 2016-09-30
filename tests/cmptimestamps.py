#!/usr/bin/env python
# cmptimestamps.py
# compare two timestamps

import argparse
import sys

def exit_success():
    print 0
    sys.exit(0)

def exit_fail():
    print 1
    sys.exit(1)

# handle arguments
parser = argparse.ArgumentParser()

parser.add_argument('op', help="operation")
parser.add_argument('-f', help="read from file",
                    action="store_true")
parser.add_argument('t1', help="timestamp1")
parser.add_argument('t2', help="timestamp2")

args = parser.parse_args()

t1 = 0
t2 = 0
if args.f:
    # read from files
    with open(args.t1, 'r') as f1:
        for line in f1:
            t1 = int(line)
            break

    with open(args.t2, 'r') as f2:
        for line in f2:
            t2 = int(line)
            break;
else:
    t1 = int(args.t1)
    t2 = int(args.t2)

if args.op in ["eq", "EQ"]:
    if t1 == t2:
        exit_success()
    else:
        exit_fail()
elif args.op in ["lt", "LT"]:
    if t1 < t2:
        exit_success()
    else:
        exit_fail()
elif args.op in ["le", "LE"]:
    if t1 <= t2:
        exit_success()
    else:
        exit_fail()
elif args.op in ["gt", "GT"]:
    if t1 > t2:
        exit_success()
    else:
        exit_fail()
elif args.op in ["ge", "GE"]:
    if t1 >= t2:
        exit_success()
    else:
        exit_fail()
else:
    exit_fail()
