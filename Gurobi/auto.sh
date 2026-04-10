TO=600
MO=14000
NO_RESULTS_DIR=results/no_pre_processing
mkdir -p $NO_RESULTS_DIR

RESULTS_DIR=results/pre_processing
mkdir -p $RESULTS_DIR


./runlim -r $TO -s $MO  python3 -u main.py graph01  2>&1 | tee $RESULTS_DIR/graph01.log
./runlim -r $TO -s $MO  python3 -u main.py graph02  2>&1 | tee $RESULTS_DIR/graph02.log
./runlim -r $TO -s $MO  python3 -u main.py graph08  2>&1 | tee $RESULTS_DIR/graph08.log
./runlim -r $TO -s $MO  python3 -u main.py graph09  2>&1 | tee $RESULTS_DIR/graph09.log
./runlim -r $TO -s $MO  python3 -u main.py graph14  2>&1 | tee $RESULTS_DIR/graph14.log
./runlim -r $TO -s $MO  python3 -u main.py scen01  2>&1 | tee $RESULTS_DIR/scen01.log
./runlim -r $TO -s $MO  python3 -u main.py scen02  2>&1 | tee $RESULTS_DIR/scen02.log
./runlim -r $TO -s $MO  python3 -u main.py scen03  2>&1 | tee $RESULTS_DIR/scen03.log
./runlim -r $TO -s $MO  python3 -u main.py scen04  2>&1 | tee $RESULTS_DIR/scen04.log
./runlim -r $TO -s $MO  python3 -u main.py scen11  2>&1 | tee $RESULTS_DIR/scen11.log

./runlim -r $TO -s $MO  python3 -u main.py graph03  2>&1 | tee $RESULTS_DIR/graph03.log
./runlim -r $TO -s $MO  python3 -u main.py graph04  2>&1 | tee $RESULTS_DIR/graph04.log
./runlim -r $TO -s $MO  python3 -u main.py graph05  2>&1 | tee $RESULTS_DIR/graph05.log
./runlim -r $TO -s $MO  python3 -u main.py graph06  2>&1 | tee $RESULTS_DIR/graph06.log
./runlim -r $TO -s $MO  python3 -u main.py graph07  2>&1 | tee $RESULTS_DIR/graph07.log
./runlim -r $TO -s $MO  python3 -u main.py graph10  2>&1 | tee $RESULTS_DIR/graph10.log
./runlim -r $TO -s $MO  python3 -u main.py graph11  2>&1 | tee $RESULTS_DIR/graph11.log
./runlim -r $TO -s $MO  python3 -u main.py graph12  2>&1 | tee $RESULTS_DIR/graph12.log
./runlim -r $TO -s $MO  python3 -u main.py graph13  2>&1 | tee $RESULTS_DIR/graph13.log
./runlim -r $TO -s $MO  python3 -u main.py scen05  2>&1 | tee $RESULTS_DIR/scen05.log
./runlim -r $TO -s $MO  python3 -u main.py scen06  2>&1 | tee $RESULTS_DIR/scen06.log
./runlim -r $TO -s $MO  python3 -u main.py scen07  2>&1 | tee $RESULTS_DIR/scen07.log
./runlim -r $TO -s $MO  python3 -u main.py scen08  2>&1 | tee $RESULTS_DIR/scen08.log
./runlim -r $TO -s $MO  python3 -u main.py scen09  2>&1 | tee $RESULTS_DIR/scen09.log
./runlim -r $TO -s $MO  python3 -u main.py scen10  2>&1 | tee $RESULTS_DIR/scen10.log
./runlim -r $TO -s $MO  python3 -u main.py TUD200.1  2>&1 | tee $RESULTS_DIR/TUD200.1.log
./runlim -r $TO -s $MO  python3 -u main.py TUD200.2  2>&1 | tee $RESULTS_DIR/TUD200.2.log
./runlim -r $TO -s $MO  python3 -u main.py TUD200.3  2>&1 | tee $RESULTS_DIR/TUD200.3.log
./runlim -r $TO -s $MO  python3 -u main.py TUD200.4  2>&1 | tee $RESULTS_DIR/TUD200.4.log
./runlim -r $TO -s $MO  python3 -u main.py TUD200.5  2>&1 | tee $RESULTS_DIR/TUD200.5.log
./runlim -r $TO -s $MO  python3 -u main.py TUD916.1  2>&1 | tee $RESULTS_DIR/TUD916.1.log
./runlim -r $TO -s $MO  python3 -u main.py TUD916.2  2>&1 | tee $RESULTS_DIR/TUD916.2.log
./runlim -r $TO -s $MO  python3 -u main.py TUD916.3  2>&1 | tee $RESULTS_DIR/TUD916.3.log
./runlim -r $TO -s $MO  python3 -u main.py TUD916.4  2>&1 | tee $RESULTS_DIR/TUD916.4.log
./runlim -r $TO -s $MO  python3 -u main.py TUD916.5  2>&1 | tee $RESULTS_DIR/TUD916.5.log


