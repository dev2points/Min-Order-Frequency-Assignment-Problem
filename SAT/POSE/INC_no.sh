TO=600
MO=14000

CAD_RESULTS_DIR=results/no_preprocessing/INC
mkdir -p $CAD_RESULTS_DIR


./runlim -r $TO -s $MO  python3 -u main_no_preprocessing.py scen01 tot assumptions cadical195 2>&1 | tee $CAD_RESULTS_DIR/scen01.log
./runlim -r $TO -s $MO  python3 -u main_no_preprocessing.py scen02 tot assumptions cadical195 2>&1 | tee $CAD_RESULTS_DIR/scen02.log
./runlim -r $TO -s $MO  python3 -u main_no_preprocessing.py scen03 tot assumptions cadical195 2>&1 | tee $CAD_RESULTS_DIR/scen03.log
./runlim -r $TO -s $MO  python3 -u main_no_preprocessing.py scen04 tot assumptions cadical195 2>&1 | tee $CAD_RESULTS_DIR/scen04.log
./runlim -r $TO -s $MO  python3 -u main_no_preprocessing.py scen11 tot assumptions cadical195 2>&1 | tee $CAD_RESULTS_DIR/scen11.log
./runlim -r $TO -s $MO  python3 -u main_no_preprocessing.py graph01 tot assumptions cadical195 2>&1 | tee $CAD_RESULTS_DIR/graph01.log
./runlim -r $TO -s $MO  python3 -u main_no_preprocessing.py graph02 tot assumptions cadical195 2>&1 | tee $CAD_RESULTS_DIR/graph02.log
./runlim -r $TO -s $MO  python3 -u main_no_preprocessing.py graph08 tot assumptions cadical195 2>&1 | tee $CAD_RESULTS_DIR/graph08.log
./runlim -r $TO -s $MO  python3 -u main_no_preprocessing.py graph09 tot assumptions cadical195 2>&1 | tee $CAD_RESULTS_DIR/graph09.log
./runlim -r $TO -s $MO  python3 -u main_no_preprocessing.py graph14 tot assumptions cadical195 2>&1 | tee $CAD_RESULTS_DIR/graph14.log

./runlim -r $TO -s $MO  python3 -u main_no_preprocessing.py graph03 tot assumptions cadical195 2>&1 | tee $CAD_RESULTS_DIR/graph03.log
./runlim -r $TO -s $MO  python3 -u main_no_preprocessing.py graph04 tot assumptions cadical195 2>&1 | tee $CAD_RESULTS_DIR/graph04.log
./runlim -r $TO -s $MO  python3 -u main_no_preprocessing.py graph05 tot assumptions cadical195 2>&1 | tee $CAD_RESULTS_DIR/graph05.log
./runlim -r $TO -s $MO  python3 -u main_no_preprocessing.py graph06 tot assumptions cadical195 2>&1 | tee $CAD_RESULTS_DIR/graph06.log
./runlim -r $TO -s $MO  python3 -u main_no_preprocessing.py graph07 tot assumptions cadical195 2>&1 | tee $CAD_RESULTS_DIR/graph07.log
./runlim -r $TO -s $MO  python3 -u main_no_preprocessing.py graph10 tot assumptions cadical195 2>&1 | tee $CAD_RESULTS_DIR/graph10.log
./runlim -r $TO -s $MO  python3 -u main_no_preprocessing.py graph11 tot assumptions cadical195 2>&1 | tee $CAD_RESULTS_DIR/graph11.log
./runlim -r $TO -s $MO  python3 -u main_no_preprocessing.py graph12 tot assumptions cadical195 2>&1 | tee $CAD_RESULTS_DIR/graph12.log
./runlim -r $TO -s $MO  python3 -u main_no_preprocessing.py graph13 tot assumptions cadical195 2>&1 | tee $CAD_RESULTS_DIR/graph13.log
./runlim -r $TO -s $MO  python3 -u main_no_preprocessing.py scen05 tot assumptions cadical195 2>&1 | tee $CAD_RESULTS_DIR/scen05.log
./runlim -r $TO -s $MO  python3 -u main_no_preprocessing.py scen06 tot assumptions cadical195 2>&1 | tee $CAD_RESULTS_DIR/scen06.log
./runlim -r $TO -s $MO  python3 -u main_no_preprocessing.py scen07 tot assumptions cadical195 2>&1 | tee $CAD_RESULTS_DIR/scen07.log
./runlim -r $TO -s $MO  python3 -u main_no_preprocessing.py scen08 tot assumptions cadical195 2>&1 | tee $CAD_RESULTS_DIR/scen08.log
./runlim -r $TO -s $MO  python3 -u main_no_preprocessing.py scen09 tot assumptions cadical195 2>&1 | tee $CAD_RESULTS_DIR/scen09.log
./runlim -r $TO -s $MO  python3 -u main_no_preprocessing.py scen10 tot assumptions cadical195 2>&1 | tee $CAD_RESULTS_DIR/scen10.log
./runlim -r $TO -s $MO  python3 -u main_no_preprocessing.py TUD200.1 tot assumptions cadical195 2>&1 | tee $CAD_RESULTS_DIR/TUD200.1.log
./runlim -r $TO -s $MO  python3 -u main_no_preprocessing.py TUD200.2 tot assumptions cadical195 2>&1 | tee $CAD_RESULTS_DIR/TUD200.2.log
./runlim -r $TO -s $MO  python3 -u main_no_preprocessing.py TUD200.3 tot assumptions cadical195 2>&1 | tee $CAD_RESULTS_DIR/TUD200.3.log
./runlim -r $TO -s $MO  python3 -u main_no_preprocessing.py TUD200.4 tot assumptions cadical195 2>&1 | tee $CAD_RESULTS_DIR/TUD200.4.log
./runlim -r $TO -s $MO  python3 -u main_no_preprocessing.py TUD200.5 tot assumptions cadical195 2>&1 | tee $CAD_RESULTS_DIR/TUD200.5.log
./runlim -r $TO -s $MO  python3 -u main_no_preprocessing.py TUD916.1 tot assumptions cadical195 2>&1 | tee $CAD_RESULTS_DIR/TUD916.1.log
./runlim -r $TO -s $MO  python3 -u main_no_preprocessing.py TUD916.2 tot assumptions cadical195 2>&1 | tee $CAD_RESULTS_DIR/TUD916.2.log
./runlim -r $TO -s $MO  python3 -u main_no_preprocessing.py TUD916.3 tot assumptions cadical195 2>&1 | tee $CAD_RESULTS_DIR/TUD916.3.log
./runlim -r $TO -s $MO  python3 -u main_no_preprocessing.py TUD916.4 tot assumptions cadical195 2>&1 | tee $CAD_RESULTS_DIR/TUD916.4.log
./runlim -r $TO -s $MO  python3 -u main_no_preprocessing.py TUD916.5 tot assumptions cadical195 2>&1 | tee $CAD_RESULTS_DIR/TUD916.5.log
