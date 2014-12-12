FROM dockerfile/ubuntu

# My stuff
RUN apt-get -y update && apt-get -y upgrade && apt-get -y install \
    python \
    make \
    gcc \
    python-dev \
    python-pip

# Stockfish
RUN cd /usr/src && git clone git://github.com/official-stockfish/Stockfish.git && cd Stockfish/src && make build ARCH=x86-64 && ln -sr stockfish /usr/local/bin

# python-chess
RUN pip install python-chess

# pystockfish
# RUN cd /usr/src && git clone git://github.com/llimllib/pystockfish
RUN pip install -e git+git://github.com/llimllib/pystockfish#egg=pystockfish

# Clean up APT when done.
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
