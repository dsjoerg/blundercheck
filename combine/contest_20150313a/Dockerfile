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
RUN echo 'fri01234567890123456'
ADD data_prep/*.py $BLUNDERCHECK_DIR/data_prep/
ADD modeling/*.py $BLUNDERCHECK_DIR/modeling/
ADD data_prep/*.sh $BLUNDERCHECK_DIR/data_prep/

RUN mkdir /data
