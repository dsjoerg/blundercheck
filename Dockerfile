FROM dockerfile/ubuntu

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

# pystockfish
RUN pip install -e git+git://github.com/dsjoerg/pystockfish#egg=pystockfish

# boto config with our AWS keys
ADD config/boto.cfg /etc/boto.cfg

CMD python /root/src/blundercheck/scoreserver_launcher.py

RUN echo '1234567'

RUN pip install -e git+git@github.com:dsjoerg/blundercheck#egg=blundercheck


# DEVELOPMENT
#ENV PYTHONPATH /root/src/pystockfish:/root/src/blundercheck

# PYPY.  why not run faster?
# 20150130 BECAUSE ITS A PAIN IN THE ASS WORKING WITH PYPY!
#
# AFTER NEARLY AN HOUR DEALING WITH A SERIES OF "MINOR ISSUES"...
#
# IN PARTICULAR, THEY RECOMMEND USING VIRTUALENV AND YOU HAVE TO RE-INSTALL MODULES,
# AND VIRTUALENV IS A ROYAL PAIN IN THE ASS AND I CANT TELL HOW MUCH FURTHER DOWN THIS
# RATHOLE I HAVE TO GO BEFORE SOMETHING WORKS.
#
#RUN add-apt-repository -y ppa:pypy/ppa && apt-get update && apt-get -y install pypy
#curl https://raw.github.com/pypa/pip/master/contrib/get-pip.py | pypy
#pypy pip install python-chess
