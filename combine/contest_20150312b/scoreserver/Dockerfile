FROM ubuntu:14.04

# My stuff
RUN apt-get -y update && apt-get -y upgrade && apt-get -y install \
    python \
    make \
    gcc \
    python-dev \
    python-pip

# boto
RUN pip install boto

RUN apt-get -y install git

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
RUN cd /usr/src && git clone -b blundercheck git://github.com/dsjoerg/Stockfish.git && cd Stockfish/src && make build ARCH=x86-64 && ln -sr stockfish /usr/local/bin

# python-chess
RUN pip install python-chess

# boto config with our AWS keys
ADD config/boto.cfg /etc/boto.cfg

CMD python /src/blundercheck/scoreserver_launcher.py

RUN echo 'thursday0'
RUN pip install -e git+git://github.com/dsjoerg/pystockfish#egg=pystockfish
RUN pip install -e git+git@github.com:dsjoerg/blundercheck#egg=blundercheck

ENV PYTHONPATH /root/src/pystockfish
