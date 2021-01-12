# -*- coding: utf-8 -*-
"""
Created on Tue Aug 18 18:09:14 2020

@author: vlaboure
"""
import os
os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'    # A ajouter pour que ca marche

import numpy as np
import sounddevice as sd

import kivy
from kivy.config import Config
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
from kivy.lang.builder import Builder
from kivy.app import App

from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import ObjectProperty, ListProperty
from kivy.uix.label import Label
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.clock import Clock

# kivy3
from kivy3 import Renderer, Scene
from kivy3 import PerspectiveCamera

# geometry
from kivy3.extras.geometries import BoxGeometry
from kivy3 import Material, Mesh

import VBAP

def select_output(self):
    self.ls.soundcard_output = self.text
    self.popup.parent.parent.parent.parent.dismiss()
    pass

def select_soundcard(self):
    sd.default.device = self.text
    self.popup.clear_widgets()
    show_output(self.popup,self.ls)
    
def show_soundcard(self):
    self.popup.clear_widgets()
    lst_devices = sd.query_devices()

    for dev in lst_devices:
        if dev["max_output_channels"] > 0:
            btn = Button(text='{} {}'.format(dev['name'],sd.query_hostapis(dev['hostapi'])['name']),
                                         on_press = select_soundcard)
            btn.popup =self.popup
            btn.ls =self.ls
            self.popup.add_widget(btn)
            
    pass

def show_output(popup,ls):
    popup.add_widget(Label(text='{}, {}'.format(sd.query_hostapis(sd.query_devices(device=sd.default.device[1])['hostapi'])['name'],sd.query_devices(device=sd.default.device[1])['name'])))
    for i in range(1,sd.query_devices(device = sd.default.device[1])['max_output_channels']+1):
        btn = Button(text =str(i))
        btn.ls = ls
        btn.popup = popup
        btn.bind(on_press = select_output)
        popup.add_widget(btn)
    btn = Button(text='Change soundcard', on_press=show_soundcard)
    btn.popup = popup
    btn.ls = ls
    popup.add_widget(btn)

