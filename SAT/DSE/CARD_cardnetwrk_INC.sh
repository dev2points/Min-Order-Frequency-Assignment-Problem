#!/usr/bin/env bash
# set -euo pipefail
cd "$(dirname "$0")"

TO=600
MO=14000

RESULT=results/preprocessing/CARD_cardnetwrk_INC
NO_RESULT=results/no_preprocessing/CARD_cardnetwrk_INC
mkdir -p "$RESULT"
mkdir -p "$NO_RESULT"

DATASETS=(
  graph01 graph02 graph08 graph09 graph14
  scen01 scen02 scen03 scen04 scen11
  graph03 graph04 graph05 graph06 graph07
  graph10 graph11 graph12 graph13
  scen05 scen06 scen07 scen08 scen09 scen10
  TUD200.1 TUD200.2 TUD200.3 TUD200.4 TUD200.5
  TUD916.1 TUD916.2 TUD916.3 TUD916.4 TUD916.5
 
)

for ds in "${DATASETS[@]}"; do
  ./runlim -r "$TO" -s "$MO" python3 -u pairwise.py "$ds" tot assumptions cadical195 3 card 3 2>&1 | tee "$RESULT/$ds.log"
done

for ds in "${DATASETS[@]}"; do
  ./runlim -r "$TO" -s "$MO" python3 -u pairwise_no_preprocessing.py "$ds" tot assumptions cadical195 3 card 3 2>&1 | tee "$NO_RESULT/$ds.log"
done
