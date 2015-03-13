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

# ipython hooray
RUN pip install "ipython[notebook]"
EXPOSE 8888
ADD notebook.sh /
RUN chmod u+x /notebook.sh
ENV PEM_FILE /key.pem
# $PASSWORD will get `unset` within notebook.sh, turned into an IPython style hash
ENV PASSWORD Dont make this your default
ENV USE_HTTP 0

# aws fun
RUN pip install awscli
ADD config/boto.cfg /root/.aws/credentials

# CONFIGURE CODE DIRS
ENV BLUNDERCHECK_DIR /home/beaker/src/src/blundercheck
ENV PATH $BLUNDERCHECK_DIR/data_prep:$PATH
ENV PATH $BLUNDERCHECK_DIR/modeling:$PATH

# BRING IN THE CODE
RUN echo 'thurs01234'
ADD data_prep/make_eheaders.py $BLUNDERCHECK_DIR/data_prep/
ADD data_prep/make_moves_csv.py $BLUNDERCHECK_DIR/data_prep/
ADD data_prep/extract_movescores_from_gz.py $BLUNDERCHECK_DIR/data_prep/
ADD data_prep/prepare_movemodel.py $BLUNDERCHECK_DIR/data_prep/
ADD modeling/fit_movemodel.py $BLUNDERCHECK_DIR/modeling/
ADD modeling/show_movemodel.py $BLUNDERCHECK_DIR/modeling/
ADD modeling/use_movemodel.py $BLUNDERCHECK_DIR/modeling/
ADD modeling/compute_moveaggs.py $BLUNDERCHECK_DIR/modeling/
ADD data_prep/make_depth_aggregates_csv.py $BLUNDERCHECK_DIR/data_prep/
ADD data_prep/make_material_aggregates.py $BLUNDERCHECK_DIR/data_prep/
ADD modeling/fit_errorchunk_models.py $BLUNDERCHECK_DIR/modeling/
ADD modeling/compute_chunklikes.py $BLUNDERCHECK_DIR/modeling/
ADD data_prep/crunch_movescores.py $BLUNDERCHECK_DIR/data_prep/
ADD data_prep/prepare_pgmodel.py $BLUNDERCHECK_DIR/data_prep/
ADD data_prep/show_pgdata.py $BLUNDERCHECK_DIR/data_prep/
ADD modeling/fit_linear_pgmodel.py $BLUNDERCHECK_DIR/modeling/
ADD modeling/fit_rfr_pgmodel.py $BLUNDERCHECK_DIR/modeling/
ADD data_prep/make_scatterplots.py $BLUNDERCHECK_DIR/data_prep/
ADD data_prep/enhance_entry.py $BLUNDERCHECK_DIR/data_prep/
ADD data_prep/masked_entry.py $BLUNDERCHECK_DIR/data_prep/
ADD data_prep/show_a_game.py $BLUNDERCHECK_DIR/data_prep/
ADD data_prep/show_one_game.py $BLUNDERCHECK_DIR/data_prep/
ADD data_prep/extract_gb_csv.py $BLUNDERCHECK_DIR/data_prep/
ADD data_prep/fit_model.sh $BLUNDERCHECK_DIR/data_prep/
ADD data_prep/consolidate_zls_to_gz.py $BLUNDERCHECK_DIR/data_prep/

RUN mkdir /data
ADD data_prep/pull_and_push.sh $BLUNDERCHECK_DIR/data_prep/
