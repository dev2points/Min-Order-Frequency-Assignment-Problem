TO=600
MO=14000

RESULT=results/preprocessing/nsc_assumptions 
mkdir -p $RESULT

NO_RESULT=results/no_pre_processing/nsc_assumptions 
mkdir -p $NO_RESULT



./runlim -r $TO -s $MO  python3 -u pairwise.py scen01  assumptions 2>&1 | tee $RESULT/scen01.log
./runlim -r $TO -s $MO  python3 -u pairwise.py scen02  assumptions 2>&1 | tee $RESULT/scen02.log
./runlim -r $TO -s $MO  python3 -u pairwise.py scen03  assumptions 2>&1 | tee $RESULT/scen03.log
./runlim -r $TO -s $MO  python3 -u pairwise.py scen04  assumptions 2>&1 | tee $RESULT/scen04.log
./runlim -r $TO -s $MO  python3 -u pairwise.py scen11  assumptions 2>&1 | tee $RESULT/scen11.log
./runlim -r $TO -s $MO  python3 -u pairwise.py graph01  assumptions 2>&1 | tee $RESULT/graph01.log
./runlim -r $TO -s $MO  python3 -u pairwise.py graph02  assumptions 2>&1 | tee $RESULT/graph02.log
./runlim -r $TO -s $MO  python3 -u pairwise.py graph08  assumptions 2>&1 | tee $RESULT/graph08.log
./runlim -r $TO -s $MO  python3 -u pairwise.py graph09  assumptions 2>&1 | tee $RESULT/graph09.log
./runlim -r $TO -s $MO  python3 -u pairwise.py graph14  assumptions 2>&1 | tee $RESULT/graph14.log

./runlim -r $TO -s $MO  python3 -u pairwise.py graph03  assumptions 2>&1 | tee $RESULT/graph03.log
./runlim -r $TO -s $MO  python3 -u pairwise.py graph04  assumptions 2>&1 | tee $RESULT/graph04.log
./runlim -r $TO -s $MO  python3 -u pairwise.py graph05  assumptions 2>&1 | tee $RESULT/graph05.log
./runlim -r $TO -s $MO  python3 -u pairwise.py graph06  assumptions 2>&1 | tee $RESULT/graph06.log
./runlim -r $TO -s $MO  python3 -u pairwise.py graph07  assumptions 2>&1 | tee $RESULT/graph07.log
./runlim -r $TO -s $MO  python3 -u pairwise.py graph10  assumptions 2>&1 | tee $RESULT/graph10.log
./runlim -r $TO -s $MO  python3 -u pairwise.py graph11  assumptions 2>&1 | tee $RESULT/graph11.log
./runlim -r $TO -s $MO  python3 -u pairwise.py graph12  assumptions 2>&1 | tee $RESULT/graph12.log
./runlim -r $TO -s $MO  python3 -u pairwise.py graph13  assumptions 2>&1 | tee $RESULT/graph13.log
./runlim -r $TO -s $MO  python3 -u pairwise.py scen05  assumptions 2>&1 | tee $RESULT/scen05.log
./runlim -r $TO -s $MO  python3 -u pairwise.py scen06  assumptions 2>&1 | tee $RESULT/scen06.log
./runlim -r $TO -s $MO  python3 -u pairwise.py scen07  assumptions 2>&1 | tee $RESULT/scen07.log
./runlim -r $TO -s $MO  python3 -u pairwise.py scen08  assumptions 2>&1 | tee $RESULT/scen08.log
./runlim -r $TO -s $MO  python3 -u pairwise.py scen09  assumptions 2>&1 | tee $RESULT/scen09.log
./runlim -r $TO -s $MO  python3 -u pairwise.py scen10  assumptions 2>&1 | tee $RESULT/scen10.log
./runlim -r $TO -s $MO  python3 -u pairwise.py TUD200.1  assumptions 2>&1 | tee $RESULT/TUD200.1.log
./runlim -r $TO -s $MO  python3 -u pairwise.py TUD200.2  assumptions 2>&1 | tee $RESULT/TUD200.2.log
./runlim -r $TO -s $MO  python3 -u pairwise.py TUD200.3  assumptions 2>&1 | tee $RESULT/TUD200.3.log
./runlim -r $TO -s $MO  python3 -u pairwise.py TUD200.4  assumptions 2>&1 | tee $RESULT/TUD200.4.log
./runlim -r $TO -s $MO  python3 -u pairwise.py TUD200.5  assumptions 2>&1 | tee $RESULT/TUD200.5.log
./runlim -r $TO -s $MO  python3 -u pairwise.py TUD916.1  assumptions 2>&1 | tee $RESULT/TUD916.1.log
./runlim -r $TO -s $MO  python3 -u pairwise.py TUD916.2  assumptions 2>&1 | tee $RESULT/TUD916.2.log
./runlim -r $TO -s $MO  python3 -u pairwise.py TUD916.3  assumptions 2>&1 | tee $RESULT/TUD916.3.log
./runlim -r $TO -s $MO  python3 -u pairwise.py TUD916.4  assumptions 2>&1 | tee $RESULT/TUD916.4.log
./runlim -r $TO -s $MO  python3 -u pairwise.py TUD916.5  assumptions 2>&1 | tee $RESULT/TUD916.5.log





