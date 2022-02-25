from scipy import io
import numpy as np
from channels import Montage, Channel

from matplotlib import pyplot as plt


indices = {'nchannels':8,'datapoints':10,'sample_rate':11,'xmin':12,'xmax':13}
indices.update({'times':14,'data':15,'raw_channels':21,'channel_info':23})
indices.update({'raw_events':25,'stats':26})

extract_values_to_number='nchannels,datapoints,sample_rate,xmin,xmax'.split(',')
extract_values_to_vector='times,raw_channels,raw_events,channel_info,stats'.split(',')

	
def load_mat_file(filename):
	return io.loadmat(filename)['EEG'][0][0]

class Participant:
	'''load eeg data from EEGlab .mat files from the following experiment:
	DOI: 10.1016/j.bandl.2014.10.006
	'''
	def __init__(self,filename, load=True):
		self.filename = filename
		self.pp_id = int(filename.strip('EEG').strip('.mat'))
		self.stimuli = Stimuli()
		if load: self.load()

	def load(self):
		self.mat_data = load_mat_file(self.filename)
		print(len(self.mat_data))
		for name,index in indices.items():
			x = self.mat_data[index]
			if name in extract_values_to_number: x = extract_value(x,to_number=True)
			elif name in extract_values_to_vector: x = extract_value(x,to_vector=True)
			setattr(self,name,x)
		self.make_events()
		self.make_channels()

	def make_events(self):
		self.events = []
		nword_in_sentence = None
		sentence_id = None
		for raw_event in self.raw_events:
			event = Event(raw_event, self, nword_in_sentence, sentence_id)
			if event.first_word_in_sentence: 
				nword_in_sentence = 2
				if len(self.events) > 0:
					self.events[-1].last_word_in_sentence = True
				sentence_id = event.sentence_id
			elif type(nword_in_sentence) == int: nword_in_sentence +=1
			self.events.append(event)
		self.nevents = len(self.events)

	def make_channels(self):
		self.channels = []
		for i,rc in enumerate(self.raw_channels):
			self.channels.append(Channel(rc,index = i))
		self.montage = Montage(self.channels)
			
			
	

	def __repr__(self):
		m = 'participant: '+str(self.pp_id) + ' | events: ' + str(self.nevents)
		return m

class Event:
	def __init__(self,raw_event,eeg_data, nword_in_sentece = None, sentence_id= None):
		self.raw_event = raw_event
		self.eeg_data = eeg_data
		names = 'word_type,latency,urevent'.split(',')
		for i,name in enumerate(names):
			value = extract_value(raw_event[i],to_number = True)
			setattr(self,name,value)
		self.sample_point = self.latency
		self.first_word_in_sentence = self.word_type > 50
		self.last_word_in_sentence = False
		if self.word_type - 50 > 0:
			self.sentence_id = self.word_type - 50
		else: self.sentence_id = sentence_id
		if self.first_word_in_sentence:
			self.word_number = 1
		else:
			self.word_number = self.word_type
		self.sentence = eeg_data.stimuli.sentences_dict[self.sentence_id]
		self.word = self.sentence.words_dict[self.word_number]
		self.word_str = self.word.word
		self.sentence_str = self.sentence.sentence_str
		self.all_lowercase_ascii = self.word.all_lowercase_ascii

	def __repr__(self):
		m =  str(self.word_number).ljust(2) + ' ' + self.word_str.ljust(12)
		m += '| ' + str(self.sentence_id).ljust(3) + ' ' + self.sentence_str
		if self.first_word_in_sentence: m += ' | first word'
		if self.last_word_in_sentence: m += ' | last word'
		return m
		

class Stimuli:
	def __init__(self):
		self.mat = io.loadmat('stimuli_erp.mat')
		self.artefact = self.mat['artefact']
		self.reject = self.mat['reject']
		self.raw_sentences = self.mat['sentences']
		self.clean_sentences()

	def clean_sentences(self):
		self.word_lists= []
		self.sentences = []
		self.sentences_dict = {}
		for i,x in enumerate(self.raw_sentences):
			x = x[0][0]
			words = []
			for item in x:
				words.append(item[0])
			self.word_lists.append(words)
			sentence = Sentence(i+1,words)
			self.sentences.append(sentence)
			self.sentences_dict[i+1] = sentence
		


class Sentence:
	def __init__(self,number,words):
		self.number = number
		self.word_list= words
		self.words = []
		for i,word in enumerate(words):
			if i == 0: first =True
			else: first = False
			if i == len(words) -1: last = True
			else: last = False
			self.words.append(Word(i+1,word,first,last))
		self.nwords = len(self.words)
		self.special_word_numbers= []
		self.words_dict ={}
		for word in self.words:
			if word.contains_special_character: 
				self.special_word_numbers.append(word.number)
			self.words_dict[word.number] = word
		self.sentence_str = ' '.join(self.word_list)

	def __repr__(self):
		m = 'number: ' + str(self.number) + ' | ' + self.sentence_str
		m += ' | ' + str(self.nwords)
		return m

class Word:
	def __init__(self,number,word,first=False,last=False):
		self.number = number
		self.word = word
		self.first = first
		self.last = last
		self._check_characters()

	def _check_characters(self):
		self.special_characters = []
		for char in ".',-":
			if char in self.word: 
				self.special_characters.append(char)
		self.contains_uppercase = False
		for char in self.word:
			if char.isupper(): self.contains_uppercase = True
		if self.contains_uppercase or len(self.special_characters) > 0: 
			self.all_lowercase_ascii= False
		else: 
			self.all_lowercase_ascii= True
		self.contains_special_character = len(self.special_characters) > 0
		self.nchars = len(self.word)
			
	
	def __repr__(self):
		m = 'number: ' + str(self.number).ljust(3) + ' | ' + self.word.ljust(12)
		if self.contains_special_character: m += ' | special'
		if self.contains_uppercase: m += ' | uppercase'
		if self.all_lowercase_ascii: m += ' | ok'
		if self.first: m += ' | first word'
		if self.last: m += ' | last word'
		return m


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