./runlim -r $TO -s $MO  python3 -u main_no.py graph01  2>&1 | tee $NO_RESULTS_DIR/graph01.log
./runlim -r $TO -s $MO  python3 -u main_no.py graph02  2>&1 | tee $NO_RESULTS_DIR/graph02.log
./runlim -r $TO -s $MO  python3 -u main_no.py graph08   2>&1 | tee $NO_RESULTS_DIR/graph08.log
./runlim -r $TO -s $MO  python3 -u main_no.py graph09  2>&1 | tee $NO_RESULTS_DIR/graph09.log
./runlim -r $TO -s $MO  python3 -u main_no.py graph14  2>&1 | tee $NO_RESULTS_DIR/graph14.log
./runlim -r $TO -s $MO  python3 -u main_no.py scen01  2>&1 | tee $NO_RESULTS_DIR/scen01.log
./runlim -r $TO -s $MO  python3 -u main_no.py scen02  2>&1 | tee $NO_RESULTS_DIR/scen02.log
./runlim -r $TO -s $MO  python3 -u main_no.py scen03  2>&1 | tee $NO_RESULTS_DIR/scen03.log
./runlim -r $TO -s $MO  python3 -u main_no.py scen04  2>&1 | tee $NO_RESULTS_DIR/scen04.log
./runlim -r $TO -s $MO  python3 -u main_no.py scen11  2>&1 | tee $NO_RESULTS_DIR/scen11.log 
./runlim -r $TO -s $MO  python3 -u main_no.py graph03  2>&1 | tee $NO_RESULTS_DIR/graph03.log
./runlim -r $TO -s $MO  python3 -u main_no.py graph04  2>&1 | tee $NO_RESULTS_DIR/graph04.log
./runlim -r $TO -s $MO  python3 -u main_no.py graph05  2>&1 | tee $NO_RESULTS_DIR/graph05.log
./runlim -r $TO -s $MO  python3 -u main_no.py graph06  2>&1 | tee $NO_RESULTS_DIR/graph06.log
./runlim -r $TO -s $MO  python3 -u main_no.py graph07  2>&1 | tee $NO_RESULTS_DIR/graph07.log
./runlim -r $TO -s $MO  python3 -u main_no.py graph10  2>&1 | tee $NO_RESULTS_DIR/graph10.log
./runlim -r $TO -s $MO  python3 -u main_no.py graph11  2>&1 | tee $NO_RESULTS_DIR/graph11.log
./runlim -r $TO -s $MO  python3 -u main_no.py graph12  2>&1 | tee $NO_RESULTS_DIR/graph12.log
./runlim -r $TO -s $MO  python3 -u main_no.py graph13  2>&1 | tee $NO_RESULTS_DIR/graph13.log
./runlim -r $TO -s $MO  python3 -u main_no.py scen05  2>&1 | tee $NO_RESULTS_DIR/scen05.log
./runlim -r $TO -s $MO  python3 -u main_no.py scen06  2>&1 | tee $NO_RESULTS_DIR/scen06.log
./runlim -r $TO -s $MO  python3 -u main_no.py scen07  2>&1 | tee $NO_RESULTS_DIR/scen07.log
./runlim -r $TO -s $MO  python3 -u main_no.py scen08  2>&1 | tee $NO_RESULTS_DIR/scen08.log
./runlim -r $TO -s $MO  python3 -u main_no.py scen09  2>&1 | tee $NO_RESULTS_DIR/scen09.log
./runlim -r $TO -s $MO  python3 -u main_no.py scen10  2>&1 | tee $NO_RESULTS_DIR/scen10.log
./runlim -r $TO -s $MO  python3 -u main_no.py TUD200.1  2>&1 | tee $NO_RESULTS_DIR/TUD200.1.log
./runlim -r $TO -s $MO  python3 -u main_no.py TUD200.2  2>&1 | tee $NO_RESULTS_DIR/TUD200.2.log
./runlim -r $TO -s $MO  python3 -u main_no.py TUD200.3  2>&1 | tee $NO_RESULTS_DIR/TUD200.3.log
./runlim -r $TO -s $MO  python3 -u main_no.py TUD200.4  2>&1 | tee $NO_RESULTS_DIR/TUD200.4.log
./runlim -r $TO -s $MO  python3 -u main_no.py TUD200.5  2>&1 | tee $NO_RESULTS_DIR/TUD200.5.log
./runlim -r $TO -s $MO  python3 -u main_no.py TUD916.1  2>&1 | tee $NO_RESULTS_DIR/TUD916.1.log
./runlim -r $TO -s $MO  python3 -u main_no.py TUD916.2  2>&1 | tee $NO_RESULTS_DIR/TUD916.2.log
./runlim -r $TO -s $MO  python3 -u main_no.py TUD916.3  2>&1 | tee $NO_RESULTS_DIR/TUD916.3.log
./runlim -r $TO -s $MO  python3 -u main_no.py TUD916.4  2>&1 | tee $NO_RESULTS_DIR/TUD916.4.log 
./runlim -r $TO -s $MO  python3 -u main_no.py TUD916.5  2>&1 | tee $NO_RESULTS_DIR/TUD916.5.log


