# ------------------------------------------------------------------------------------
# Klotho/klotho/chronos/chronos.py
# ------------------------------------------------------------------------------------
'''
--------------------------------------------------------------------------------------
General functions for performing calculations and computations related to time.
--------------------------------------------------------------------------------------
'''
from typing import Union
import numpy as np
from fractions import Fraction
from itertools import accumulate
from utils.data_structures.enums import MinMaxEnum

class TEMPO(MinMaxEnum):
  '''
  Enum for musical tempo markings mapped to beats per minute (bpm).

  Each tempo marking is associated with a range of beats per minute. 
  This enumeration returns a tuple representing the minimum and maximum bpm for each tempo.

  ----------------|----------------------|----------------
  Name            | Tempo Marking        | BPM Range
  ----------------|----------------------|----------------
  Larghissimo     | extremely slow       | (12 - 24 bpm)
  Adagissimo_Grave | very slow, solemn   | (24 - 40 bpm)
  Largo           | slow and broad       | (40 - 66 bpm)
  Larghetto       | rather slow and broad| (44 - 66 bpm)
  Adagio          | slow and expressive  | (44 - 68 bpm)
  Adagietto       | slower than andante  | (46 - 80 bpm)
  Lento           | slow                 | (52 - 108 bpm)
  Andante         | walking pace         | (56 - 108 bpm)
  Andantino       | slightly faster than andante | (80 - 108 bpm)
  Marcia_Moderato | moderate march       | (66 - 80 bpm)
  Andante_Moderato | between andante and moderato | (80 - 108 bpm)
  Moderato        | moderate speed       | (108 - 120 bpm)
  Allegretto      | moderately fast      | (112 - 120 bpm)
  Allegro_Moderato | slightly less than allegro | (116 - 120 bpm)
  Allegro         | fast, bright         | (120 - 156 bpm)
  Molto_Allegro_Allegro_Vivace | slightly faster than allegro | (124 - 156 bpm)
  Vivace          | lively, fast         | (156 - 176 bpm)
  Vivacissimo_Allegrissimo | very fast, bright | (172 - 176 bpm)
  Presto          | very fast            | (168 - 200 bpm)
  Prestissimo     | extremely fast       | (200 - 300 bpm)
  ----------------|----------------------|----------------

  Example use:
  `>>> Tempo.Adagio.min`
  '''  
  Larghissimo                  = (12, 24)
  Adagissimo_Grave             = (24, 40)
  Largo                        = (40, 66)
  Larghetto                    = (44, 66)
  Adagio                       = (44, 68)
  Adagietto                    = (46, 80)
  Lento                        = (52, 108)
  Andante                      = (56, 108)
  Andantino                    = (80, 108)
  Marcia_Moderato              = (66, 80)
  Andante_Moderato             = (80, 108)
  Moderato                     = (108, 120)
  Allegretto                   = (112, 120)
  Allegro_Moderato             = (116, 120)
  Allegro                      = (120, 156)
  Molto_Allegro_Allegro_Vivace = (124, 156)
  Vivace                       = (156, 176)
  Vivacissimo_Allegrissimo     = (172, 176)
  Presto                       = (168, 200)
  Prestissimo                  = (200, 300)

