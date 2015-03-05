#!/usr/bin/env python

import sys
import chess
import chess.pgn
import os


pgn_fd = open(sys.argv[1], 'r')
game_num = 50001
for line in pgn_fd:
    line = line.strip()
    if line.startswith('[Event'):
        print '[Event "%i"]' % game_num
        game_num = game_num + 1
        print line.replace('Event', 'RealEvent')
    else:
        print line


if False:

    game_num = 50001
    game = chess.pgn.read_game(pgn_fd)
    while game is not None:
        game.headers['RealEvent'] = game.headers['Event']
        game.headers['Event'] = game_num
        exporter = chess.pgn.StringExporter()
        game.export(exporter, headers=True, variations=False, comments=False)

        sys.stdout.write(str(exporter))
        sys.stdout.write('\n\n')
        sys.stdout.flush()
        game_num = game_num + 1
        game = None
        while game is None:
            try:
                game = chess.pgn.read_game(pgn_fd)
            except:
                pass
