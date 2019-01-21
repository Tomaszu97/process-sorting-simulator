import kivy
kivy.require('1.10.1')
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import ObjectProperty
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView, FileChooserIconView
from kivy.uix.button import Button
from kivy.config import Config
from kivy.clock import Clock
from kivy.graphics import *
from random import randint
from kivy.graphics import Color, Ellipse
from kivy.core.text import Label as CoreLabel
from queue import Queue
from operator import itemgetter
from random import uniform
from math import ceil, floor
from kivy.config import Config
from time import sleep
from functools import partial
import os
from pygame import mixer
from kivy.core.window import Window

#window size, no antialiasing
Config.set('graphics','multisamples',0)
Config.set('graphics', 'width', '1900')
Config.set('graphics', 'height', '950')
Config.write()

class PrecisionSlider(BoxLayout):
	def increase_value(self):
		if (self.ids.slider.value + self.ids.slider.step) <= self.max:
			self.ids.slider.value += self.ids.slider.step

	def decrease_value(self):
		if (self.ids.slider.value - self.ids.slider.step) >= self.min:
			self.ids.slider.value -= self.ids.slider.step



class AnalogValue(BoxLayout):
	def update_from_reg(self):
		self.ids.slider.ids.slider.value = round(self.reg_value * self.step, 1)



class LoadDialog(FloatLayout):
	load = ObjectProperty(None)
	cancel = ObjectProperty(None)


class SaveDialog(FloatLayout):
	save = ObjectProperty(None)
	text_input = ObjectProperty(None)
	cancel = ObjectProperty(None)



