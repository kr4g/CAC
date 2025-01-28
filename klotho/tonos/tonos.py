# ------------------------------------------------------------------------------------
# Klotho/klotho/tonos/tonos.py
# ------------------------------------------------------------------------------------
'''
--------------------------------------------------------------------------------------
General functions for performing calculations and computations related to pitch and 
frequency.
--------------------------------------------------------------------------------------
'''
from typing import Union, List, Tuple, Dict, Set
from collections import namedtuple
from fractions import Fraction
import numpy as np

A4_Hz   = 440.0
A4_MIDI = 69

from utils.data_structures.enums import DirectValueEnumMeta, Enum  

class PITCH_CLASSES(Enum, metaclass=DirectValueEnumMeta):
  class N_TET_12(Enum, metaclass=DirectValueEnumMeta):
    C  = 0
    Cs = 1
    Db = 1
    D  = 2
    Ds = 3
    Eb = 3
    E  = 4
    Es = 5
    Fb = 4
    F  = 5
    Fs = 6
    Gb = 6
    G  = 7
    Gs = 8
    Ab = 8
    A  = 9
    As = 10
    Bb = 10
    B  = 11
    Bs = 0
  
    class names:
      as_sharps = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
      as_flats  = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']


class Pitch:
  def __init__(self, pitchclass: str = 'A', octave: int = 4, cents_offset: float = 0.0, partial: int = 1):
    self._pitchclass = pitchclass
    self._octave = octave
    self._cents_offset = cents_offset
    self._partial = partial
  
  @property
  def pitchclass(self):
    return self._pitchclass
  
  @property
  def octave(self):
    return self._octave
  
  @property
  def cents_offset(self):
    return self._cents_offset
  
  @property
  def partial(self):
    return self._partial
  
  @property
  def virtual_fundamental(self):
    return Pitch(*partial_to_fundamental(self._pitchclass, self._octave, self._partial, self._cents_offset))
  
  @property
  def freq(self):
    return pitchclass_to_freq(self._pitchclass, self._octave, self._cents_offset)
  
  @cents_offset.setter
  def cents_offset(self, value):
    self._cents_offset = value
  
  @partial.setter
  def partial(self, value):
    self._partial = value
  
  def __str__(self):
    cents_offset = f'({self._cents_offset:+0.2f} cents)' if round(self._cents_offset, 2) != 0 else ''
    base_str = (
      f'Name:          {self._pitchclass}{self._octave} {cents_offset}\n'
      f'Frequency:     {round(self.freq, 4)} Hz'
    )
    
    # if self._partial != 1:
    #   base_str += (
    #     f'\nPartial:       {self._partial}\n'
    #     f'Virtual Fund.: {self.virtual_fundamental.pitchclass}{self.virtual_fundamental.octave} '
    #     f'({self.virtual_fundamental.cents_offset:+0.4f} cents)'
    #   )
    
    return base_str + '\n'
    
  def __repr__(self):
    return self.__str__()


def freq_to_midicents(frequency: float) -> float:
  '''
  Convert a frequency in Hertz to MIDI cents notation.
  
  MIDI cents are a logarithmic unit of measure used for musical intervals.
  The cent is equal to 1/100th of a semitone. There are 1200 cents in an octave.
  
  MIDI cents combines MIDI note numbers (denoting pitch with) with cents (denoting
  intervals).  The MIDI note number is the integer part of the value, and the cents
  are the fractional part.
  
  The MIDI note for A above middle C is 69, and the frequency is 440 Hz.  The MIDI
  cent value for A above middle C is 6900.  Adding or subtracting 100 to the MIDI
  cent value corresponds to a change of one semitone (one note number in the Western
  dodecaphonic equal-tempered "chromatic" scale).
  
  Values other than multiple of 100 indicate microtonal intervals.

  Args:
  frequency: The frequency in Hertz to convert.

  Returns:
  The MIDI cent value as a float.
  '''
  return 100 * (12 * np.log2(frequency / A4_Hz) + A4_MIDI)

def midicents_to_freq(midicents: float) -> float:
  '''
  Convert MIDI cents back to a frequency in Hertz.
  
  MIDI cents are a logarithmic unit of measure used for musical intervals.
  The cent is equal to 1/100th of a semitone. There are 1200 cents in an octave.
  
  MIDI cents combines MIDI note numbers (denoting pitch with) with cents (denoting
  intervals).  The MIDI note number is the integer part of the value, and the cents
  are the fractional part.
  
  The MIDI note for A above middle C is 69, and the frequency is 440 Hz.  The MIDI
  cent value for A above middle C is 6900.  Adding or subtracting 100 to the MIDI
  cent value corresponds to a change of one semitone (one note number in the Western
  dodecaphonic equal-tempered "chromatic" scale).
  
  Values other than multiple of 100 indicate microtonal intervals.
  
  Args:
    midicents: The MIDI cent value to convert.
    
  Returns:
    The corresponding frequency in Hertz as a float.
  '''
  return A4_Hz * (2 ** ((midicents - A4_MIDI * 100) / 1200.0))

