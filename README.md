Code for the Finding Elo Kaggle contest that ended 20150324.
Earned 2nd place with final MAE of ~160.

System components:

* Scoreserver. Many features were computed by rerunning
  lightly-modified Stockfish/pystockfish on a bunch of AWS/EC2 servers
  running Docker containers.  To read the scoreserver code and see
  what features it computes, look at djeval/__init__.py, starting from
  the function do_it_backwards().  The results of that were ultimately
  gathered into a big JSON file called 20150312.gz.
  * Tweaks in pystockfish to return more stats from Stockfish
   evaluations: https://github.com/dsjoerg/pystockfish/commits/master
  * Minor tweaks in Stockfish to dump stats on material value and game
   phase: https://github.com/dsjoerg/Stockfish/commits/blundercheck
  * We computed the Guid-Bratko complexity measure as described
   [here](http://magix.fri.uni-lj.si/~matej/doc/Computer_Analysis_of_World_Chess_Champions.pdf)
  * We computed several features from the output of stockfish, such as
   the number of times the best move changed, and the deepest depth at
   which Stockfish agreed with the player's move.
  * In the end I ran Stockfish with an embarrassingly large 16 seconds
   per move (rather than a fixed depth).  However, the extra time made
   surprsingly little difference.  Holding all else equal, doubling
   from 2s to 4s per move improved my score by 0.3 points.  Doubling
   to 8s gave another 0.4 points, and against to 16s gave another 0.4
   points.

* Game library.  Rather than use an opening book, we use the 10MM game
  library OM GOLEM from [Opening
  Master](http://www.openingmaster.com/).  We modified Fabien
  Letouzey's polyglot program in conjunction with the library:
  https://github.com/dsjoerg/polyglot_elo.
  * We added a
   ("filter-games")[https://github.com/dsjoerg/polyglot_elo/blob/master/src/filter_games.cpp]
   mode to polyglot_elo to filter out the Kaggle games from OM GOLEM.
  * We added an
   ("elo-book")[https://github.com/dsjoerg/polyglot_elo/blob/master/src/elo_book.cpp]
   mode to polyglot_elo to compute stats about the Kaggle games, using
   the filtered OM GOLEM library.  Inspired by the ELO stats available
   in ChessTempo's [Game
   Database](http://chesstempo.com/game-database.html), we build an
   "opening book" up to 24 ply deep of the OM GOLEM games (filtered),
   noting for each position how many games reached it, and the
   average/max/min/stdev of the ELO of the players in those games.
   Then for each Kaggle game we look up to 24 ply deep for a match,
   stopping when fewer than 10 games match.  The average/min/max/stdev
   of the matching games are features, as well as some other ELO-based
   stats gathered during the walk to 24 ply.
  * To get an immediate feel for how this works, simply go to the
   [Chess Tempo Game
   Database](http://chesstempo.com/game-database.html) and click on
   the various moves, making note of the Av/Perf/Max Rating as you go.

* Modeling.  See data_prep/fit_model.sh.  The scripts it refers to can
  be found in the data_prep and modeling directories.

If anyone cares to actually run/reproduce this script please ask and I
will give more detailed directions, which I have in my own notes but
are not clean enough to be readily comprehensible to others.

There are more tricks and gritty details I can elaborate on if there
is further interest :)