class View3D(BoxLayout):
    
    prev_list_source = []
    
    def _adjust_aspect(self, *args):
        rsize = self.renderer.size
        aspect = rsize[0] / float(rsize[1])
        self.renderer.camera.aspect = aspect
    
    def __init__(self,**kwargs):
        # create renderer
        self.renderer = Renderer()
        self.renderer.set_clear_color((.2, .2, .2, 1.))
    
        # create scene
        self.scene = Scene()
        self.scene.add(Mesh(
                            geometry=BoxGeometry(.5, .5, .5),
                            material=Material(color=(0., 1., 0.), diffuse=(1., 1., 0.),
                            specular=(.35, .35, .35))
                            ))
        
        # create camera for scene
        self.camera = PerspectiveCamera(
            fov=75,    # distance from the screen
            aspect=0,  # "screen" ratio
            near=0.01,    # nearest rendered point
            far=100    # farthest rendered point
        )#default position 0,0,0
        
        # self.camera.look_at([0,0,0])
        
        self.camera.pos.x = 0.
        self.camera.pos.y = 2.
        self.camera.pos.z = 5.
        self.camera.bind_to(self.renderer)
        # set renderer ratio is its size changes
        # e.g. when added to parent
        
        self.renderer.bind(size=self._adjust_aspect)
        self.renderer.render(self.scene, self.camera)
        
        super(View3D,self).__init__(**kwargs)
        self.add_widget(self.renderer)
        
        Clock.schedule_interval(self.rotate_cam,1/60)
        
    def rotate_cam(self,time):
        if False:
            phi = np.angle(self.camera.pos.x+1j*self.camera.pos.z)
            mod = np.abs(self.camera.pos.x+1j*self.camera.pos.z)
            delta = 2*np.pi/360
    
            self.camera.pos.x=float(mod*np.cos(delta+phi))
            self.camera.pos.z=float(mod*np.sin(delta+phi))
   
        pass    
        
    def refresh_3Dview(self,list_source,list_loudpeaker):
        
        self.remove_widget(self.renderer)
        self.renderer = Renderer()
        self.renderer.set_clear_color((.2, .2, .2, 1.))
        self.scene = Scene()
        self.scene.add(Mesh(
                            geometry=BoxGeometry(.1, .1, .1),
                            material=Material(color=(0., 1., 0.), diffuse=(1., 1., 0.),
                            specular=(.35, .35, .35))
                            ))

        cube_geo = BoxGeometry(.1, .1, .1)
        src_mat = Material(color=(1., 0., 0.), diffuse=(1., 1., 0.),
                            specular=(1, .35, .35))
        ls_mat = Material(color=(0., 0., 1.), diffuse=(1., 1., 0.),
                            specular=(.35, .35, .35))
        for src in list_source:
            src.cube3d = Mesh(
                            geometry=cube_geo,
                            material=src_mat
                            )
            src.cube3d.position.x=src.position_x
            src.cube3d.position.y=src.position_z
            src.cube3d.position.z=src.position_y
            self.scene.add(src.cube3d)
        
        for ls in list_loudpeaker:
            ls.cube3d = Mesh(
                            geometry=cube_geo,
                            material=ls_mat
                            )
            ls.cube3d.position.x=ls.position_x
            ls.cube3d.position.y=ls.position_z
            ls.cube3d.position.z=ls.position_y
            self.scene.add(ls.cube3d)
        self.renderer.render(self.scene, self.camera)
        self.add_widget(self.renderer)
        pass
    
    def on_touch_down(self, touch):
        if touch.button == 'left':
            self.prev_pos_left = touch.pos
        if touch.button == 'right':
            self.prev_pos_right = touch.pos
        if touch.is_mouse_scrolling:
            if touch.button == 'scrolldown':
                self.camera.position.z=1.1*self.camera.position.z

            elif touch.button == 'scrollup':
                self.camera.position.z=0.9*self.camera.position.z
     
    def on_touch_move(self,touch): 

        if touch.button == 'left':
            move_x = (touch.pos[0] - self.prev_pos_left[0])/self.size[0]
            move_y = (touch.pos[1] - self.prev_pos_left[1])/self.size[1]
            
            delta= 2*np.pi*move_x
            phi = np.angle(self.camera.pos.x+1j*self.camera.pos.z)
            mod = np.abs(self.camera.pos.x+1j*self.camera.pos.z)
            self.camera.pos.x=float(mod*np.cos(delta+phi))
            self.camera.pos.z=float(mod*np.sin(delta+phi))
            
            delta= 2*np.pi*move_y
            phi = np.angle(self.camera.pos.y+1j*self.camera.pos.z)
            mod = np.abs(self.camera.pos.y+1j*self.camera.pos.z)
            self.camera.pos.y=float(mod*np.cos(delta+phi))
            self.camera.pos.z=float(mod*np.sin(delta+phi))
               
            self.prev_pos_left = touch.pos
        
        if touch.button == 'right':
            move_x = (touch.pos[0] - self.prev_pos_right[0])/self.size[0]
            move_y = (touch.pos[1] - self.prev_pos_right[1])/self.size[1]
              
            self.camera.pos.y=(1+move_y)*self.camera.pos.y
            self.camera.pos.x=(1+move_x)*self.camera.pos.x
            
            self.camera.look_at([self.camera._look_at[0]+move_x*self.camera.pos.x,
                self.camera._look_at[1]-move_y*self.camera.pos.y,
                0])
            
            self.prev_pos_right = touch.pos
            
    def on_touch_up(self, touch):
        pass

        
class LabelButton(ButtonBehavior,Label):
    pass

class ScreenManag(ScreenManager):
    pass

class Main_screen(Screen):
    pass

class Sources_screen(Screen):
    n_sources = ObjectProperty(0)
    list_source = ListProperty()
    
    def save_conf(self,path,popup):
        file = open(path,'w+')
        file.write("#### Sources configuration #### \n")
        for src in self.list_source:
            file.write(str(src.name) + ';'
                    + str(src.position_x) + ';'
                    + str(src.position_y) + ';'
                    + str(src.position_z) + ';'
                    + str(src.volume) + ';'
                    + str(src.filename) + ';' + '\n')
        file.close()
        popup.dismiss()
    
    def open_conf(self,instance,selection,position):
              
        file = open(selection and selection[0] or '','r')
        file_lines = file.readlines()
        
        for src in self.list_source:
            self.ids['scrollbox'].remove_widget(src)
        
        self.list_source.clear()
        self.n_sources = 0
        
        for line in file_lines[1:]:
                
            fields = line.split(';')
            
            self.n_sources=self.n_sources+1
            widget=Source_layout()
            widget.sources_screen = self

            
            widget.name = fields[0]
            widget.ids.x_input.text = fields[1]
            widget.ids.y_input.text = fields[2]
            widget.ids.z_input.text = fields[3]
            widget.ids.slider.value = float(fields[4])
            widget.filename = fields[5]
            
            self.list_source.append(widget)
            self.ids.scrollbox.add_widget(widget,index=1)
            
            instance.parent.parent.parent.dismiss()
        file.close()

