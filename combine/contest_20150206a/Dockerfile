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

# boto config with our AWS keys
ADD config/boto.cfg /etc/boto.cfg

CMD python

# DO NOT REMOVE THIS STEP
# IT ENSURES THAT WHEN WE MAKE A SUBMISSION CANDIDATE, WE'VE BUILT IT FROM SCRATCH
ADD submit_build_times.txt /root/src

# pystockfish
RUN pip install -e git+git://github.com/dsjoerg/pystockfish#egg=pystockfish
RUN pip install -e git+git@github.com:dsjoerg/blundercheck#egg=blundercheck

ENV CLUSTER_INPUT_FILE 20150203.json.zl

ADD $CLUSTER_INPUT_FILE /data/

WORKDIR /home/beaker/src/src/blundercheck

#RUN echo 'hello world'
#RUN 'wc -l /data/20150203.json.zl'

RUN data_prep/extract_movescores.py /data/$CLUSTER_INPUT_FILE > /data/movescores.csv

# NEXT RERUN: MOVE THIS UP
ADD data.pgn /data/
# AND KILL THIS
RUN pip install -U git+git@github.com:dsjoerg/blundercheck#egg=blundercheck

RUN data_prep/make_eheaders.py < /data/data.pgn > /data/eheaders.p
RUN data_prep/make_moves_csv.py /data/$CLUSTER_INPUT_FILE > /data/moves.csv
RUN data_prep/make_depth_aggregates_csv.py < /data/moves.csv > /data/depthstats.csv

# DEVELOPMENT
#ENV PYTHONPATH /root/src/pystockfish:/root/src/blundercheck

