#!/usr/bin/env bash

TO=600
MO=14000

RESULTS_DIR=results/no_preprocessing
mkdir -p "$RESULTS_DIR"

./runlim -r "$TO" -s "$MO" python3 -u main_no.py graph01 "$TO" 2>&1 | tee "$RESULTS_DIR/graph01.log"
./runlim -r "$TO" -s "$MO" python3 -u main_no.py graph02 "$TO" 2>&1 | tee "$RESULTS_DIR/graph02.log"
./runlim -r "$TO" -s "$MO" python3 -u main_no.py graph08 "$TO" 2>&1 | tee "$RESULTS_DIR/graph08.log"
./runlim -r "$TO" -s "$MO" python3 -u main_no.py graph09 "$TO" 2>&1 | tee "$RESULTS_DIR/graph09.log"
./runlim -r "$TO" -s "$MO" python3 -u main_no.py graph14 "$TO" 2>&1 | tee "$RESULTS_DIR/graph14.log"
./runlim -r "$TO" -s "$MO" python3 -u main_no.py scen01 "$TO" 2>&1 | tee "$RESULTS_DIR/scen01.log"
./runlim -r "$TO" -s "$MO" python3 -u main_no.py scen02 "$TO" 2>&1 | tee "$RESULTS_DIR/scen02.log"
./runlim -r "$TO" -s "$MO" python3 -u main_no.py scen03 "$TO" 2>&1 | tee "$RESULTS_DIR/scen03.log"
./runlim -r "$TO" -s "$MO" python3 -u main_no.py scen04 "$TO" 2>&1 | tee "$RESULTS_DIR/scen04.log"
./runlim -r "$TO" -s "$MO" python3 -u main_no.py scen11 "$TO" 2>&1 | tee "$RESULTS_DIR/scen11.log"

./runlim -r "$TO" -s "$MO" python3 -u main_no.py graph03 "$TO" 2>&1 | tee "$RESULTS_DIR/graph03.log"
./runlim -r "$TO" -s "$MO" python3 -u main_no.py graph04 "$TO" 2>&1 | tee "$RESULTS_DIR/graph04.log"
./runlim -r "$TO" -s "$MO" python3 -u main_no.py graph05 "$TO" 2>&1 | tee "$RESULTS_DIR/graph05.log"
./runlim -r "$TO" -s "$MO" python3 -u main_no.py graph06 "$TO" 2>&1 | tee "$RESULTS_DIR/graph06.log"
./runlim -r "$TO" -s "$MO" python3 -u main_no.py graph07 "$TO" 2>&1 | tee "$RESULTS_DIR/graph07.log"
./runlim -r "$TO" -s "$MO" python3 -u main_no.py graph10 "$TO" 2>&1 | tee "$RESULTS_DIR/graph10.log"
./runlim -r "$TO" -s "$MO" python3 -u main_no.py graph11 "$TO" 2>&1 | tee "$RESULTS_DIR/graph11.log"
./runlim -r "$TO" -s "$MO" python3 -u main_no.py graph12 "$TO" 2>&1 | tee "$RESULTS_DIR/graph12.log"
./runlim -r "$TO" -s "$MO" python3 -u main_no.py graph13 "$TO" 2>&1 | tee "$RESULTS_DIR/graph13.log"
./runlim -r "$TO" -s "$MO" python3 -u main_no.py scen05 "$TO" 2>&1 | tee "$RESULTS_DIR/scen05.log"
./runlim -r "$TO" -s "$MO" python3 -u main_no.py scen06 "$TO" 2>&1 | tee "$RESULTS_DIR/scen06.log"
./runlim -r "$TO" -s "$MO" python3 -u main_no.py scen07 "$TO" 2>&1 | tee "$RESULTS_DIR/scen07.log"
./runlim -r "$TO" -s "$MO" python3 -u main_no.py scen08 "$TO" 2>&1 | tee "$RESULTS_DIR/scen08.log"
./runlim -r "$TO" -s "$MO" python3 -u main_no.py scen09 "$TO" 2>&1 | tee "$RESULTS_DIR/scen09.log"
./runlim -r "$TO" -s "$MO" python3 -u main_no.py scen10 "$TO" 2>&1 | tee "$RESULTS_DIR/scen10.log"
./runlim -r "$TO" -s "$MO" python3 -u main_no.py TUD200.1 "$TO" 2>&1 | tee "$RESULTS_DIR/TUD200.1.log"
./runlim -r "$TO" -s "$MO" python3 -u main_no.py TUD200.2 "$TO" 2>&1 | tee "$RESULTS_DIR/TUD200.2.log"
./runlim -r "$TO" -s "$MO" python3 -u main_no.py TUD200.3 "$TO" 2>&1 | tee "$RESULTS_DIR/TUD200.3.log"
./runlim -r "$TO" -s "$MO" python3 -u main_no.py TUD200.4 "$TO" 2>&1 | tee "$RESULTS_DIR/TUD200.4.log"
./runlim -r "$TO" -s "$MO" python3 -u main_no.py TUD200.5 "$TO" 2>&1 | tee "$RESULTS_DIR/TUD200.5.log"
./runlim -r "$TO" -s "$MO" python3 -u main_no.py TUD916.1 "$TO" 2>&1 | tee "$RESULTS_DIR/TUD916.1.log"
./runlim -r "$TO" -s "$MO" python3 -u main_no.py TUD916.2 "$TO" 2>&1 | tee "$RESULTS_DIR/TUD916.2.log"
./runlim -r "$TO" -s "$MO" python3 -u main_no.py TUD916.3 "$TO" 2>&1 | tee "$RESULTS_DIR/TUD916.3.log"
./runlim -r "$TO" -s "$MO" python3 -u main_no.py TUD916.4 "$TO" 2>&1 | tee "$RESULTS_DIR/TUD916.4.log"
./runlim -r "$TO" -s "$MO" python3 -u main_no.py TUD916.5 "$TO" 2>&1 | tee "$RESULTS_DIR/TUD916.5.log"
