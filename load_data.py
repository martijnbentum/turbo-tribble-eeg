'''load eeg data from EEGlab .mat files from the following experiment:
DOI: 10.1016/j.bandl.2014.10.006
'''

from scipy import io
import numpy as np
from matplotlib import pyplot as plt
import glob
import pickle

from channels import Montage, Channel
from stimuli import Stimuli, data_dir


indices = {'nchannels':8,'datapoints':10,'sample_rate':11,'xmin':12,'xmax':13}
indices.update({'times':14,'data':15,'raw_channels':21,'channel_info':23})
indices.update({'raw_events':25,'stats':26})

extract_values_to_number='nchannels,datapoints,sample_rate,xmin,xmax'.split(',')
extract_values_to_vector='times,raw_channels,raw_events,channel_info,stats'.split(',')

	
def load_mat_file(filename):
	return io.loadmat(filename)['EEG'][0][0]

class Participants:
	'''load all eeg data for all participants.'''
	def __init__(self, load_data = True):
		self.fn = glob.glob(data_dir + 'EEG*.mat')
		self.stimuli = Stimuli()
		if load_data: self.load_data()

	def __repr__(self):
		m = 'Participants: ' 
		if hasattr(self,'participants'): m += str(len(self.participants))
		else: m += 'no data loaded'
		return m

	def load_data(self):
		self.participants = []
		self.non_artefact_events = []
		self.non_reject_events = []
		for filename in self.fn:
			print(filename)
			p = Participant(filename,stimuli = self.stimuli)
			self.non_artefact_events.extend(p.non_artefact_events)
			self.non_reject_events.extend(p.non_reject_events)
			self.participants.append(p)

	def pickle(self, filename):
		save_participants(self,filename)


class Participant:
	'''load eeg data and stimuli information from 1 participant.'''
	def __init__(self,filename, load=True, stimuli = None):
		self.filename = filename
		self.pp_id = int(filename.split('EEG')[-1].strip('.mat'))
		if not stimuli: self.stimuli = Stimuli()
		else: self.stimuli = stimuli
		if load: self.load()


	def __repr__(self):
		m = 'participant: '+str(self.pp_id) + ' | events: ' + str(self.nevents)
		return m

	def load(self):
		self.mat_data = load_mat_file(self.filename)
		for name,index in indices.items():
			x = self.mat_data[index]
			if name in extract_values_to_number: x = extract_value(x,to_number=True)
			elif name in extract_values_to_vector: x = extract_value(x,to_vector=True)
			setattr(self,name,x)
		self.make_events()
		self.make_channels()

	def make_events(self):
		self.events, self.non_artefact_events, self.non_reject_events = [], [], []
		sentence_id = None
		for raw_event in self.raw_events:
			event = Event(raw_event, self, sentence_id)
			if event.first_word_in_sentence: 
				if len(self.events) > 0:
					self.events[-1].last_word_in_sentence = True
				sentence_id = event.sentence_id
			self.events.append(event)
			if not event.ok: continue
			if not event.artefact: self.non_artefact_events.append(event)
			if not event.reject: self.non_reject_events.append(event)
		self.nevents = len(self.events)


	def make_channels(self):
		self.channels = []
		for i,rc in enumerate(self.raw_channels):
			self.channels.append(Channel(rc,index = i))
		self.montage = Montage(self.channels)
			
			
