#!/usr/bin/env python

import chess.pgn, time, sys, djeval
from collections import defaultdict

def games_equal(a, b):
    if (a.variations is None) != (b.variations is None):
        return False
    if (a.variations is None) and (b.variations is None):
        return True
    if (len(a.variations) != len(b.variations)):
        return False
    if (len(a.variations) == 0):
        return True
    if a.move != b.move:
        return False
    return games_equal(a.variations[0], b.variations[0])

def export_game(game):
    exporter = chess.pgn.StringExporter()
    game.export(exporter, headers=False, variations=False, comments=False)
    return str(exporter)

games = {}
def get_game(fd, offset):
    if (fd, offset) not in games:
        fd.seek(offset)
        game = chess.pgn.read_game(fd, None)
        games[(fd, offset)] = game
    return games[(fd, offset)]
    

game_num = 0
kaggle_fd = open(sys.argv[1], 'r')
kaggle_games = defaultdict(list)
for offset, headers in chess.pgn.scan_headers(kaggle_fd):
    if int(headers['hash32']) > 0:
        kaggle_games[headers['hash32']].append(offset)
    game_num = game_num + 1
    if game_num % 1000 == 0:
        sys.stderr.write('.')
#    if game_num > 50000:
#        break
sys.stderr.write('Done reading left games\n')


game_num = 0
num_hits = 0
hashmatchonly = 0
multimatch = 0
library_fd = open(sys.argv[2], 'r')
for offset, headers in chess.pgn.scan_headers(library_fd):
    if int(headers['hash32']) == 0:
        continue
    if headers['hash32'] in kaggle_games:
#        print 'header found, %i games, seeking... (Hash = %s)' % (len(kaggle_games[headers['hash32']]), headers['hash32'])
        our_game = get_game(library_fd, offset)
        matching_kaggle_games = []
        for koffset in kaggle_games[headers['hash32']]:
            kaggle_game = get_game(kaggle_fd, koffset)
            if games_equal(our_game, kaggle_game):
                num_hits = num_hits + 1
                matching_kaggle_games.append(kaggle_game.headers)
        if len(matching_kaggle_games) == 0:
            hashmatchonly = hashmatchonly + 1
#            print "Hmm, hash matched but no hit for %s" % game.headers
        if len(matching_kaggle_games) > 1:
            print "WHOA, multiple kaggle games (%s) match %s" % (matching_kaggle_games, headers)
            multimatch = multimatch + 1
        if len(matching_kaggle_games) == 1:
            
            print '%s matches %s' % (matching_kaggle_games[0]['Event'], headers['Event'])
        
    game_num = game_num + 1
#    if game_num % 100 == 0:
#        sys.stderr.write('.')

sys.stderr.write('Out of %i games, %i found hits. %i hash hits but game mismatch. %i had multimatch.\n' % (game_num, num_hits, hashmatchonly, multimatch))
#print str(exporter)
