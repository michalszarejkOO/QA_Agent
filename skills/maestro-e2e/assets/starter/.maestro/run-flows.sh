#!/bin/zsh
# Runs Maestro flows one by one on a simulator or emulator, in rounds, and prints a PASS / FAIL line per flow.
#
#   .maestro/run-flows.sh -d <device-id> [-r <rounds>] [-t <tag>] [-o <output-dir>] [flow-name ...]
#
# Flow names are file names from .maestro/flows/** without .yaml; with none given every flow runs
# (only those tagged <tag> with -t, never those tagged wip). The output directory gets summary.txt,
# junit.xml with every flow run and per-flow debug output.
#
# A flow is rerun once only when the Maestro driver itself failed: it died ("Device unreachable"
# in maestro.log), XCTest timed out reading the screen ("Snapshot failure" in its log, which froze
# the app for minutes right after launch) or the driver never started (IOSDriverTimeoutException). That is not a result of the app or the flow, and is
# reported as INFRA_RETRY so it stays visible. Every other failure is final.

set -u
MAESTRO_DIR=${0:A:h}
DEVICE=""
ROUNDS=1
TAG=""
OUT=${TMPDIR:-/tmp}/maestro-run-$(date +%Y%m%d-%H%M%S)

while getopts "d:r:t:o:" opt; do
  case $opt in
    d) DEVICE=$OPTARG ;;
    r) ROUNDS=$OPTARG ;;
    t) TAG=$OPTARG ;;
    o) OUT=$OPTARG ;;
    *) exit 2 ;;
  esac
done
shift $((OPTIND - 1))
[[ -z $DEVICE ]] && { echo "usage: $0 -d <device-id> [-r rounds] [-t tag] [-o output-dir] [flow ...]"; exit 2; }

if grep -rnE '^\s*-?\s*(sleep|point)\s*:' $MAESTRO_DIR/flows $MAESTRO_DIR/subflows; then
  echo "Flows must not sleep or tap by coordinates (see README.md)."
  exit 2
fi

has_tag() {
  sed '/^---$/q' $1 | grep -qx "  - $2"
}

typeset -A FLOW_PATHS
for file in $MAESTRO_DIR/flows/**/*.yaml; do FLOW_PATHS[${file:t:r}]=$file; done

FLOWS=("$@")
if (( ${#FLOWS} == 0 )); then
  for name in ${(ko)FLOW_PATHS}; do
    has_tag $FLOW_PATHS[$name] wip && continue
    [[ -n $TAG ]] && ! has_tag $FLOW_PATHS[$name] $TAG && continue
    FLOWS+=$name
  done
fi
for flow in $FLOWS; do
  [[ -z ${FLOW_PATHS[$flow]:-} ]] && { echo "no such flow: $flow"; exit 2; }
done

mkdir -p $OUT
SUMMARY=$OUT/summary.txt
: > $SUMMARY

run_once() {
  local flow=$1 dir=$2
  rm -rf $dir
  maestro --device $DEVICE test $FLOW_PATHS[$flow] --debug-output $dir \
    --format JUNIT --output $dir.junit.xml > $dir.log 2>&1
}

driver_died() {
  grep -q -s -E "DeviceUnreachableException|Device unreachable|Transport unreachable" $1/.maestro/tests/*/maestro.log ||
    grep -q -s "Snapshot failure, cannot return view hierarchy" $1/.maestro/tests/*/xctest_runner_*.log ||
    grep -q -s "IOSDriverTimeoutException" $1.log
}

failures=0
for round in $(seq 1 $ROUNDS); do
  for flow in $FLOWS; do
    dir=$OUT/r${round}_$flow
    start=$SECONDS
    result=PASS
    if ! run_once $flow $dir; then
      if driver_died $dir; then
        mv $dir $dir.driver-crash
        mv $dir.log $dir.driver-crash.log
        if run_once $flow $dir; then result=INFRA_RETRY; else result=FAIL; fi
      else
        result=FAIL
      fi
    fi
    [[ $result == FAIL ]] && failures=$((failures + 1))
    echo "r$round $flow $((SECONDS - start))s $result" | tee -a $SUMMARY
  done
done

{
  echo "<?xml version='1.0' encoding='UTF-8'?>"
  echo "<testsuites>"
  for report in $OUT/r*_*.junit.xml(N); do sed -n '/<testsuite /,/<\/testsuite>/p' $report; done
  echo "</testsuites>"
} > $OUT/junit.xml

echo "failures: $failures, output: $OUT" | tee -a $SUMMARY
(( failures == 0 ))