./runlim -r $TO -s $MO  python3 -u pairwise_no_preprocessing.py scen01  assumptions 2>&1 | tee $NO_RESULT/scen01.log
./runlim -r $TO -s $MO  python3 -u pairwise_no_preprocessing.py scen02  assumptions 2>&1 | tee $NO_RESULT/scen02.log
./runlim -r $TO -s $MO  python3 -u pairwise_no_preprocessing.py scen03  assumptions 2>&1 | tee $NO_RESULT/scen03.log
./runlim -r $TO -s $MO  python3 -u pairwise_no_preprocessing.py scen04  assumptions 2>&1 | tee $NO_RESULT/scen04.log
./runlim -r $TO -s $MO  python3 -u pairwise_no_preprocessing.py scen11  assumptions 2>&1 | tee $NO_RESULT/scen11.log
./runlim -r $TO -s $MO  python3 -u pairwise_no_preprocessing.py graph01  assumptions 2>&1 | tee $NO_RESULT/graph01.log
./runlim -r $TO -s $MO  python3 -u pairwise_no_preprocessing.py graph02  assumptions 2>&1 | tee $NO_RESULT/graph02.log
./runlim -r $TO -s $MO  python3 -u pairwise_no_preprocessing.py graph08  assumptions 2>&1 | tee $NO_RESULT/graph08.log
./runlim -r $TO -s $MO  python3 -u pairwise_no_preprocessing.py graph09  assumptions 2>&1 | tee $NO_RESULT/graph09.log
./runlim -r $TO -s $MO  python3 -u pairwise_no_preprocessing.py graph14  assumptions 2>&1 | tee $NO_RESULT/graph14.log

./runlim -r $TO -s $MO  python3 -u pairwise_no_preprocessing.py graph03  assumptions 2>&1 | tee $NO_RESULT/graph03.log
./runlim -r $TO -s $MO  python3 -u pairwise_no_preprocessing.py graph04  assumptions 2>&1 | tee $NO_RESULT/graph04.log
./runlim -r $TO -s $MO  python3 -u pairwise_no_preprocessing.py graph05  assumptions 2>&1 | tee $NO_RESULT/graph05.log
./runlim -r $TO -s $MO  python3 -u pairwise_no_preprocessing.py graph06  assumptions 2>&1 | tee $NO_RESULT/graph06.log
./runlim -r $TO -s $MO  python3 -u pairwise_no_preprocessing.py graph07  assumptions 2>&1 | tee $NO_RESULT/graph07.log
./runlim -r $TO -s $MO  python3 -u pairwise_no_preprocessing.py graph10  assumptions 2>&1 | tee $NO_RESULT/graph10.log
./runlim -r $TO -s $MO  python3 -u pairwise_no_preprocessing.py graph11  assumptions 2>&1 | tee $NO_RESULT/graph11.log
./runlim -r $TO -s $MO  python3 -u pairwise_no_preprocessing.py graph12  assumptions 2>&1 | tee $NO_RESULT/graph12.log
./runlim -r $TO -s $MO  python3 -u pairwise_no_preprocessing.py graph13  assumptions 2>&1 | tee $NO_RESULT/graph13.log
./runlim -r $TO -s $MO  python3 -u pairwise_no_preprocessing.py scen05  assumptions 2>&1 | tee $NO_RESULT/scen05.log
./runlim -r $TO -s $MO  python3 -u pairwise_no_preprocessing.py scen06  assumptions 2>&1 | tee $NO_RESULT/scen06.log
./runlim -r $TO -s $MO  python3 -u pairwise_no_preprocessing.py scen07  assumptions 2>&1 | tee $NO_RESULT/scen07.log
./runlim -r $TO -s $MO  python3 -u pairwise_no_preprocessing.py scen08  assumptions 2>&1 | tee $NO_RESULT/scen08.log
./runlim -r $TO -s $MO  python3 -u pairwise_no_preprocessing.py scen09  assumptions 2>&1 | tee $NO_RESULT/scen09.log
./runlim -r $TO -s $MO  python3 -u pairwise_no_preprocessing.py scen10  assumptions 2>&1 | tee $NO_RESULT/scen10.log
./runlim -r $TO -s $MO  python3 -u pairwise_no_preprocessing.py TUD200.1  assumptions 2>&1 | tee $NO_RESULT/TUD200.1.log
./runlim -r $TO -s $MO  python3 -u pairwise_no_preprocessing.py TUD200.2  assumptions 2>&1 | tee $NO_RESULT/TUD200.2.log
./runlim -r $TO -s $MO  python3 -u pairwise_no_preprocessing.py TUD200.3  assumptions 2>&1 | tee $NO_RESULT/TUD200.3.log
./runlim -r $TO -s $MO  python3 -u pairwise_no_preprocessing.py TUD200.4  assumptions 2>&1 | tee $NO_RESULT/TUD200.4.log
./runlim -r $TO -s $MO  python3 -u pairwise_no_preprocessing.py TUD200.5  assumptions 2>&1 | tee $NO_RESULT/TUD200.5.log
./runlim -r $TO -s $MO  python3 -u pairwise_no_preprocessing.py TUD916.1  assumptions 2>&1 | tee $NO_RESULT/TUD916.1.log
./runlim -r $TO -s $MO  python3 -u pairwise_no_preprocessing.py TUD916.2  assumptions 2>&1 | tee $NO_RESULT/TUD916.2.log
./runlim -r $TO -s $MO  python3 -u pairwise_no_preprocessing.py TUD916.3  assumptions 2>&1 | tee $NO_RESULT/TUD916.3.log
./runlim -r $TO -s $MO  python3 -u pairwise_no_preprocessing.py TUD916.4  assumptions 2>&1 | tee $NO_RESULT/TUD916.4.log
./runlim -r $TO -s $MO  python3 -u pairwise_no_preprocessing.py TUD916.5  assumptions 2>&1 | tee $NO_RESULT/TUD916.5.log