class Loudspeakers_screen(Screen):
    n_loudspeakers = ObjectProperty(0)
    list_loudspeaker = ListProperty()
    
    def save_conf(self,path,popup):
        file = open(path,'w+')
        file.write("#### Lourdspeakers configuration #### \n")
        for ls in self.list_loudspeaker:
            file.write(str(ls.name) + ';'
                    + str(ls.position_x) + ';'
                    + str(ls.position_y) + ';'
                    + str(ls.position_z) + ';'
                    + str(ls.nom_gain) + ';'
                    + str(ls.nom_delay) + ';'
                    + str(ls.soundcard_output) + ';' + '\n')
        file.close()
        popup.dismiss()
    
    def open_conf(self,instance,selection,position):
              
        file = open(selection and selection[0] or '','r')
        file_lines = file.readlines()
        
        for src in self.list_loudspeaker:
            self.ids['scrollbox'].remove_widget(src)
        
        self.list_loudspeaker.clear()
        self.n_loudspeakers = 0
        
        for line in file_lines[1:]:
                
            fields = line.split(';')
            
            self.n_loudspeakers=self.n_loudspeakers+1
            widget=Loudspeaker_layout()
            widget.loudspeakers_screen = self

            
            widget.name = fields[0]
            widget.ids.x_input.text = fields[1]
            widget.ids.y_input.text = fields[2]
            widget.ids.z_input.text = fields[3]
            widget.ids.slider_gain.value = float(fields[4])
            widget.ids.slider_delay.value = float(fields[5])
            widget.ids.soundcard_txt_input.text = fields[6]
            
            self.list_loudspeaker.append(widget)
            self.ids.scrollbox.add_widget(widget,index=1)
            
            instance.parent.parent.parent.dismiss()
        file.close()
    pass

class Source_layout(BoxLayout):
    
    name = ObjectProperty('Source')
    
    position = ListProperty([0.0,0.0,0.0])
    position_x = ObjectProperty(0.0)
    position_y = ObjectProperty(0.0)
    position_z = ObjectProperty(0.0)
    
    volume = ObjectProperty(1)
    
    filename = ObjectProperty('')
    
    cube3d= ObjectProperty()
    
    loudspeaker_triplet = ListProperty()
    
    def on_position_x(self,instance,value):
        try:
            value = float(value)
        except:
            value = 0.0
        self.position_x = value
        self.position[0] = value
    def on_position_y(self,instance,value):
        try:
            value = float(value)
        except:
            value = 0.0
        self.position_y = value
        self.position[1] = value
    def on_position_z(self,instance,value):
        try:
            value = float(value)
        except:
            value = 0.0
        self.position_z = value
        self.position[2] = value
        
        
        
    pass

class Loudspeaker_layout(BoxLayout):
    name = ObjectProperty('Loudspeaker')
    
    position = ListProperty([0,0,0])
    position_x = ObjectProperty(0)
    position_y = ObjectProperty(0)
    position_z = ObjectProperty(0)
    
    nom_gain = ObjectProperty(1.)
    nom_delay = ObjectProperty(0) #second
    
    soundcard_output = ObjectProperty('')
    
    cube3d= ObjectProperty()

    
    
    def on_position_x(self,instance,value):
        try:
            value = float(value)
        except:
            value = 0
        self.position_x = value
        self.position[0] = value
    def on_position_y(self,instance,value):
        try:
            value = float(value)
        except:
            value = 0
        self.position_y = value
        self.position[1] = value
    def on_position_z(self,instance,value):
        try:
            value = float(value)
        except:
            value = 0
        self.position_z = value
        self.position[2] = value
        

    pass

class VBAPApp(App):
    def build(self):
        return ScreenManag()
    
    
if __name__ == '__main__':
    Builder.load_file('GUI2.kv')
    VBAPApp().run()