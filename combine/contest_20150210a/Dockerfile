FROM beakernotebook/beaker
# probably https://github.com/twosigma/beaker-notebook/blob/v1.1.1/Dockerfile

# My stuff
RUN apt-get -y update && apt-get -y upgrade && apt-get -y install \
    python \
    make \
    gcc \
    python-dev \
    python-pip \
    libmysqlclient-dev

# boto
RUN pip install boto

# sqlalchemy
RUN pip install sqlalchemy
RUN pip install MySQL-python

# pandas yay
RUN pip install pandas

# SSH git fun from http://stackoverflow.com/questions/23391839/clone-private-git-repo-with-dockerfile/25977750#25977750
ADD config/repo-key /
RUN \
  chmod 600 /repo-key && \  
  echo "IdentityFile /repo-key" >> /etc/ssh/ssh_config && \  
  echo "StrictHostKeyChecking no" >> /etc/ssh/ssh_config

# to do various networking tests
RUN apt-get install telnet

# Clean up APT when done.
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Stockfish
RUN cd /usr/src && git clone git://github.com/official-stockfish/Stockfish.git && cd Stockfish/src && make build ARCH=x86-64 && ln -sr stockfish /usr/local/bin

# python-chess
RUN pip install python-chess

# something with multiple regression dammit
RUN pip install -U scikit-learn
RUN pip install -U statsmodels
RUN pip install -U patsy

RUN apt-get -y update
RUN apt-get -y install python-pygraphviz
RUN apt-get -y install emacs

# boto config with our AWS keys
ADD config/boto.cfg /etc/boto.cfg

CMD python

# software we've modified
RUN pip install -e git+git@github.com:dsjoerg/scikit-learn@0.15.X#egg=scikit-learn
RUN pip install -e git+git://github.com/dsjoerg/pystockfish#egg=pystockfish
RUN pip install -e git+git@github.com:dsjoerg/blundercheck#egg=blundercheck

# CONFIGURE INPUT
ENV CLUSTER_INPUT_FILE 20150203.json.zl

# COPY DATA IN FROM THE OUTSIDE WORLD
RUN mkdir /data
RUN wget -O - https://s3.amazonaws.com/bc-runoutputs/$CLUSTER_INPUT_FILE > /data/$CLUSTER_INPUT_FILE
RUN wget -O /data/data.pgn https://s3.amazonaws.com/bc-games/kaggle/data.pgn
RUN wget -O /data/stockfish.csv https://s3.amazonaws.com/bc-games/first/stockfish.csv
# would have rather used ADD but the following was getting run every time instead of just once
#ADD https://s3.amazonaws.com/bc-games/first/stockfish.csv /data/

ENV BLUNDERCHECK_DIR /home/beaker/src/src/blundercheck
ENV PATH $BLUNDERCHECK_DIR/data_prep:$PATH
ENV PATH $BLUNDERCHECK_DIR/modeling:$PATH

RUN extract_movescores.py /data/$CLUSTER_INPUT_FILE > /data/movescores.csv

# TODO move this up
RUN pip install seaborn

RUN make_eheaders.py /data/data.pgn > /data/eheaders.p
RUN make_moves_csv.py /data/$CLUSTER_INPUT_FILE > /data/moves.csv
RUN make_depth_aggregates_csv.py < /data/moves.csv > /data/depthstats.csv

# make movemodel
RUN cat /data/moves.csv | prepare_movemodel.py /data/movedata.p

ADD modeling/fit_movemodel.py $BLUNDERCHECK_DIR/modeling/
RUN fit_movemodel.py /data/movedata.p /data/movemodel.p

ADD modeling/show_movemodel.py $BLUNDERCHECK_DIR/modeling/
RUN show_movemodel.py /data/movemodel.p

# prepare playergame data
ADD data_prep/prepare_pgmodel.py $BLUNDERCHECK_DIR/data_prep/
RUN prepare_pgmodel.py /data/yy_df.p

# read in yy_df, train a linear model, dump some stats about it
ADD modeling/fit_linear_pgmodel.py $BLUNDERCHECK_DIR/modeling/
RUN fit_linear_pgmodel.py /data/yy_df.p

# read in yy_df, train a gradientboosting model, dump some stats about it and write a submission.
ADD modeling/fit_gbr_pgmodel.py $BLUNDERCHECK_DIR/modeling/
RUN fit_gbr_pgmodel.py /data/yy_df.p /data/gbr_pgmodel.p

# show more about the GBR model
ADD data_prep/show_gbrmodel.py $BLUNDERCHECK_DIR/data_prep/
RUN show_gbrmodel.py /data/gbr_pgmodel.p

# create histograms of each variable and scatterplots of every pair of
# variables, so we can look through em and understand our data
ADD data_prep/make_scatterplots.py $BLUNDERCHECK_DIR/data_prep/
RUN make_scatterplots.py /data/yy_df.p
