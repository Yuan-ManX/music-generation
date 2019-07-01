'''
functions and classes:
MidiDataset = Torch data loader. Transforms a list of midi files (midi_files) into a pytorch dataloader
list_midi_files = Given a source folder and the number of Train, Validation and test cases that you want, it will return a list of midis for each category

extra info about libraries:
music21 = Open source toolkit. Used to extract midi files into a Python understandable, event-based syntaxis. (https://web.mit.edu/music21/doc/)
'''

import glob
import pickle
import numpy as np
from music21 import converter, instrument, note, chord, stream

from os import walk
import random
from torch.utils import data

class MidiDataset(data.Dataset):
  'Characterizes a dataset for PyTorch'
  def __init__(self, qnsf, seq_len=25, cod_type=2, midi_files=[]):
        'Initialization'
        if cod_type !=1 and cod_type !=2:  
          raise TypeError("cod_type is not 1 (88 notes) or 2 (176 notes)")
        self.notes = self.get_notes(qnsf=qnsf, cod_type=cod_type, midi_files=midi_files)
        self.qnsf = qnsf
        self.seq_len = seq_len
        self.cod_type = cod_type
        self.midi_source = midi_files
        


  def __len__(self):
        'Denotes the total number of samples'
        return len(self.notes) - self.seq_len*2

  def __getitem__(self, index):
        'Generates one sample of data'
        # Select sample
        samples = self.notes[index:(index+self.seq_len*2)]
        x=np.asarray(samples).astype(np.float32)
        
        return (x[0:self.seq_len,:],x[self.seq_len:,:])
        #return  (samples[0:self.seq_len], samples[self.seq_len:])
      
  def get_notes(self, qnsf, cod_type,midi_files):
      """ Get all the notes and chords from the midi files in the ./midi_songs directory """
      notes = []

      for i,file in enumerate(midi_files):

          
          midi = converter.parse(file)

          print("Parsing %s" % file)
          
          
          try: # file has instrument parts
              s2 = instrument.partitionByInstrument(midi)
              notes_to_parse = s2.parts[0].recurse() 
          except: # file has notes in a flat structure
              notes_to_parse = midi.flat.notes

              #initialize piano roll
          length=int(notes_to_parse[-1].offset*qnsf)+1 #count number subdivisions
          notes_song=np.zeros((length,88*cod_type))

          for element in notes_to_parse:
              #print(element.offset, element.duration.quarterLength, element.pitch.midi-21)
              if isinstance(element, note.Note):
                  # cod_type is based on (0,1), (1,0), (0,0)
                  notes_song[int(element.offset*qnsf),cod_type*(element.pitch.midi-21)]=1.0    
                  notes_song[(int(element.offset*qnsf)+1):(int(element.offset*qnsf)+int(element.duration.quarterLength*qnsf)),cod_type*(element.pitch.midi-21)+1]=1.0   

              elif isinstance(element, chord.Chord):
                  for note_in_chord in element.pitches:
                    # cod_type is based on (0,1), (1,0), (0,0)
                    notes_song[int(element.offset*qnsf),cod_type*(note_in_chord.midi-21)]=1.0   
                    notes_song[(int(element.offset*qnsf)+1):(int(element.offset*qnsf)+int(element.duration.quarterLength*qnsf)),cod_type*(note_in_chord.midi-21)+1]=1.0   
              #print(notes_song.shape)
                   
          notes+=[list(i) for i in list(notes_song)]
      return notes


def list_midi_files(midi_source, data_len_train, data_len_val , data_len_test, randomSeq=True, seed = 666):
  midi_files_all = []
  for (dirpath, dirnames, filenames) in walk(midi_source):
    midi_files_all.extend(filenames)
  midi_files_all = [ glob.glob(midi_source+"/"+fi)[0] for fi in midi_files_all if fi.endswith(".mid") ]
  
  if randomSeq:
    random.seed( seed )
    midi_files_sel = random.sample(midi_files_all, (data_len_train + data_len_val + data_len_test))
  else:
    midi_files_sel = midi_files_all
    
  
  return midi_files_sel[:data_len_train], midi_files_sel[data_len_train:(data_len_train + data_len_val)], midi_files_sel[(data_len_train + data_len_val):]

