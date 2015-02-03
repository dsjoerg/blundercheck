#!/usr/bin/env python

import json, sys, argparse
from chess import *
from chess.pgn import *


# returns "NE", "SW" etc for a move, from the players perspective
# and also the distance moved
def move_direction_and_distance(board, move):

    from_file = file_index(move.from_square)
    from_rank = rank_index(move.from_square)
    to_file = file_index(move.to_square)
    to_rank = rank_index(move.to_square)
    file_move = to_file - from_file
    rank_move = to_rank - from_rank
    if node.board().turn == chess.BLACK:
        file_move = -1 * file_move
        rank_move = -1 * rank_move

    ns_letter = ""
    if rank_move > 0:
        ns_letter = "N"
    elif rank_move < 0:
        ns_letter = "S"
    
    ew_letter = ""
    if file_move > 0:
        ew_letter = "E"
    elif file_move < 0:
        ew_letter = "W"


    return (ns_letter + ew_letter), max(abs(file_move), abs(rank_move))


# returns a comma-separated string representing the features of this move
def features(board, move):
    if move is None:
        return ", ".join([""] * 5)

    move_dir, move_dist = move_direction_and_distance(board, move)
    board.push(move)
    is_check = board.is_check()
    board.pop()
    result = ", ".join([board.piece_at(move.from_square).symbol().upper(),
                        move_dir,
                        str(move_dist),
                        str(board.piece_at(move.to_square) is not None),
                        str(is_check)
                    ])
    return result


parser = argparse.ArgumentParser(description='Produce a set of features for each move in a set of games.  Output goes to stdout.')
parser.add_argument('pgn', help='PGN file of games')
parser.add_argument('jsoneval', help='JSON eval of games')
parser.add_argument('outfile', help='output file')

args = parser.parse_args()

best_moves = {}

output_fd = open(args.outfile, 'w')

print "Opening %s" % args.jsoneval
json_fd = open(args.jsoneval, 'r')
results = json.load(json_fd)
for result in results:
    game_num = int(result['event'])
    best_moves[game_num] = result['best_moves']

print "Opening %s" % args.pgn
game_fd = open(args.pgn, 'r')
game = read_game(game_fd)
while game is not None:
    node = game
    movenum = 0
    game_num =  int(game.headers['Event'])
    print 'Doing game %i' % game_num
    if game_num % 100 == 0:
        sys.stdout.write('.')
    while node.variations:
        next_node = node.variation(0)
        done_move = next_node.move

        best_moves_list = best_moves.get(game_num)
        if best_moves_list:
            best_move_san = best_moves_list[movenum]
            best_move = node.board().parse_san(best_move_san)
        else:
            best_move_san = ""
            best_move = None
        best_move_features = features(node.board(), best_move)

        done_move_features = features(node.board(), done_move)
        output_fd.write(', '.join([str(game_num),
                                   str(movenum),
                                   node.board().san(done_move),
                                   done_move_features,
                                   best_move_san,
                                   best_move_features]))
        output_fd.write('\n')
        movenum = movenum + 1
        node = next_node
    game = read_game(game_fd)

output_fd.close()