class MainLayout(BoxLayout):
	def __init__(self):
		BoxLayout.__init__(self)
		self.proclist = []
		mixer.init()
		self.algorithm_used = 'None'
		x = randint(0,2)
		if  x == 0:
			mixer.music.load('res/unreal superhero.mp3')
		elif x == 1:
			mixer.music.load('res/most awesome song.mp3')
		else:
			mixer.music.load('res/digital insanity.mp3')
		mixer.music.play()


	def get_processes_arrived_in(self, time_start, time_end):
		temp = []	
		for item in self.proclist:
			if item[1] <= time_end and item[1] >= time_start:
				temp.append(item)
		return temp


	def update_gui_from_proclist(self):
		#put data in scrollable table
		proc_count = len(self.proclist)
		self.ids['process_table'].clear_widgets()
		self.ids['process_table'].width = proc_count*100
		for i in range(proc_count):
			templayout = BoxLayout(orientation = 'vertical', size_hint_x = None)
			templayout.add_widget(Label(text = str(self.proclist[i][0]), font_size='20sp'))
			templayout.add_widget(Label(text = str(self.proclist[i][1]), font_size='20sp'))
			templayout.add_widget(Label(text = str(self.proclist[i][2]), font_size='20sp'))
			templayout.add_widget(Label(text = str(self.proclist[i][3]), font_size='20sp'))
			templayout.add_widget(Label(text = str(self.proclist[i][4]), font_size='20sp'))
			templayout.add_widget(Label(text = str(self.proclist[i][5]), font_size='20sp'))
			self.ids['process_table'].add_widget(templayout)


	def generate_data(self):
		proc_count = int(self.ids['process_count_slider'].value)

		#generate processes
		self.proclist.clear()
		for i in range(proc_count):
			#0-PID	1-AT	2-BT	3-CT	4-TAT	5-WT
			self.proclist.append([0,0,0,0,0,0])
			#PID
			self.proclist[i][0] = i
			#AT
			#one after another with doubles
			if i > 0:
				self.proclist[i][1] = randint(self.proclist[i-1][1], self.proclist[i-1][1]+30)
			#BT
			self.proclist[i][2] = randint(5, 50)
			#CT
			self.proclist[i][3] = None
			#TAT
			self.proclist[i][4] = None
			#WT
			self.proclist[i][5] = None

		self.update_gui_from_proclist()

			
	def calculate(self):
		if len(self.proclist) == 0:
			return

		proc_count = len(self.proclist)
		
		#stable sort first by PID and then by AT
		self.proclist.sort(key = itemgetter(0))
		self.proclist.sort(key = itemgetter(1))

		#now calculate the rest depending on chosen algorithm
		if self.ids['algorithm_picker'].text == 'FCFS':
			self.algorithm_used = 'FCFS'
			t = 0
			prevt = 0
			ran_processes = 0
			q = Queue()
			while True:
				#get processes for current time
				current_processes = self.get_processes_arrived_in(prevt, t)
				prevt = t+1

				#put all of them in order in queue
				for item in current_processes:
					q.put(item)

				#run first process from queue, jump to its end
				if q.qsize() != 0:
					proc = q.get()
					t += proc[2]
					proc[3] = t
					proc[4] = proc[3] - proc[1]
					proc[5] = proc[4] - proc[2]
					ran_processes += 1
					if ran_processes >= proc_count:
						break
				else:
					t += 1
				
		if self.ids['algorithm_picker'].text == 'SJF':
			self.algorithm_used = 'SJF'
			t = 0
			prevt = 0
			ran_processes = 0
			q = Queue()
			while True:
				#get processes for current time
				current_processes = self.get_processes_arrived_in(prevt, t)
				prevt = t+1

				#put all of them in order in queue
				for item in current_processes:
					q.put(item)

				#rearrange queue - shortest jobs first
				tempproclist = list(q.queue)
				q.queue.clear()
				tempproclist.sort(key = itemgetter(2))
				for item in tempproclist:
					q.put(item)

				#run first process from queue, jump to its end
				if q.qsize() != 0:
					proc = q.get()
					t += proc[2]
					proc[3] = t
					proc[4] = proc[3] - proc[1]
					proc[5] = proc[4] - proc[2]
					ran_processes += 1
					if ran_processes >= proc_count:
						break
				else:
					t += 1

		if self.ids['algorithm_picker'].text == 'SJF+AGING':
			self.algorithm_used = 'SJF+AGING'
			t = 0
			prevt = 0
			ran_processes = 0
			q = Queue()
			while True:
				#get processes for current time
				current_processes = self.get_processes_arrived_in(prevt, t)
				prevt = t+1

				#put all of them in order in queue
				for item in current_processes:
					q.put(item)

				#rearrange queue - shortest jobs first + aging
				tempproclist = list(q.queue)
				q.queue.clear()

				#SJF
				tempproclist.sort(key = itemgetter(2))
				
				#AGING - if age >=100 then move to the beginning of the queue. if two or more expired at the same time - shortest goes first
				shorttempproclist = []
				for process in tempproclist:
					if (t - process[1]) >= 100:
						shorttempproclist.append(process)
				
				shorttempproclist.sort(key = itemgetter(2))
				
				for process in reversed(shorttempproclist):
					tempproclist.remove(process)
					tempproclist.insert(0, process)

				for item in tempproclist:
					q.put(item)

				#run first process from queue, jump to its end
				if q.qsize() != 0:
					proc = q.get()
					t += proc[2]
					proc[3] = t
					proc[4] = proc[3] - proc[1]
					proc[5] = proc[4] - proc[2]
					ran_processes += 1
					if ran_processes >= proc_count:
						break
				else:
					t += 1

		#now sort by individual completion time
		self.proclist.sort(key = itemgetter(3))

		# #print completion time
		# print(self.proclist[len(self.proclist)-1][3])

		self.update_gui_from_proclist()

		this_widget = self.ids['visualization_widget']
		time_row = self.ids['time_row']
		arrrival_row = self.ids['arrival_row']
		empty_row = self.ids['empty_row']
		burst_row = self.ids['burst_row']
		this_widget.canvas.clear()
		with this_widget.canvas:
			#draw black background
			Color(0.06, 0.07, 0.15)
			Rectangle(pos=this_widget.pos, size=this_widget.size)

			#draw time stamps every 10 ms
			ms_count = ceil(self.proclist[len(self.proclist)-1][3]/100)*100
			#ms_count = round(round(self.proclist[len(self.proclist)-1][3], -2))
			ms_distance = this_widget.width/ms_count
			i=0
			while True:
				if (this_widget.x + (ms_distance*i)) >= (this_widget.x + this_widget.width):
					break
				#green every 100ms
				if i%100 == 0:
					Color(0,1,0.1)
				else:
					Color(0,0.7,1)
				Line(points=[this_widget.x + (ms_distance*i), this_widget.y+this_widget.height-time_row.height, this_widget.x + (ms_distance*i), this_widget.y+this_widget.height], width = 1)
				i += 10
			
			#draw arrival times and burst times with PIDs
			for process in self.proclist:
				Color(uniform(.5,1.), uniform(.5,1.), uniform(.5,1.))
				#AT
				Line(points=[this_widget.x + (ms_distance*process[1]), this_widget.y+burst_row.height+empty_row.height, this_widget.x + (ms_distance*process[1]), this_widget.y+burst_row.height+empty_row.height+arrrival_row.height], width = 1)
				#BT
				Rectangle(pos = (this_widget.x + (ms_distance*(process[1]+process[5])), this_widget.y), size = (ms_distance*process[2],burst_row.height))
				#PID
				mylabel = CoreLabel(text = str(process[0]), font_size = 18, color = (0, 0, 0, 1))
				mylabel.refresh()
				texture = mylabel.texture
				texture_size = list(texture.size)
				Rectangle(texture=texture, size=texture_size, pos = ( ms_distance*process[2]/2 + this_widget.x + (ms_distance*(process[1]+process[5])), this_widget.height/6 + this_widget.y))
				#line connecting both
				Line(points=[this_widget.x+(ms_distance*(process[1]+process[5])), this_widget.y+burst_row.height, this_widget.x+(ms_distance*process[1]), this_widget.y+burst_row.height+empty_row.height], width = 1)


	def on_resize(self):
		Clock.schedule_once(lambda dt: self.calculate())

	def dismiss_popup(self):
		self._popup.dismiss()

		
	def show_load(self):
		content = LoadDialog(load=self.load, cancel=self.dismiss_popup)
		content.ids['filechooser'].path = str(os.getcwd()) + '\\savefiles'
		self._popup = Popup(title="Load file", content=content, size_hint=(0.5, 0.5))
		self._popup.open()


	def show_save(self):
		content = SaveDialog(save=self.save, cancel=self.dismiss_popup)
		content.ids['filechooser'].path = str(os.getcwd()) + '\\savefiles'
		self._popup = Popup(title="Save file", content=content, size_hint=(0.5, 0.5))
		self._popup.open()


	def load(self, path, filename):
		self.proclist.clear()
		with open(os.path.join(path, filename[0])) as stream:
			for line in stream:
				#skip commented lines
				if line[0] == '#':
					continue
				self.proclist.append([int(line.split(',')[0]),int(line.split(',')[1]),int(line.split(',')[2]),None,None,None])
			self.update_gui_from_proclist()
		self.dismiss_popup()


	def save(self, path, filename):
		with open(os.path.join(path, filename), 'w') as stream:
			stream.write('#Process ID, Arrival Time, Burst Time[, Completion Time, TurnAround Time, Waiting Time]\n')
			for process in self.proclist:
				stream.write(str(process[0]))
				stream.write(',')
				stream.write(str(process[1]))
				stream.write(',')
				stream.write(str(process[2]))
				if self.algorithm_used != 'None':
					stream.write(',')
					stream.write(str(process[3]))
					stream.write(',')
					stream.write(str(process[4]))
					stream.write(',')
					stream.write(str(process[5]))
				stream.write('\n')
			
			if self.algorithm_used != 'None':
				avg_wt = 0
				avg_tat = 0
				for process in self.proclist:
					#TAT
					avg_tat += process[4]
					#WT
					avg_wt += process[5]
				avg_tat /= len(self.proclist)
				avg_wt /= len(self.proclist)
				stream.write('#Algorithm used: ' + self.algorithm_used + '\n')
				stream.write('#Average Waiting Time: ' + str(avg_wt) + '\n')
				stream.write('#Average TurnAround Time: ' + str(avg_tat) + '\n')
			
		self.dismiss_popup()




Builder.load_file('kv/layout.kv')



class MyApp(App):
	def build(self):
		self.icon = 'res/icon.ico'
		m = MainLayout()
		Window.bind(on_resize=lambda a,b,c: m.on_resize())
		return m



if __name__ == '__main__':
	MyApp().run()