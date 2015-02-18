#!/usr/bin/env ruby

require 'curb'

c = Curl::Easy.new("http://chesstempo.com/requests/login.php")
c.enable_cookies = true
c.http_post(Curl::PostField.content('username', 'dsjoerg'), Curl::PostField.content('password', 'yabutabu'), Curl::PostField.content('submit', '1'))

2012.upto(2013) {|year|
1200.upto(2800) {|elo|
  c.url = "http://chesstempo.com/requests/pgnforgames.php?currentFen=rnbqkbnr%2Fpppppppp%2F8%2F8%2F8%2F8%2FPPPPPPPP%2FRNBQKBNR%20w%20KQkq%20-%200%201&playerMinRating=#{elo}&playerMaxRating=#{elo}&pieceColour=white&gameResult=any&yearMin=#{year}&yearMax=#{year}&materialSearchStableLength=2&bishopColourChoice=-1&subsetMinRating=all"
  c.http_get
  pgn = c.body_str
  File.open("ct-#{year}-#{elo}.pgn", 'w') {|file| file.write(pgn)}
  print "Did #{year} #{elo}, #{pgn.size} bytes\n"
  sleep 1.0
}
}