def seconds_to_hmsms(seconds: float, as_string=True) -> str:
    '''
    Convert a duration from seconds to a formatted string in hours, minutes, seconds, and milliseconds.
    Only shows non-zero units, starting from the largest unit.

    Args:
    seconds (float): The duration in seconds.
    as_string (bool, optional): Whether to return the result as a string or as a tuple of integers. 
    Defaults to True.

    Returns:
    str: The formatted duration string, showing only non-zero units (e.g., '1h:30m:45s:500ms' or '45s:500ms').
    tuple: The formatted duration as a tuple of integers in the form (hours, minutes, seconds, milliseconds).
    '''    
    h = int(seconds // 3600)
    seconds %= 3600
    m = int(seconds // 60)
    seconds %= 60
    s = int(seconds)
    ms = int((seconds - s) * 1000)
    
    if not as_string:
        return (h, m, s, ms)
    
    parts = []
    if h > 0:
        parts.append(f'{h}h')
    if h > 0 or m > 0:
        parts.append(f'{m:02}m')
    # if h > 0 or m > 0 or s > 0:
    parts.append(f'{s:02}s')
    parts.append(f'{ms:03}ms')
    
    return ':'.join(parts)
  
def cycles_to_frequency(cycles: Union[int, float], duration: float) -> float:
    '''
    Calculate the frequency (in Hz) needed to produce a specific number of cycles within a given duration.

    Args:
    cycles (Union[int, float]): The desired number of complete cycles
    duration (float): The time duration in seconds

    Returns:
    float: The frequency in Hertz (Hz) that will produce the specified number of cycles in the given duration

    Example:
    >>> cycles_to_frequency(4, 2)  # 4 cycles in 2 seconds = 2 Hz
    2.0
    '''
    return cycles / duration

def beat_duration(ratio:Union[int, float, Fraction, str], bpm:Union[int, float], beat_ratio:Union[int, float, Fraction, str] = '1/4') -> float:
  '''
  Calculate the duration in seconds of a musical beat given a ratio and tempo.

  The beat duration is determined by the ratio of the beat to a reference beat duration (beat_ratio),
  multiplied by the tempo factor derived from the beats per minute (BPM).

  Args:
  ratio (str): The ratio of the desired beat duration to a whole note (e.g., '1/4' for a quarter note).
  bpm (float): The tempo in beats per minute.
  beat_ratio (str, optional): The reference beat duration ratio, defaults to a quarter note '1/4'.

  Returns:
  float: The beat duration in seconds.
  '''
  tempo_factor = 60 / bpm
  ratio_value  = float(Fraction(ratio))
  beat_ratio   = Fraction(beat_ratio)
  return tempo_factor * ratio_value * (beat_ratio.denominator / beat_ratio.numerator)

def calc_onsets(durations:tuple):
    return tuple(accumulate([0] + list(abs(r) for r in durations)))

def quantize(duration: float, bpm: float, beat_ratio: str = '1/4', max_denominator: float = 16) -> Fraction:
  '''
  Finds the closest beat ratio for a given duration at a certain tempo.
  
  Args:
  duration (float): The duration in seconds.
  bpm (float): The tempo in beats per minute.
  beat_ratio (str, optional): The reference beat duration ratio, defaults to a quarter note '1/4'.
  
  Returns:
  str: The closest beat ratio as a string in the form 'numerator/denominator'.
  '''  
  approximate_ratio = lambda x: Fraction(x).limit_denominator(max_denominator)
  
  beat_numerator, beat_denominator = map(int, beat_ratio.split('/'))
  reference_beat_duration = 60 / bpm * (beat_denominator / beat_numerator)
  beat_count = duration / reference_beat_duration
  return approximate_ratio(beat_count)

def metric_modulation(current_tempo:float, current_beat_value:Union[Fraction,str,float], new_beat_value:Union[Fraction,str,float]) -> float:
  '''
  Determine the new tempo (in BPM) for a metric modulation from one metric value to another.

  Metric modulation is calculated by maintaining the duration of a beat constant while changing
  the note value that represents the beat, effectively changing the tempo.
  
  see:  https://en.wikipedia.org/wiki/Metric_modulation

  Args:
  current_tempo (float): The original tempo in beats per minute.
  current_beat_value (float): The note value (as a fraction of a whole note) representing one beat before modulation.
  new_beat_value (float): The note value (as a fraction of a whole note) representing one beat after modulation.

  Returns:
  float: The new tempo in beats per minute after the metric modulation.
  '''
  current_duration = 60 / current_tempo * current_beat_value
  new_tempo = 60 / current_duration * new_beat_value
  return new_tempo

def rubato(durations, accelerando=True, intensity=0.5):
    '''
    Apply rubato to a list of durations.

    Rubato is a musical term for expressive and flexible tempo, often used to convey emotion or
    to create a sense of freedom in the music. This function applies rubato to a list of durations
    by stretching or compressing the durations according to the given parameters.

    Args:
    durations (list): A list of durations in seconds.
    accelerando (bool, optional): Whether to apply an accelerando (True) or a ritardando (False), defaults to True.
    intensity (float, optional): The intensity of the rubato effect, defaults to 0.5.

    Returns:
    list: The list of durations with rubato applied.
    '''
    assert 0 <= intensity <= 1, "Intensity must be between 0 and 1"
    
    durations = np.array(durations)
    total_duration = durations.sum()
    n = len(durations)
    
    increments = np.linspace(n, 1, n) if accelerando else np.linspace(1, n, n)
    
    increments = increments * intensity + (1 - intensity)
    increments_scaled = increments / increments.sum() * total_duration
    
    # correction by scaling
    corrected_total = increments_scaled.sum()
    scaling_factor = total_duration / corrected_total
    corrected_durations = increments_scaled * scaling_factor

    return corrected_durations.tolist()
