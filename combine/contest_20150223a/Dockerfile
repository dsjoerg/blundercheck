FROM ubuntu:14.04

RUN apt-get -y update && apt-get -y upgrade && apt-get -y install \
    python \
    make \
    gcc \
    python-dev \
    python-pip \
    telnet \
    emacs \
    python-pygraphviz \
    python-matplotlib \
    python-scipy \
    git \
    wget

# nah this is too useful to kill
#RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN pip install boto
RUN pip install pandas
RUN pip install python-chess
RUN pip install -U statsmodels
RUN pip install -U patsy
RUN pip install seaborn

# SSH git fun from http://stackoverflow.com/questions/23391839/clone-private-git-repo-with-dockerfile/25977750#25977750
ADD config/repo-key /
RUN \
  chmod 600 /repo-key && \  
  echo "IdentityFile /repo-key" >> /etc/ssh/ssh_config && \  
  echo "StrictHostKeyChecking no" >> /etc/ssh/ssh_config

# Stockfish
RUN cd /usr/src && git clone git://github.com/official-stockfish/Stockfish.git && cd Stockfish/src && make build ARCH=x86-64 && ln -sr stockfish /usr/local/bin

# boto config with our AWS keys
ADD config/boto.cfg /etc/boto.cfg

CMD python

# software we've modified
RUN pip install -e git+git@github.com:dsjoerg/scikit-learn@0.15.X#egg=scikit-learn
RUN pip install -e git+git://github.com/dsjoerg/pystockfish#egg=pystockfish
RUN pip install -e git+git@github.com:dsjoerg/blundercheck#egg=blundercheck

# CONFIGURE INPUT
ENV CLUSTER_INPUT_FILE 20150211.json.zl



# COPY DATA IN FROM THE OUTSIDE WORLD
RUN mkdir /data
RUN wget -O - https://s3.amazonaws.com/bc-runoutputs/20150203.json.zl > /data/20150203.json.zl
RUN wget -O - https://s3.amazonaws.com/bc-runoutputs/$CLUSTER_INPUT_FILE > /data/$CLUSTER_INPUT_FILE
RUN wget -O /data/data.pgn https://s3.amazonaws.com/bc-games/kaggle/data.pgn
RUN wget -O /data/stockfish.csv https://s3.amazonaws.com/bc-games/first/stockfish.csv
ADD timecontrol.csv /data/

ENV BLUNDERCHECK_DIR /home/beaker/src/src/blundercheck
ENV PATH $BLUNDERCHECK_DIR/data_prep:$PATH
ENV PATH $BLUNDERCHECK_DIR/modeling:$PATH

ADD data_prep/extract_movescores.py $BLUNDERCHECK_DIR/data_prep/
RUN extract_movescores.py /data/$CLUSTER_INPUT_FILE > /data/movescores.csv

ADD data_prep/make_eheaders.py $BLUNDERCHECK_DIR/data_prep/
RUN make_eheaders.py /data/data.pgn > /data/eheaders.p

ADD data_prep/make_moves_csv.py $BLUNDERCHECK_DIR/data_prep/
RUN make_moves_csv.py /data/$CLUSTER_INPUT_FILE > /data/moves.csv

ADD data_prep/prepare_movemodel.py $BLUNDERCHECK_DIR/data_prep/
RUN cat /data/moves.csv | prepare_movemodel.py /data/movedata.p

# TODO move all this BS up
RUN pip install "ipython[notebook]"
EXPOSE 8888
ADD notebook.sh /
RUN chmod u+x /notebook.sh
ENV PEM_FILE /key.pem
# $PASSWORD will get `unset` within notebook.sh, turned into an IPython style hash
ENV PASSWORD Dont make this your default
ENV USE_HTTP 0

ADD modeling/fit_movemodel.py $BLUNDERCHECK_DIR/modeling/
RUN fit_movemodel.py /data/movedata.p /data/movemodel.p

ADD data_prep/show_a_game.py $BLUNDERCHECK_DIR/data_prep/
ADD data_prep/show_one_game.py $BLUNDERCHECK_DIR/data_prep/

ADD modeling/show_movemodel.py $BLUNDERCHECK_DIR/modeling/
RUN show_movemodel.py /data/movemodel.p

ADD data_prep/make_depth_aggregates_csv.py $BLUNDERCHECK_DIR/data_prep/
#RUN make_depth_aggregates_csv.py < /data/moves.csv > /data/depthstats.csv

# get the previous movescores, do they help?
#RUN extract_movescores.py /data/20150203.json.zl > /data/20150203_movescores.csv

# prepare playergame data
ADD data_prep/prepare_pgmodel.py $BLUNDERCHECK_DIR/data_prep/
#RUN prepare_pgmodel.py /data/yy_df.p

# TODO move this up one
ADD data_prep/show_pgdata.py $BLUNDERCHECK_DIR/data_prep/
#RUN show_pgdata.py /data/yy_df.p

# read in yy_df, train a linear model, dump some stats about it
ADD modeling/fit_linear_pgmodel.py $BLUNDERCHECK_DIR/modeling/
#RUN fit_linear_pgmodel.py /data/yy_df.p

ADD modeling/fit_rfr_pgmodel.py $BLUNDERCHECK_DIR/modeling/
#RUN fit_rfr_pgmodel.py /data/yy_df.p /data/rfr_pgmodel.p

# create histograms of each variable and scatterplots of every pair of
# variables, so we can look through em and understand our data
ADD data_prep/make_scatterplots.py $BLUNDERCHECK_DIR/data_prep/
#RUN make_scatterplots.py /data/yy_df.p


# TODO make CROSS VALIDATING step in RFR spit out the average of the three values
# TODO write moves_df back out at the end of fit_movemodel.py
# TODO add predict_move_elos() to fit_movemodel.py

RUN cd /usr/src && git clone git://github.com/strohel/PyBayes.git && cd PyBayes && ./setup.py install
RUN apt-get -y install libboost-all-dev
RUN cd /usr/src && git clone git://github.com/JohnLangford/vowpal_wabbit.git && cd vowpal_wabbit && make
RUN cd /usr/src/vowpal_wabbit && make vw && make library_example && make test
RUN cd /usr/src/vowpal_wabbit && sudo make install

ADD data_prep/prepare_vw_movemodel.py $BLUNDERCHECK_DIR/data_prep/
