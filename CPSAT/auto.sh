#!/usr/bin/env bash

TO=600
MO=14000

NO_RESULTS_DIR=results/no_preprocessing
RESULTS_DIR=results/preprocessing
mkdir -p "$NO_RESULTS_DIR"
mkdir -p "$RESULTS_DIR"

./runlim -r "$TO" -s "$MO" python3 -u main.py graph01 "$TO" 2>&1 | tee "$RESULTS_DIR/graph01.log"
./runlim -r "$TO" -s "$MO" python3 -u main.py graph02 "$TO" 2>&1 | tee "$RESULTS_DIR/graph02.log"
./runlim -r "$TO" -s "$MO" python3 -u main.py graph08 "$TO" 2>&1 | tee "$RESULTS_DIR/graph08.log"
./runlim -r "$TO" -s "$MO" python3 -u main.py graph09 "$TO" 2>&1 | tee "$RESULTS_DIR/graph09.log"
./runlim -r "$TO" -s "$MO" python3 -u main.py graph14 "$TO" 2>&1 | tee "$RESULTS_DIR/graph14.log"
./runlim -r "$TO" -s "$MO" python3 -u main.py scen01 "$TO" 2>&1 | tee "$RESULTS_DIR/scen01.log"
./runlim -r "$TO" -s "$MO" python3 -u main.py scen02 "$TO" 2>&1 | tee "$RESULTS_DIR/scen02.log"
./runlim -r "$TO" -s "$MO" python3 -u main.py scen03 "$TO" 2>&1 | tee "$RESULTS_DIR/scen03.log"
./runlim -r "$TO" -s "$MO" python3 -u main.py scen04 "$TO" 2>&1 | tee "$RESULTS_DIR/scen04.log"
./runlim -r "$TO" -s "$MO" python3 -u main.py scen11 "$TO" 2>&1 | tee "$RESULTS_DIR/scen11.log"

./runlim -r "$TO" -s "$MO" python3 -u main.py graph03 "$TO" 2>&1 | tee "$RESULTS_DIR/graph03.log"
./runlim -r "$TO" -s "$MO" python3 -u main.py graph04 "$TO" 2>&1 | tee "$RESULTS_DIR/graph04.log"
./runlim -r "$TO" -s "$MO" python3 -u main.py graph05 "$TO" 2>&1 | tee "$RESULTS_DIR/graph05.log"
./runlim -r "$TO" -s "$MO" python3 -u main.py graph06 "$TO" 2>&1 | tee "$RESULTS_DIR/graph06.log"
./runlim -r "$TO" -s "$MO" python3 -u main.py graph07 "$TO" 2>&1 | tee "$RESULTS_DIR/graph07.log"
./runlim -r "$TO" -s "$MO" python3 -u main.py graph10 "$TO" 2>&1 | tee "$RESULTS_DIR/graph10.log"
./runlim -r "$TO" -s "$MO" python3 -u main.py graph11 "$TO" 2>&1 | tee "$RESULTS_DIR/graph11.log"
./runlim -r "$TO" -s "$MO" python3 -u main.py graph12 "$TO" 2>&1 | tee "$RESULTS_DIR/graph12.log"
./runlim -r "$TO" -s "$MO" python3 -u main.py graph13 "$TO" 2>&1 | tee "$RESULTS_DIR/graph13.log"
./runlim -r "$TO" -s "$MO" python3 -u main.py scen05 "$TO" 2>&1 | tee "$RESULTS_DIR/scen05.log"
./runlim -r "$TO" -s "$MO" python3 -u main.py scen06 "$TO" 2>&1 | tee "$RESULTS_DIR/scen06.log"
./runlim -r "$TO" -s "$MO" python3 -u main.py scen07 "$TO" 2>&1 | tee "$RESULTS_DIR/scen07.log"
./runlim -r "$TO" -s "$MO" python3 -u main.py scen08 "$TO" 2>&1 | tee "$RESULTS_DIR/scen08.log"
./runlim -r "$TO" -s "$MO" python3 -u main.py scen09 "$TO" 2>&1 | tee "$RESULTS_DIR/scen09.log"
./runlim -r "$TO" -s "$MO" python3 -u main.py scen10 "$TO" 2>&1 | tee "$RESULTS_DIR/scen10.log"
./runlim -r "$TO" -s "$MO" python3 -u main.py TUD200.1 "$TO" 2>&1 | tee "$RESULTS_DIR/TUD200.1.log"
./runlim -r "$TO" -s "$MO" python3 -u main.py TUD200.2 "$TO" 2>&1 | tee "$RESULTS_DIR/TUD200.2.log"
./runlim -r "$TO" -s "$MO" python3 -u main.py TUD200.3 "$TO" 2>&1 | tee "$RESULTS_DIR/TUD200.3.log"
./runlim -r "$TO" -s "$MO" python3 -u main.py TUD200.4 "$TO" 2>&1 | tee "$RESULTS_DIR/TUD200.4.log"
./runlim -r "$TO" -s "$MO" python3 -u main.py TUD200.5 "$TO" 2>&1 | tee "$RESULTS_DIR/TUD200.5.log"
./runlim -r "$TO" -s "$MO" python3 -u main.py TUD916.1 "$TO" 2>&1 | tee "$RESULTS_DIR/TUD916.1.log"
./runlim -r "$TO" -s "$MO" python3 -u main.py TUD916.2 "$TO" 2>&1 | tee "$RESULTS_DIR/TUD916.2.log"
./runlim -r "$TO" -s "$MO" python3 -u main.py TUD916.3 "$TO" 2>&1 | tee "$RESULTS_DIR/TUD916.3.log"
./runlim -r "$TO" -s "$MO" python3 -u main.py TUD916.4 "$TO" 2>&1 | tee "$RESULTS_DIR/TUD916.4.log"
./runlim -r "$TO" -s "$MO" python3 -u main.py TUD916.5 "$TO" 2>&1 | tee "$RESULTS_DIR/TUD916.5.log"

