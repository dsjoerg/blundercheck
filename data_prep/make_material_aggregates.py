#!/usr/bin/env python

import sys, csv, code
import numpy as np
from djeval import *

def shell():
    vars = globals()
    vars.update(locals())
    shell = code.InteractiveConsole(vars)
    shell.interact()

msg("HI THERE")

def cheapo_lopass(x, alpha):
    if len(x) == 0:
        return []

    y = []
    y_last = x[0]
    for x_i in x:
        y_now = y_last + alpha * (x_i - y_last)
        y.append(y_now)
        y_last = y_now
    return y

class GameState:
    def __init__(self):
        self.total_material = []
        self.white_strategic_advantage = []
        self.opening_length = 0
        self.midgame_length = 0
        self.endgame_length = 0

def dump_rows(gs):

    material_breakpoints = []
    material_index = 0
    for material_level in [70,60,50,40,30]:
        material_index = next((index for index,value in enumerate(gs.total_material) if value < material_level), material_index)
        material_breakpoints.append(material_index)

    acwsa = np.abs(np.clip(cheapo_lopass(gs.white_strategic_advantage, 0.2), -300, 300))
    macwsa_by_decade = []
    for halfply_decade in range(0,10):
        macwsa_by_decade.append(np.mean(acwsa[halfply_decade * 10 : (halfply_decade + 1) * 10]))

    if current_game == 0:
        return
    print current_game,
    for mb in material_breakpoints:
        print mb,
    print gs.opening_length,
    print gs.midgame_length,
    print gs.endgame_length,
    print round(np.mean(acwsa), 1),
    for macwsa_d in macwsa_by_decade:
        print round(macwsa_d, 1),
    print

columns = [
'halfply',
'moverscore',
'movergain',
'prevgain',
'move_piece',
'move_dir',
'move_dist',
'move_is_capture',
'move_is_check',
'bestmove_piece',
'bestmove_dir',
'bestmove_dist',
'bestmove_is_capture',
'bestmove_is_check',
'depth',
'seldepth',
'depths_agreeing',
'deepest_agree',
'num_bestmoves',
'num_bestmove_changes',
'bestmove_depths_agreeing',
'deepest_change',
'elo',
'side',
'gamenum',
'white_material',
'black_material',
'game_phase',
]

infile = open(sys.argv[1], 'r')
csvreader = csv.DictReader(infile, fieldnames=columns)


current_game = 0
rownum = 0
gs = GameState()

for row in csvreader:
    if row['gamenum'] != current_game:
        dump_rows(gs)
        current_game = row['gamenum']
        gs = GameState()
    side = int(row['side'])
    if int(row['game_phase']) == 128:
        gs.opening_length = gs.opening_length + 1
    elif int(row['game_phase']) == 0:
        gs.endgame_length = gs.endgame_length + 1
    else:
        gs.midgame_length = gs.midgame_length + 1
    gs.total_material.append(int(row['white_material']) + int(row['black_material']))
    white_equity = int(row['moverscore']) * int(row['side'])
    white_material_advantage = 100 * (int(row['white_material']) - int(row['black_material']))
    white_strategic_advantage = white_equity - white_material_advantage
    gs.white_strategic_advantage.append(white_strategic_advantage)

    rownum = rownum + 1
#    if rownum % 20000 == 0:
#        msg('row %i\n' % rownum)
#    if rownum > 10000:
#        break
