Code for the Finding Elo Kaggle contest that ended 20150324.
Earned 2nd place with final MAE of ~160.


System components:

* Scoreserver. Many features were computed by rerunning
  lightly-modified Stockfish/pystockfish on a bunch of AWS/EC2 servers
  running Docker containers.  To read the scoreserver code and see
  what features it computes, look at `djeval/__init__.py`, starting from
  the function [do_it_backwards()](https://github.com/dsjoerg/blundercheck/blob/master/djeval/__init__.py#L402).  The results of that were ultimately
  gathered into a big JSON file called `20150312.gz`.  Some notable things happening in the scoreserver:
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
   ["filter-games"](https://github.com/dsjoerg/polyglot_elo/blob/master/src/filter_games.cpp)
   mode to `polyglot_elo` to filter out the Kaggle games from OM GOLEM.
  * We added an
   ["elo-book"](https://github.com/dsjoerg/polyglot_elo/blob/master/src/elo_book.cpp)
   mode to `polyglot_elo` to compute stats about the Kaggle games, using
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
   

* Modeling.  See [data_prep/fit_model.sh](https://github.com/dsjoerg/blundercheck/blob/master/data_prep/fit_model.sh).  The scripts it refers to can be found in the `data_prep` and `modeling` directories.
  * `fit_movemodel.py` fits a `RandomForestRegressor` model that predicts the ELO of a player from a **single move**.  It takes into account various features of the move, the score at that time, the ply, which piece is being moved, in what direction and distance, and the same properties of Stockfish's best move.  In the end it was worth a point or two, but only once I had the Guid-Bratko complexity measure as one of its features.
  * `make_material_aggregates.py` computed some features about material and non-material equity throughout the game.  worth a point.
  * `crunch_movescores.py` computes various features from the stockfish equity valuations, for example `q_error_one` which is the centipawn loss of the player's 25% worst move: `percentile(clip(movescores[side], -1. * ERROR_CLIP, 0), 25)`.  To put it another way, it's the median equity lost in the worse-half of the player's moves.
  * `prepare_pgmodel.py` combines the various datasets into a single `DataFrame` ready for modeling.
  * `fit_linear_pgmodel.py` fits an ordinary least-squares linear model
  * `fit_rfr_pgmodel.py` fits a `RandomForestRegressor`; one of its inputs is the linear model prediction from the previous step.  I found it strange and unwelcome to be feeding one model's prediction into another model, but couldn't eliminate it without losing ~3-4 score points.


Other interesting things:

* There were about 200 games that are both in the test set *and* the training set.  For example, game 55 is a move-by-move match for game 33412.  I asked the tournament admins if it was permitted to use the ELO of game 55 when predicting the ELO of game 33412; the rules seemed ambiguous on this point; and they indicated it was OK.
* The distribution of ELO difference between opponents was bimodal -- rather than one big hump at zero there were two humps, at ~-150 and +150.  Perhaps this is because of how tournaments get paired?  I was unable to explicitly use this observation; but perhaps the `RandomForestRegressor` picked it up for free.
* Using external databases I was able to match about 90% of Kaggle games 1-25,000 to an external source which included the event name.  About 3.5% of those games had the word Blitz or Rapid in the event name.   Knowing which games were blitz/rapid was worth ~5 score points, but of course this could not be used for the contest because we do not know the event names or time controls for the game 25-50k.  (This is an underestimate of the time control issue because there are other funky formats that my simple string search did not detect, such as [Basque](http://media.sportaccord.com/articles/view/Chess-Basque-system-chess-a-definite-Mind-Game)).
* Towards the end of the contest I became worried that public progress on the leaderboard would give too much information away to my fellow competitors.  However I was still interested in knowing how well I was doing on games 25-50k.  So I made "masked" submissions in pairs, where in the first submission I would override my prediction for games 25-37.5k to be a dumb constant, and the in the second submission I would override my prediction for games 37.5-50k in the same way.  With the scores of both bad submissions I could back out what score I would have gotten had I submitted it normally, and thus get my score without anyone else being able to see it.  That reduced the number of submissions per day I could make by half, but it seemed worth it.
* I tried many things that didn't end up improving the score:
  * I attempted a sequential Bayesian model inspired by [Skill Rating by Bayesian Inference](http://www.cse.buffalo.edu/~regan/papers/pdf/DFHR09.pdf).  The resulting features were predictive in isolation, but must have been correlated to other features I already had because they did not add enough score to be worth including.  I suspect that the quantiles of player error were fulfilling a similar role.
  * It seemed like a 10MM game library could be used more effectively, in the spirit of [The Unreasonable Effectiveness of Data](http://static.googleusercontent.com/media/research.google.com/en/us/pubs/archive/35179.pdf).  I scored an additional 50k games and used them in the full modeling process, however they actually made the model worse!  This may have been due to the fact that the Kaggle games were selected by different criteria than the OM GOLEM or Chess Tempo libraries I used.  I attempted to weight the 50k games to make their ELO distribution similar to that of the Kaggle games, at which point they were mildly helpful (0.5 point IIRC), but not enough to justify the extra computational and complexity cost.


If anyone cares to actually re-run and reproduce the full modeling pipeline, please ask and I
will give more detailed directions, which I have in my own notes but
are not yet clean enough to be readily comprehensible to others.

Thanks to my fellow competitors, Yaron Gvili, Jonathan Baxter and Teddy Coleman for the friendly exchange of ideas.  Thanks also to Matej Guid, Kenneth Regan and the other academics whose work was linked above.