def midicents_to_pitchclass(midicents: float) -> Pitch:
  '''
  Convert MIDI cents to a pitch class with offset in cents.
  
  Args:
    midicents: The MIDI cent value to convert.
    
  Returns:
    A tuple containing the pitch class and the cents offset.
  '''
  PITCH_LABELS = PITCH_CLASSES.N_TET_12.names.as_sharps
  midi = midicents / 100
  midi_round = round(midi)
  note_index = int(midi_round) % len(PITCH_LABELS)
  octave = int(midi_round // len(PITCH_LABELS)) - 1  # MIDI starts from C-1
  pitch_label = PITCH_LABELS[note_index]
  cents_diff = (midi - midi_round) * 100
  return pitch_label, octave, round(cents_diff, 4)
  # return Pitch(pitch_label, octave, round(cents_diff, 4))

def ratio_to_cents(ratio: Union[int, float, Fraction, str], round_to: int = 4) -> float:
  '''
  Convert a musical interval ratio to cents, a logarithmic unit of measure.
  
  Args:
    ratio: The musical interval ratio as a string (e.g., '3/2') or float.
    
  Returns:
    The interval in cents as a float.
  '''
  # bad...
  # if isinstance(ratio, str):
  #   numerator, denominator = map(float, ratio.split('/'))
  # else:  # assuming ratio is already a float
  #   numerator, denominator = ratio, 1.0
  if isinstance(ratio, str):
    ratio = Fraction(ratio)
    numerator, denominator = ratio.numerator, ratio.denominator
  else:  # assuming ratio is already a float/int
    ratio = Fraction(ratio)
    numerator, denominator = ratio.numerator, ratio.denominator
  return round(1200 * np.log2(numerator / denominator), round_to)

def cents_to_ratio(cents: float) -> str:
  '''
  Convert a musical interval in cents to a ratio.
  
  Args:
    cents: The interval in cents to convert.
    
  Returns:
    The interval ratio as a float.
  '''
  return 2 ** (cents / 1200)

def cents_to_setclass(cent_value: float = 0.0, n_tet: int = 12, round_to: int = 2) -> float:
   return round((cent_value / 100)  % n_tet, round_to)

def ratio_to_setclass(ratio: Union[str, float], n_tet: int = 12, round_to: int = 2) -> float:
  '''
  Convert a musical interval ratio to a set class.
  
  Args:
    ratio: The musical interval ratio as a string (e.g., '3/2') or float.
    n_tet: The number of divisions in the octave, default is 12.
    round_to: The number of decimal places to round to, default is 2.
    
  Returns:
    The set class as a float.
  '''
  return cents_to_setclass(ratio_to_cents(ratio), n_tet, round_to)

def freq_to_pitchclass(freq: float, cent_round: int = 4) -> Pitch:
    '''
    Converts a frequency to a pitch class with offset in cents.
    
    Args:
        freq: The frequency in Hertz to convert.
        cent_round: Number of decimal places to round cents to
    
    Returns:
        A tuple containing the pitch class and the cents offset.
    '''
    PITCH_LABELS = PITCH_CLASSES.N_TET_12.names.as_sharps
    n_PITCH_LABELS = len(PITCH_LABELS)
    midi = A4_MIDI + n_PITCH_LABELS * np.log2(freq / A4_Hz)
    midi_round = round(midi)
    note_index = int(midi_round) % n_PITCH_LABELS
    octave = int(midi_round // n_PITCH_LABELS) - 1  # MIDI starts from C-1
    pitch_label = PITCH_LABELS[note_index]
    cents_diff = (midi - midi_round) * 100
    
    # Format negative octaves with proper number
    # octave_str = str(octave) if octave >= 0 else f"-{abs(octave)}"
    return pitch_label, octave, round(cents_diff, cent_round)
    # return Pitch(pitch_label, octave, round(cents_diff, cent_round))

def pitchclass_to_freq(pitchclass: str, octave: int = 4, cent_offset: float = 0.0, hz_round: int = 4, A4_Hz=A4_Hz, A4_MIDI=A4_MIDI):
    '''
    Converts a pitch class with offset in cents to a frequency.
    
    Args:
        pitchclass: The pitch class (like "C4" or "F#-2") to convert.
        cent_offset: The cents offset, default is 0.0.
        A4_Hz: The frequency of A4, default is 440 Hz.
        A4_MIDI: The MIDI note number of A4, default is 69.
    
    Returns:
        The frequency in Hertz.
    '''
    # Try both sharp and flat notations
    SHARP_LABELS = PITCH_CLASSES.N_TET_12.names.as_sharps
    FLAT_LABELS = PITCH_CLASSES.N_TET_12.names.as_flats
    
    try:
        note_index = SHARP_LABELS.index(pitchclass)
    except ValueError:
        try:
            note_index = FLAT_LABELS.index(pitchclass)
        except ValueError:
            raise ValueError(f"Invalid pitch class: {pitchclass}")

    midi = note_index + (octave + 1) * 12
    midi = midi - A4_MIDI
    midi = midi + cent_offset / 100
    frequency = A4_Hz * (2 ** (midi / 12))
    return round(frequency, hz_round)

def partial_to_fundamental(pitchclass: str, octave: int = 4, partial: int = 1, cent_offset: float = 0.0) -> Tuple[str, float]:
    '''
    Calculate the fundamental frequency given a pitch class and its partial number.
    
    Args:
        pitchclass: The pitch class with octave (e.g., "A4", "C#3", "Bb2")
        partial: The partial number (integer >= 1)
        cent_offset: The cents offset from the pitch class, default is 0.0
        
    Returns:
        A tuple containing the fundamental's pitch class with octave and cents offset
    '''
    if partial < 1:
        raise ValueError("Partial number must be 1 or greater")

    freq = pitchclass_to_freq(pitchclass, octave, cent_offset)
    fundamental_freq = freq / partial
    return freq_to_pitchclass(fundamental_freq)

def split_interval(interval:Union[int, float, Fraction, str], n:int = 2):
    result = namedtuple('result', ['sequence', 'k'])

    multiplier = float(Fraction(interval))
    k = 1
    while True:
        d = ((multiplier-1) * k) / n
        if d.is_integer():
            sequence = [k + i*int(d) for i in range(n+1)]
            if sequence[-1] / sequence[0] == multiplier:
                return result(sequence, k)
        k += 1

def find_first_equave(harmonic: Union[int, float, Fraction], equave=2, max_equave=None):
  '''
  Returns the first equave in which a harmonic first appears.
  
  Args:
    harmonic: A harmonic.
    max_equave: The maximum equave to search, default is None.
    
  Returns:
    The first equave in which the harmonic first appears as an integer.
  '''
  n_equave = 0
  while max_equave is None or n_equave <= max_equave:
    if harmonic <= equave ** n_equave:
      return n_equave
    n_equave += 1
  return None

def equave_reduce(interval:Union[int, float, Fraction, str], equave:Union[Fraction, int, str, float] = 2, n_equaves:int = 1) -> Union[int, float, Fraction]:
  '''
  Reduce an interval to within the span of a specified octave.
  
  Args:
    interval: The musical interval to be octave-reduced.
    equave: The span of the octave for reduction, default is 2.
    n_equaves: The number of equaves, default is 1.
    
  Returns:
    The equave-reduced interval as a float.
  '''
  interval = Fraction(interval)
  equave = Fraction(equave)
  while interval > equave**n_equaves:
    interval /= equave
  return interval

def fold_interval(interval:Union[Fraction, int, float, str], equave:Union[Fraction, int, float, str] = 2, n_equaves:int = 1) -> float:
  '''
  Fold an interval to within a specified range.

  Args:
    interval: The interval to be wrapped.
    equave: The equave value, default is 2.
    n_equaves: The number of equaves, default is 1.

  Returns:
    The folded interval as a float.
  '''
  interval = Fraction(interval)
  equave = Fraction(equave)  
  while interval < 1/(equave**n_equaves):
    interval *= equave
  while interval > (equave**n_equaves):
    interval /= equave
  return interval

def fold_freq(freq: float, lower: float = 27.5, upper: float = 4186, equave: float = 2.0) -> float:
  '''
  Fold a frequency value to within a specified range.
  
  Args:
    freq: The frequency to be wrapped.
    lower: The lower bound of the range.
    upper: The upper bound of the range.
    
  Returns:
    The folded frequency as a float.
  '''
  while freq < lower:
      freq *= equave
  while freq > upper:
      freq /= equave  
  return freq

def n_tet(divisions=12, equave=2, nth_division=1):
  '''
  Calculate the size of the nth division of an interval in equal temperament.
  
  see:  https://en.wikipedia.org/wiki/Equal_temperament

  :param interval: The interval to divide (default is 2 for an octave)
  :param divisions: The number of equal divisions
  :param nth_division: The nth division to calculate
  :return: The frequency ratio of the nth division
  '''
  return equave ** (nth_division / divisions)

def ratios_n_tet(divisions=12, equave=2):
  '''
  Calculate the ratios of the divisions of an interval in equal temperament.
  
  see:  https://en.wikipedia.org/wiki/Equal_temperament

  :param interval: The interval to divide (default is 2 for an octave)
  :param divisions: The number of equal divisions
  :return: A list of the frequency ratios of the divisions
  '''
  return [n_tet(divisions, equave, nth_division) for nth_division in range(divisions)]
