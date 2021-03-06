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

# DO NOT REMOVE THIS STEP
# IT ENSURES THAT WHEN WE MAKE A SUBMISSION CANDIDATE, WE'VE BUILT IT FROM SCRATCH
ADD submit_build_times.txt /root/src

# software we've modified
RUN pip install -e git+git@github.com:dsjoerg/scikit-learn@0.15.X#egg=scikit-learn
RUN pip install -e git+git://github.com/dsjoerg/pystockfish#egg=pystockfish
RUN pip install -e git+git@github.com:dsjoerg/blundercheck#egg=blundercheck

# CONFIGURE INPUT
ENV CLUSTER_INPUT_FILE 20150203.json.zl

# COPY DATA IN FROM THE OUTSIDE WORLD
# TODO pull this from a URL instead to make Docker build startup faster
ADD $CLUSTER_INPUT_FILE /data/
ADD data.pgn /data/

ENV PATH /home/beaker/src/src/blundercheck/data_prep:$PATH
ENV PATH /home/beaker/src/src/blundercheck/modeling:$PATH

RUN extract_movescores.py /data/$CLUSTER_INPUT_FILE > /data/movescores.csv

RUN make_eheaders.py /data/data.pgn > /data/eheaders.p
RUN make_moves_csv.py /data/$CLUSTER_INPUT_FILE > /data/moves.csv
RUN make_depth_aggregates_csv.py < /data/moves.csv > /data/depthstats.csv

# TODO remove me when doing an earlier step
RUN echo 'not yet 123'
RUN pip install -e git+git@github.com:dsjoerg/blundercheck#egg=blundercheck

# prepare movedata for modeling
RUN cat /data/moves.csv | prepare_movemodel.py /data/movedata.p

# TODO remove me when doing an earlier step
RUN echo 'not yet'
RUN pip install -e git+git@github.com:dsjoerg/blundercheck#egg=blundercheck

# then play with the movemodel and make N versions for later cross-validation
RUN fit_movemodel.py /data/movedata.p /data/movemodel.p
RUN show_movemodel.py /data/movemodel.p

# TODO remove me when doing an earlier step
RUN echo 'not yet piano12'
RUN pip install -e git+git@github.com:dsjoerg/blundercheck#egg=blundercheck

# compute_opening_count also
# TODO remove this when you re-run the earlier make_eheaders.py step
RUN make_eheaders.py /data/data.pgn > /data/eheaders2.p

# copy stockfish.csv in to the container
RUN wget -O /data/stockfish.csv https://s3.amazonaws.com/bc-games/first/stockfish.csv
# the following was getting run every time
#ADD https://s3.amazonaws.com/bc-games/first/stockfish.csv /data/

# TODO remove me when doing an earlier step
RUN echo 'not yet 12345678'
RUN pip install -e git+git@github.com:dsjoerg/blundercheck#egg=blundercheck

# read everything in to memory, compute additional columns and write out yy_df to disk
RUN prepare_pgmodel.py /data/yy_df.p

# TODO remove me when doing an earlier step
RUN echo 'not yet 1234'
RUN pip install -e git+git@github.com:dsjoerg/blundercheck#egg=blundercheck

# read in yy_df, train a linear model, dump some stats about it
RUN fit_linear_pgmodel.py /data/yy_df.p

# TODO remove me when doing an earlier step
RUN echo 'not yet 08'
RUN pip install -e git+git@github.com:dsjoerg/blundercheck#egg=blundercheck

# read in yy_df, train a gradientboosting model, dump some stats about it and write a submission.
RUN fit_gbr_pgmodel.py /data/yy_df.p /data/gbr_pgmodel.p

# TODO remove me when doing an earlier step
RUN echo 'not yet 0'
RUN pip install -e git+git@github.com:dsjoerg/blundercheck#egg=blundercheck

# show more about the GBR model
RUN show_gbrmodel.py /data/gbr_pgmodel.p
