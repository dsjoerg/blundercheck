FROM dockerfile/ubuntu

# My stuff
RUN apt-get -y update && apt-get -y upgrade && apt-get -y install \
    python \
    make \
    gcc \
    python-dev \
    python-pip \
    libmysqlclient-dev

# Stockfish
RUN cd /usr/src && git clone git://github.com/official-stockfish/Stockfish.git && cd Stockfish/src && make build ARCH=x86-64 && ln -sr stockfish /usr/local/bin

# python-chess
RUN pip install python-chess

# pystockfish
RUN pip install -e git+git://github.com/dsjoerg/pystockfish#egg=pystockfish

# boto
RUN pip install boto
ADD config/boto.cfg /etc/boto.cfg

# sqlalchemy
RUN pip install sqlalchemy
RUN pip install MySQL-python

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


# DEVELOPMENT
#ENV PYTHONPATH /root/src/pystockfish:/root/src/blundercheck

CMD python /root/src/blundercheck/scoreserver.py

RUN echo '1'

RUN pip install -e git+git@github.com:dsjoerg/blundercheck#egg=blundercheck