class Event:
	'''represents trial in the experiment. 
	the visual presentation of a single word
	'''
	def __init__(self,raw_event,eeg_data, sentence_id= None):
		self.raw_event = raw_event
		self.eeg_data = eeg_data
		self.sentence_id = sentence_id
		self.set_info()
		self.set_artefact_reject()

	def __repr__(self):
		if not self.ok: return 'sentence loading error'
		m =  str(self.word_number).ljust(2) + ' ' + self.word_str.ljust(12)
		m += '| ' + str(self.sentence_id).ljust(3) + ' ' + self.sentence_str
		if self.first_word_in_sentence: m += ' | first word'
		if self.last_word_in_sentence: m += ' | last word'
		return m

	def set_info(self):
		names = 'word_type,latency,urevent'.split(',')
		for i,name in enumerate(names):
			value = extract_value(self.raw_event[i],to_number = True)
			setattr(self,name,value)
		self.sample_point = self.latency
		self.first_word_in_sentence = self.word_type > 50
		self.last_word_in_sentence = False
		if self.word_type - 50 > 0:
			self.sentence_id = self.word_type - 50
		if self.first_word_in_sentence:
			self.word_number = 1
		else:
			self.word_number = self.word_type
		if self.sentence_id != None:
			self.sentence = self.eeg_data.stimuli.sentences_dict[self.sentence_id]
			self.word = self.sentence.words_dict[self.word_number]
			self.word_str = self.word.word
			self.sentence_str = self.sentence.sentence_str
			self.all_lowercase_ascii = self.word.all_lowercase_ascii
			self.ok = True
		else: self.ok = False

	def set_artefact_reject(self):
		if self.ok:
			word_index = self.word.index
			sentence_index = self.sentence.index
			pp_index = self.eeg_data.pp_id - 1
			artefact = self.eeg_data.stimuli.artefact
			reject= self.eeg_data.stimuli.reject
			self.artefact_code = artefact[sentence_index][0][word_index][pp_index]
			self.artefact = True if self.artefact_code == 1 else False
			self.reject_code = reject[sentence_index][0][word_index][pp_index]
			self.reject = True if self.reject_code == 1 else False
		else: self.artefact, self.reject = None,None

	


class EventData:
	def __init__(self, event):
		self.event = event
		self.sample_rate = self.event.eeg_data.sample_rate
		sp = self.event.sample_point
		self.sample_point = sp
		self.baseline_length = 0.1
		self.trial_length= 0.700
		self.start_epoch = sp - int(self.baseline_length * self.sample_rate)
		self.end_epoch = sp + int(self.trial_length * self.sample_rate)
		self.start_offset = 0

	@property
	def baseline(self):
		if hasattr(self,'_baseline'): return self._baseline
		baseline = self.event.eeg_data.data[:,self.start_epoch:self.sample_point]
		assert not has_nan(baseline) 
		self._baseline = baseline
		return self._baseline

	@property
	def baseline_channel_average(self):
		if hasattr(self,'_baseline_channel_average'): 
			return self._baseline_channel_average
		self._baseline_channel_average = np.mean(self.baseline,1)
		return self._baseline_channel_average

	@property
	def baseline_average(self):
		if hasattr(self,'_baseline_average'): return self._baseline_average
		self._baseline_average = np.mean(self.baseline)
		return self._baseline_average

	@property
	def epoch(self):
		if hasattr(self,'_epoch'): return self._epoch
		epoch = self.event.eeg_data.data[:,self.start_epoch:self.end_epoch]
		assert not has_nan(epoch)
		self._epoch = epoch
		return epoch 
		





def extract_value(x, to_number=False, to_vector=False):
	'''helper function to extract data from array in array structure of loaded mat file
	when loading mat file with scipy the is embeded in multiple single dimension 
	np arrays.
	this function extracts the data from these nuisance arrays
		to_number 			extract a single number from np array
		to_vector 			extract a single vector from np array
	'''
	while True:
		if to_number:
			if type(x) == np.ndarray:
				x = x[0]
			else: break
		elif to_vector: 
			if len(x.shape) > 1:
				x = x[0]
			else: break
		elif x.shape == (1,1):
			x = x[0]
		else: break
	return x

def has_nan(number_array_or_matrix):
	'''return true when array or matrix contains a nan value.'''
	if type(number_array_or_matrix) != np.ndarray: 
		return np.isnan(number_array_or_matrix)
	while True:
		number_array_or_matrix= sum(number_array_or_matrix)
		if not type(number_array_or_matrix) == np.ndarray: break
	return np.isnan(number_array_or_matrix)

def find_start_data_vector(vector):
	for i,number in enumerate(vector):
		if not np.isnan(number): return i

def find_start_data_matrix(matrix):
	assert type(matrix[0]) == np.ndarray
	return find_start_data_vector(matrix[0])

def load_participants(filename ='../data/participants.pickle' ):
	with open(filename,'rb') as fin:
		participants = pickle.load(fin)

def save_participants(participants, filename = '../data/participants.pickle' ):
	with open(filename,'wb') as fout:
		participants = pickle.load(participants,fout)
		
