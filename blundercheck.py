
import chess.pgn
import chess
import urllib
import pystockfish

class DSJURLopener(urllib.FancyURLopener):
    version = "dsjoerg"

urllib._urlopener = DSJURLopener()


def score_node(engine, node):
    """
    Returns the score, in centipawns for white,
    for the position indicated by the given GameNode.
    
    If the position is won or illegal, return infinity.
    
    Also return the best move.
    """

    engine.setfen(node.board().fen())
    bestmove = engine.bestmove()
    score_cp = bestmove['score_cp']
    if score_cp:
        score_cp_for_white = score_cp
    else:
        score_cp_for_white = float("inf")

    if node.board().turn == chess.BLACK:
        score_cp_for_white = -1 * score_cp_for_white

    if bestmove['move'] != '(none)':
        move_object = chess.Move.from_uci(bestmove['move'])
    else:
        move_object = None
        
    return (score_cp_for_white, move_object)

    

def do_it(pgn_url="http://en.lichess.org/game/export/tKEOqmC3.pgn", depth=15):
    engine = pystockfish.Engine(depth=depth, param={'Threads': 8})
    game = chess.pgn.read_game(urllib.urlopen(pgn_url))
    node = game

    (current_score_white, best_move) = score_node(engine, node)

    while node.variations:

        turn_indicator = '.'
        score_sign = 1
        if node.board().turn == chess.BLACK:
            turn_indicator = '...'
            score_sign = -1

        next_node = node.variation(0)
        (next_score_white, next_best_move) = score_node(engine, next_node)
        score_loss = score_sign * (current_score_white - next_score_white)

        print('%2d%-3s %6s loss:%5.0f (equity: %+5.0f) (best move: %s)' %
              (node.board().fullmove_number, turn_indicator, node.board().san(next_node.move), score_loss, next_score_white, node.board().san(best_move)))
        node = next_node
        current_score_white = next_score_white
        best_move = next_best_move

