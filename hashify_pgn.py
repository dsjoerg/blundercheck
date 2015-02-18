#!/usr/bin/env python

import chess.pgn, time, sys, djeval

game_num = 0
exporter = chess.pgn.StringExporter()
game = chess.pgn.read_game(sys.stdin)

while game is not None:
    game.headers['hash32'] = djeval.hash32(game)
    game.export(exporter, headers=True, variations=False, comments=False)
    game_num = game_num + 1
    if game_num % 1000 == 0:
        sys.stderr.write('.')
    game = chess.pgn.read_game(sys.stdin, None)

print str(exporter)
