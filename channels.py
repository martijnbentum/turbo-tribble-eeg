import numpy as np

channels = {'50':'Fp1','36':'Fp2','49':'F7,AF7','37':'F8,AF8','48':'FT7','38':'FT8'}
channels.update({'47':'T7','39':'T8','46':'TP7','40':'TP8','45':'P7,PO7'})
channels.update({'41':'P8,PO8'})
channels.update({'44':'O1','42':'O2','34':'AF3','21':'AF4','33':'F5','22':'F6'})
channels.update({'31':'C5','24':'C4','30':'CP5,P5','25':'CP6,P6','29':'P5,P3,PO3'})
channels.update({'26':'P6,P4,PO4','18':'FC3','10':'FC4','16':'CP3','12':'CP4'})
channels.update({'14':'Pz','1':'Cz','35':'Fp2','8':'Fz','VEOG':'VEOG','HEOG':'HEOG'})

class Montage:
	'''holds all channels, plots channels.'''
	def __init__(self,channels):
		self.name = 'M10'
		self.channels = channels
		self.make_dict()

	def __repr__(self):
		return 'Montage: M10 | ' + ' '.join(self.dict_name.keys())

	def plot(self):
		plt.ion()
		self.figure = plt.figure()
		for channel in self.channels:
			channel.plot()

	def plot_3d(self):
		plt.ion()
		figure = plt.figure()
		ax = figure.add_subplot(projection='3d')
		for channel in self.channels:
			channel.plot_3d(ax)

	def make_dict(self):
		'''dicts to access channels based on name, raw_name and index.'''
		self.dict_name = {}
		self.dict_raw_name= {}
		self.dict_index = {}
		for channel in self.channels:
			self.dict_name[channel.name] = channel
			self.dict_raw_name[channel.raw_name] = channel
			self.dict_index[channel.index] = channel

		

class Channel:
	'''a given EEG channels, name location index.'''
	def __init__(self,line, index):
		self.line = line
		self.raw_name = line[0][0]
		self.index = index
		self.name = channels[self.raw_name]
		self.set_info()

	def __repr__(self):
		m = self.name.ljust(10) 
		if self.name != self.raw_name:
			m += '| ' + self.raw_name.ljust(3)
		if self.x != None:
			m += '| xyz: ' +str(round(self.x,2)).rjust(5)
			m += ' ' + str(round(self.y,2)).rjust(5)
			m += ' ' +str(round(self.z,2)).rjust(5)
			m += ' | phi/theta: ' +str(self.phi).rjust(4)
			m += ' ' +str(self.theta).rjust(4)
		return m

	def set_info(self):
		if self.name in ['VEOG','HEOG']: 
			self.data_channel = False
			self.eye_channel = True
			self.type = 'eye'
			self.x = None
			self.y = None
			self.z = None
			self.theta = None
			self.phi = None
		else:
			self.data_channel = True
			self.eye_channel = False 
			self.type = 'data'
			self.theta= self.line[7][0][0]
			self.phi= self.line[8][0][0]
			if self.theta < 0: self.theta = 360 + self.theta
			if self.phi < 0: self.phi = 360 + self.phi
			self.x = np.cos(np.radians(self.phi)) * np.sin(np.radians(self.theta))
			self.y = np.sin(np.radians(self.phi)) * np.sin(np.radians(self.theta))
			self.z = np.cos(np.radians(self.theta))

	
	def plot(self):
		if self.data_channel:
			plt.scatter(self.x,self.y)
			plt.text(self.x,self.y,self.name)

	def plot_3d(self,ax):
		if self.data_channel:
			ax.scatter(self.x,self.y,self.z)
