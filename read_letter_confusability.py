import pandas as pd
import string

feature_dict = {'descender':list('gjpqy'),'ascender':list('bdfhiklt')}
feature_dict['oblique'] = list('kvwxyz')
feature_dict['round'] = list('bcdgopq')
feature_dict['arch'] = list('hmnru')

def load_confusability_matrix(filename):
	output = pd.read_csv(filename, header = None)
	output.columns = list(string.ascii_lowercase)
	output.index = list(string.ascii_lowercase)
	for letter in string.ascii_lowercase:
		output[letter] = output[letter].astype(int)
	return output

def make_confusability_dict():
	d = {}
	for f in 'left,middle,right'.split(','):
		filename = '../'+f+'_cm.csv'
		d[f] = load_confusability_matrix(filename)
	return d

def make_features():
	output = []
	for name in feature_dict.keys():
		output.append(Feature(name))
	

class Alphabet:
	def __init__(self):
		self.features = make_features()
		self.confusability_dict = make_confusability_dict() 
		self._make_letter_positions()

	def _make_letter_positions(self):
		for position_name in 'left,middle,right'.split(','):
			setattr(self,position_name,Position(position_name,self))


class Position:
	def __init__(self,name, alphabet):
		self.name = name
		self.alphabet = alphabet
		self.cm = alphabet.confusability_dict[name]
		self._make_letters()

	def _make_letters(self):
		for letter in string.ascii_lowercase:
			row_index = string.ascii_lowercase.index(letter)
			column = self.cm[letter]
			row = self.cm[row_index:row_index+1]
			setattr(self,letter,Letter(letter,column,row,self))


class Letter:
	def __init__(self,name,cm_column,cm_row,position):
		self.name = name
		self.cm_column = cm_column
		self.cm_row = cm_row
		self._set_info()

	def _set_info(self):
		#probability list of reporting a letter being shown this class ie self.name
		self.prob_column =self.cm_column / sum(self.cm_column)
		#probability list of reportin this class (ie self.name) shown another letter
		row = self.cm_row.values[0]
		self.prob_row =row / sum(row)
		self.prob_dict_column= {}
		self.prob_dict_row = {}
		for i,letter in enumerate(string.ascii_lowercase):
			if self.prob_column[letter] > 0:
				# the participant was shown the letter of this class ie self.name
				self.prob_dict_column[letter] = self.prob_column[letter]
			if self.prob_row[i] > 0:
				# the participant was reporting the letter of this class ie self.name
				self.prob_dict_row[letter] = self.prob_row[i]

class Feature:
	def __init__(self,name):
		self.name = name
		self.letters = feature_dict[name]
		
	@property
	def has_feature(self,letter):
		return letter in self.letters

	


