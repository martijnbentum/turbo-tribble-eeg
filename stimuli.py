'''classes to represent the stimuli of the EEG experiment.
DOI: 10.1016/j.bandl.2014.10.006
'''
from scipy import io

data_dir = '../data/'

class Stimuli:
	'''loads all stimuli related information in the corresponding .mat file.'''
	def __init__(self):
		self.mat = io.loadmat(data_dir + 'stimuli_erp.mat')
		self.artefact = self.mat['artefact']
		self.reject = self.mat['reject']
		self.raw_sentences = self.mat['sentences']
		self.clean_sentences()

	def __repr__(self):
		m = 'Stimuli | sentences: ' + str( self.nsentences)
		m += ' | words: ' + str( self.nwords )
		return m
		
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
			sentence = Sentence(i+1,words,self)
			self.sentences.append(sentence)
			self.sentences_dict[i+1] = sentence
		self.nsentences = len(self.sentences)
		self.nwords = sum([len(wl) for wl in self.word_lists])


class Sentence:
	'''represents 1 sentence from the experiment.
	Participants viewed sentences word by word.'''
	def __init__(self,number,words,stimuli):
		self.number = number
		self.index = number -1
		self.word_list= words
		self.stimuli = stimuli
		self.words = []
		for i,word in enumerate(words):
			if i == 0: first =True
			else: first = False
			if i == len(words) -1: last = True
			else: last = False
			self.words.append(Word(i+1,word,self,first,last))
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
	def __init__(self,number,word,sentence,first=False,last=False):
		self.number = number
		self.index = number - 1
		self.word = word
		self.sentence = sentence
		self.first = first
		self.last = last
		self._check_characters()

	def __repr__(self):
		m = 'number: ' + str(self.number).ljust(3) + ' | ' + self.word.ljust(12)
		if self.contains_special_character: m += ' | special'
		if self.contains_uppercase: m += ' | uppercase'
		if self.all_lowercase_ascii: m += ' | ok'
		if self.first: m += ' | first word'
		if self.last: m += ' | last word'
		return m

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
			
	
