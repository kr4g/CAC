import sys
from pathlib import Path

root_path = Path(__file__).parent.parent.parent
sys.path.append(str(root_path))

# -------------------------------------------------------------------------------------
# IMPORTS -----------------------------------------------------------------------------
# --------
from klotho.chronos.temporal_units import TemporalUnit as UT, TemporalUnitSequence as UTSeq
from klotho.chronos import seconds_to_hmsms
from klotho.tonos import fold_interval
from klotho.aikous.expression import db_amp
from klotho.skora.graphs import *
from klotho.skora.animation.animate import *

# from utils.data_structures import scheduler as sch
from klotho.aikous.messaging import Scheduler
scheduler = Scheduler()

import numpy as np

# -------------------------------------------------------------------------------------
# PRE-COMPOSITIONAL MATERIAL ----------------------------------------------------------
# ---------------------------
tempus = '4/4'
beat = '1/4'
bpm = 92

utseq = UTSeq(
    (
        # UT(tempus=tempus, prolatio=(1,1,1,1), tempo=bpm, beat=beat),
        # UT(tempus=beat, prolatio='r', tempo=bpm, beat=beat),
        # UT(tempus=tempus, prolatio=(1,2,1,1), tempo=bpm, beat=beat),
        # UT(tempus=beat, prolatio='r', tempo=bpm, beat=beat),
        # UT(tempus=tempus, prolatio=(1,2,1,5), tempo=bpm, beat=beat),
        # UT(tempus=beat, prolatio='r', tempo=bpm, beat=beat),
        # UT(tempus=tempus, prolatio=(3,2,1,5), tempo=bpm, beat=beat),
        # UT(tempus=beat, prolatio='r', tempo=bpm, beat=beat),
        # UT(tempus=tempus, prolatio=(3,2,7,5), tempo=bpm, beat=beat),
        # UT(tempus=beat, prolatio='r', tempo=bpm, beat=beat),
        UT(tempus=tempus, prolatio=(3,2,(7,(3,1,1)),5), tempo=bpm, beat=beat),
        UT(tempus=beat, prolatio='r', tempo=bpm, beat=beat),
    )
)

# for i, ut in enumerate(utseq):
#     if len(ut.ratios) == 1: continue
#     ut.offset = 0
#     animate_temporal_unit(ut, True, False, file_name=f'ut_{i}c')
# animate_temporal_units(utseq.uts, True, False, file_name='utblock')
# print(seconds_to_hmsms(utseq.time))
# plot_graph(graph_tree(utseq.uts[-2].tempus, utseq.uts[-2].prolationis))

_ut = UT(tempus=tempus, prolatio=(3,2,(7,(3,1,1)),5), tempo=bpm, beat=beat)
animate_temporal_unit(_ut, True, False, file_name='ut6')

synths = {
    1: 'kick',
    2: 'snare',
    3: 'perc2',
    5: 'hat',
    7: 'crash',
}

print(utseq.time)
# ------------------------------------------------------------------------------------
# COMPOSITIONAL PROCESS --------------------------------------------------------------
# ----------------------
seed = np.random.randint(1000)
for j, ut in enumerate(utseq):
    dur_scale = np.interp(j, [0, utseq.size], [0.167, 0.667])
    for i, event in enumerate(ut):
        if event['duration'] < 0: continue
        # synth = 'ping' #synths[ut.prolationis[i]]
        duration = event['duration'] * dur_scale
        # freq = 333.0 * ut.prolationis[i] * 2**0 #fold_interval(1/ut.prolationis[i], n_equaves=1)
        freq = 333.0 * event['duration'] * 2**2 #fold_interval(1/ut.prolationis[i], n_equaves=1)
        scheduler.new_event('perc', event['start'], freq=freq, amp=db_amp(-8))
        scheduler.new_event('kick', event['start'], amp=db_amp(-7))

# ------------------------------------------------------------------------------------
# SEND COMPOSITION TO SYNTHESIZER ----------------------------------------------------
# --------------------------------
# scheduler.run()
