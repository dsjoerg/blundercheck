#!env python

import chess.pgn, urllib, os, sys
from sqlalchemy import create_engine, MetaData, Table, text
from sqlalchemy.orm import mapper, sessionmaker

class Sources(object):
    pass


t = text("""
insert into game (source_id, source_ref, white_elo, black_elo, eco, result, white_computer, black_computer)
values (:source_id, :source_ref, :white_elo, :black_elo, :eco, :result, :white_computer, :black_computer)""")

results = {'0-1': -1,
           '1-0': 1}

def insert_game(game):
    result = 0
    if game.headers['Result'] in results:
        result = results[game.headers['Result']]

    if 'BlackIsComp' in game.headers and game.headers['BlackIsComp'] == 'Yes':
        black_computer = 1
    else:
        black_computer = 0

    if 'WhiteIsComp' in game.headers and game.headers['WhiteIsComp'] == 'Yes':
        white_computer = 1
    else:
        white_computer = 0

    result = connection.execute(t, source_id=1,
                                source_ref=game.headers['FICSGamesDBGameNo'],
                                white_elo=int(game.headers['WhiteElo']),
                                black_elo=int(game.headers['BlackElo']),
                                eco=game.headers['ECO'],
                                result=result,
                                white_computer=white_computer,
                                black_computer=black_computer)
    sys.stdout.write('.')

    # TODO check that a row was inserted
    # TODO dont re-insert the row if it already exists.  update?  barf?



host = os.environ['DB_HOST']
mysql_engine_string = "mysql://root@%s/bc" % (host)
engine = create_engine(mysql_engine_string)
connection = engine.connect()

urlfd = urllib.urlopen(sys.argv[1])
game = chess.pgn.read_game(urlfd)

while game is not None:
    insert_game(game)
    game = chess.pgn.read_game(urlfd)

print "Done"
