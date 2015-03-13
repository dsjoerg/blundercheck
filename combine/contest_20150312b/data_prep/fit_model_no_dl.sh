#!/bin/bash

if [ 1 -eq 0 ]; then
    echo 'yo'
make_eheaders.py /data/data.pgn > /data/eheaders.p
make_moves_csv.py /data/$CLUSTER_INPUT_FILE > /data/moves.csv
extract_movescores_from_gz.py /data/$CLUSTER_INPUT_FILE > /data/movescores.csv
extract_gb_csv.py /data/$CLUSTER_INPUT_FILE > /data/gb.csv
cat /data/moves.csv | prepare_movemodel.py /data/movedata.p
fit_movemodel.py /data/movedata.p /data/movemodel.p
show_movemodel.py /data/movemodel.p
use_movemodel.py /data/movedata.p /data/movemodel.p
compute_moveaggs.py /data/movedata.p
make_depth_aggregates_csv.py < /data/moves.csv > /data/depthstats.csv
make_material_aggregates.py /data/moves.csv > /data/material.csv
#fit_errorchunk_models.py 2 3 1000 15 100 /data/errorchunks/
#compute_chunklikes.py /data/errorchunks/
fi

crunch_movescores.py /data/crunched.csv 25000
foo/data_prep/prepare_pgmodel.py /data/crunched.csv /data/gb.csv /data/yy_df.p
foo/data_prep/standardize.py /data/yy_df.p
show_pgdata.py /data/yy_df.p
foo/modeling/fit_linear_pgmodel.py /data/yy_df.p
foo/modeling/fit_rfr_pgmodel.py /data/yy_df.p /data/rfr_pgmodel.p
#make_scatterplots.py /data/yy_df.p
enhance_entry.py /data/data25k.pgn.elos /data/certain_elos /data/submission_rfr.csv > /data/submission_enhanced.csv
masked_entry.py 25001 37500 < /data/submission_enhanced.csv > /data/submission_1H.csv
masked_entry.py 37501 50001 < /data/submission_enhanced.csv > /data/submission_2H.csv
