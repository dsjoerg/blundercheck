#!/bin/bash -x

RESULTDIR=$(date +%Y%m%d%H%M%S)-$HOSTNAME
mkdir /data/results-$RESULTDIR


wget -O /data/data.pgn https://s3.amazonaws.com/bc-games/kaggle/data.pgn
wget -O /data/stockfish.csv https://s3.amazonaws.com/bc-games/first/stockfish.csv
wget -O - https://s3.amazonaws.com/bc-runoutputs/$CLUSTER_INPUT_FILE > /data/$CLUSTER_INPUT_FILE

# data from OM GOLEM
wget -O /data/data.pgn.eloscored21 https://s3.amazonaws.com/bc-runoutputs/data100k.pgn.golemelos.21
wget -O /data/data.pgn.eloscored4 https://s3.amazonaws.com/bc-runoutputs/data100k.pgn.golemelos.4
wget -O /data/data.pgn.eloscored10 https://s3.amazonaws.com/bc-runoutputs/data100k.pgn.golemelos.10

# data used for enhancing entry
# TODO instead of downloading this, could use your extract_elos.py
wget -O /data/data25k.pgn.elos https://s3.amazonaws.com/bc-games/data25k.pgn.elos
# TODO instead of downloading this, could run polyglot in elo-book -exact-match mode
# HOWEVER YOU HAVE TO POST-FILTER IT, BECAUSE elo_book.cpp has changed and spits out all events, not just those >25k
wget -O /data/certain_elos https://s3.amazonaws.com/bc-games/certain_elos

# guid-bratko runs
wget -O /data/gb1-25.gz https://s3.amazonaws.com/bc-runoutputs/20150308.25k.gz
wget -O /data/gb25-50.gz https://s3.amazonaws.com/bc-runoutputs/20150313-k2550.gz

# timecontrol for the 25k, not used in modeling, but strictly in
# show_one.py and other diagnostic tools
wget -O /data/timecontrols.txt https://s3.amazonaws.com/bc-runinputs/timecontrols.txt

######## NOT CURRENTLY USED STUFF ########
# an old run that had good depth (and caching?)
#wget -O - https://s3.amazonaws.com/bc-runoutputs/20150203.json.zl > /data/20150203.json.zl
# make data.pgn hold another 50k matches from chesstempo
#wget -O /data/ct-201234.csn50k.pgn https://s3.amazonaws.com/bc-games/first/ct-201234.csn50k.pgn
#cat /data/ct-201234.csn50k.pgn >> /data/data.pgn
##########################################


extract_gb_csv.py /data/gb25-50.gz > /data/gb.csv
extract_gb_csv_noslice.py /data/gb1-25.gz >> /data/gb.csv
make_eheaders.py /data/data.pgn > /data/eheaders.p
make_moves_csv.py /data/$CLUSTER_INPUT_FILE > /data/moves.csv
extract_movescores_from_gz.py /data/$CLUSTER_INPUT_FILE > /data/movescores.csv
cat /data/moves.csv | prepare_movemodel.py /data/movedata.p
fit_movemodel.py /data/movedata.p /data/movemodel.p
show_movemodel.py /data/movemodel.p
use_movemodel.py /data/movedata.p /data/movemodel.p
compute_moveaggs.py /data/movedata.p
make_depth_aggregates_csv.py < /data/moves.csv > /data/depthstats.csv
make_material_aggregates.py /data/moves.csv > /data/material.csv

if [ $DO_ERRORCHUNK -eq 1 ]
   then
       fit_errorchunk_models.py $NUM_ELO_GROUPS $NUM_ERRORCHUNKS $NUM_ESTIMATORS 15 100 /data/errorchunks/
       compute_chunklikes.py /data/errorchunks/
fi

crunch_movescores.py /data/crunched.csv $NUMGAMES
prepare_pgmodel.py /data/crunched.csv /data/gb.csv /data/yy_df.p
show_pgdata.py /data/yy_df.p
# standardize /data/yy_df.p
fit_linear_pgmodel.py /data/yy_df.p
fit_rfr_pgmodel.py /data/yy_df.p /data/rfr_pgmodel.p | tee /data/results-$RESULTDIR/rfr.stdout
#make_scatterplots.py /data/yy_df.p
enhance_entry.py /data/data25k.pgn.elos /data/certain_elos /data/submission_rfr.csv > /data/submission_enhanced.csv
masked_entry.py 25001 37500 < /data/submission_enhanced.csv > /data/submission_1H.csv
masked_entry.py 37501 50001 < /data/submission_enhanced.csv > /data/submission_2H.csv

cp /data/submission*.csv /data/results-$RESULTDIR
printenv > /data/results-$RESULTDIR/env.txt
aws s3 mb s3://bc-runoutputs/results-$RESULTDIR
aws s3 sync /data/results-$RESULTDIR s3://bc-runoutputs/results-$RESULTDIR
