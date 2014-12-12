
import chess.pgn
import urllib
import pystockfish

class DSJURLopener(urllib.FancyURLopener):
    version = "dsjoerg"

urllib._urlopener = DSJURLopener()

def do_it(pgn_url):
    engine = pystockfish.Engine(depth=15, param={'Hash': 1000})
    game = chess.pgn.read_game(urllib.urlopen(pgn_url))
    node = game.end()

    while node.parent:
        engine.setfen(node.board().fen())
        bestmove = engine.bestmove()
        print(node.board().fen(), len(list(node.board().generate_legal_moves())), node.board().is_checkmate(), bestmove['score_cp'])
        node = node.parent
