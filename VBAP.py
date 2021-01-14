# -*- coding: utf-8 -*-
"""
Created on Sun Sep 13 09:59:47 2020

@author: User
"""

import numpy as np
from ai import cs #Cartesian to spherical
from scipy.spatial import Delaunay
import sounddevice as sd
import scipy.io.wavfile as wav

from matplotlib import path

c=343

def pad_along_axis(array: np.ndarray, target_length: int, axis: int = 0):

    pad_size = target_length - array.shape[axis]

    if pad_size <= 0:
        return array

    npad = [(0, 0)] * array.ndim
    npad[axis] = (0, pad_size)
    return np.pad(array, pad_width=npad, mode='constant', constant_values=0)

def play_vbap(ls_list,src_list,vbap_matrix):
    #test
    # duration = 5
    # Fs= 44100
    # time = np.arange(0,duration,1/Fs)
    # # data =  np.sin(2*np.pi*1000*time)
    #test
    
    len_max = 0
   
    for src in src_list:
         #get the file for each src
        Fs, src.file = wav.read(src.filename)
        
        if src.file.ndim>1: #Passage en mono
            src.file = (np.sum(src.file, axis=1)/src.file.shape[1]).astype('int16')
            src.file = src.file.reshape((src.file.size,1))
        else:
            src.file = src.file.reshape((src.file.size,1))
    
        # get the max length
        if len_max < src.file.size:
            len_max = src.file.size
    
    all_src = np.array([])
    #pad with zeros and concatenate all
    for src in src_list:
        if len_max > src.file.size:
            src.file = np.pad(src.file,((0,len_max-src.file.size),(0,0)),'constant')
        if all_src.size == 0:
            all_src = src.file
        else:
            all_src = np.append(all_src,src.file,axis=1)
    
    #Create one wav file per loudspeaker and create the array of index loudspeaker
    i=0
    index_ls = []
    playable_array = np.array([])
    for ls in ls_list:
        ls.file =  (np.sum(all_src*vbap_matrix[:,i],axis=1)/3).astype('int16')
        ls.file = (ls.file*ls.nom_gain).astype('int16') #nominal gain
        ls.file = np.pad(ls.file,(int(ls.nom_delay*Fs),0),'constant')[:ls.file.size] #nominal delay
        
        if playable_array.size == 0:
            playable_array = ls.file.reshape((ls.file.size,1))
        else:
            playable_array = np.append(playable_array,ls.file.reshape((ls.file.size,1)),axis=1)
        
        if ls.soundcard_output != '':
            index_ls.append(int(ls.soundcard_output))
        else:
            playable_array=np.delete(playable_array,i,axis=1)
        i+=1
         
    sd.play(playable_array,mapping=index_ls)
    
    
    
    ###test2
    # data=np.array([])
    # len_max=0
    
    # for src in src_list:
    #     Fs,data_temp = wav.read(src.file)
    #     if data_temp.shape[1]>1: #Passage en mono
    #         data_temp = (np.sum(data_temp, axis=1)/data_temp.shape[1]).astype('int16')
        
    #     if data.size==0: #1er fichier
    #         data = data_temp.reshape((data_temp.size,1))
    #         len_max = data_temp.size
    #     else:
    #         if len_max < data_temp.size: #pad with zeros if the file have different size
    #             len_max = data_temp.size
    #             print(len_max-data.shape[0])
    #             data = pad_along_axis(data, len_max,axis=0) 
    #         else:
    #             data_temp = pad_along_axis(data_temp, len_max,axis=0)
    #         data = np.append(data,data_temp.reshape((data_temp.size,1)),axis=1)
    # print(data.shape)        
    # sd.play(data,Fs,[1,1])
    pass

def distanceToOrigin(point,x=0,y=0,z=0):
    
    return np.sqrt((x-point.position_x)**2
                  + (y-point.position_y)**2
                  + (z-point.position_z)**2)


def computeNomParam(ls,ls_list):
    
        global c
        d_max = max(map(distanceToOrigin, ls_list))
        ls.nom_gain = float(distanceToOrigin(ls)/d_max)
        ls.nom_delay = float((d_max-distanceToOrigin(ls))/c)
        
def computeAllNominal(ls_list):
    
    for ls in ls_list:
        computeNomParam(ls,ls_list)
        
def find_triplet(src,ls_list):

        # distance_list = []
        # triplet = []
        
        # for ls in ls_list:
        #     distance_list.append(distanceToOrigin(ls,x=src.position_x,y=src.position_y,z=src.position_z))
        
        # d1 = sorted(distance_list)[0]
        # d2 = sorted(distance_list)[1]
        # d3 = sorted(distance_list)[2]
        
        # for ls in ls_list:
        #     if distanceToOrigin(ls,x=src.position_x,y=src.position_y,z=src.position_z)==d1 or distanceToOrigin(ls,x=src.position_x,y=src.position_y,z=src.position_z)==d2 or distanceToOrigin(ls,x=src.position_x,y=src.position_y,z=src.position_z)==d3:
        #         triplet.append(ls)
        # src.loudspeaker_triplet = triplet
        
        src.loudspeaker_triplet =[]
        
        projection_plan(src,ls_list)
        
        tri = Delaunay(np.array([[ls.position_x_proj for ls in ls_list], [ls.position_y_proj for ls in ls_list]]).T)
        for s in tri.simplices:
            polygon = path.Path([(ls_list[s[0]].position_x_proj,ls_list[s[0]].position_y_proj),
                              (ls_list[s[1]].position_x_proj,ls_list[s[1]].position_y_proj),
                              (ls_list[s[2]].position_x_proj,ls_list[s[2]].position_y_proj)])
            if polygon.contains_points([[src.position_x_proj,src.position_y_proj]]):
                src.loudspeaker_triplet = [ls_list[s[0]],ls_list[s[1]],ls_list[s[2]]]
        
        
        
        if len(src.loudspeaker_triplet) ==0:
            distance_list = []
            triplet = []
            
            for ls in ls_list:
                distance_list.append(distanceToOrigin(ls,x=src.position_x,y=src.position_y,z=src.position_z))
            
            d1 = sorted(distance_list)[0]
            d2 = sorted(distance_list)[1]
            d3 = sorted(distance_list)[2]
            
            for ls in ls_list:
                if distanceToOrigin(ls,x=src.position_x,y=src.position_y,z=src.position_z)==d1 or distanceToOrigin(ls,x=src.position_x,y=src.position_y,z=src.position_z)==d2 or distanceToOrigin(ls,x=src.position_x,y=src.position_y,z=src.position_z)==d3:
                    triplet.append(ls)
            src.loudspeaker_triplet = triplet
            
            
        print(src.name)
        for ls in src.loudspeaker_triplet:
            print(ls.name)
        
        
def projection_plan(src,ls_list,chg_proj=1):
    
    dmax = max(map(distanceToOrigin, ls_list))
    max_norm_ls=0

    distance,theta,phi=cs.cart2sp(src.position_x, src.position_y, src.position_z)
    x,y,z = cs.sp2cart(dmax,theta,phi)
    src.position_x_nom, src.position_y_nom, src.position_z_nom = float(x),float(y),float(z) 
    with np.errstate(all='raise'):
        try:
            src.position_x_proj = src.position_x/(dmax-src.position_z_nom*chg_proj)
            src.position_y_proj = src.position_y/(dmax-src.position_z_nom*chg_proj)
            
            for ls in ls_list:
                distance,theta,phi=cs.cart2sp(ls.position_x, ls.position_y, ls.position_z)
                x,y,z = cs.sp2cart(dmax,theta,phi)
                ls.position_x_nom, ls.position_y_nom, ls.position_z_nom = float(x),float(y),float(z) 
            
                ls.position_x_proj = ls.position_x_nom/(dmax-ls.position_z_nom*chg_proj)
                ls.position_y_proj = ls.position_y_nom/(dmax-ls.position_z_nom*chg_proj)
                # print(np.linalg.norm([src.position_x_proj,src.position_y_proj]))
                if np.linalg.norm([ls.position_x_proj,ls.position_y_proj]) > max_norm_ls:
                    max_norm_ls = np.linalg.norm([ls.position_x_proj,ls.position_y_proj])
            if np.linalg.norm([src.position_x_proj,src.position_y_proj]) > max_norm_ls:
                raise
        except:
            projection_plan(src, ls_list,chg_proj=-1)
            
        
def find_alltriplets(src_list,ls_list):
    
    for src in src_list:
        find_triplet(src,ls_list)
        
def computeVBAP(src_list,ls_list):
    
    #Initialisation de la matrice de gains
    vbap_matrix = np.zeros((len(src_list),len(ls_list)))
    
    #Projete tout les loudspeaker sur une sphere
    d_max = max(map(distanceToOrigin, ls_list))
    for ls in ls_list:
        distance,theta,phi=cs.cart2sp(ls.position_x, ls.position_y, ls.position_z)
        x,y,z = cs.sp2cart(d_max,theta,phi)
        ls.position_x_nom, ls.position_y_nom, ls.position_z_nom = float(x),float(y),float(z) 
    
    i=0
    #Projete les sources aussi
    for src in src_list:
        distance,theta,phi=cs.cart2sp(src.position_x, src.position_y, src.position_z)
        x,y,z = cs.sp2cart(d_max,theta,phi)
        src.position_x_nom, src.position_y_nom, src.position_z_nom = float(x),float(y),float(z) 
     
        #Definition des vecteurs
        
        #basis vector
        l1 = np.zeros((3,1))
        l1[0,0] = src.loudspeaker_triplet[0].position_x_nom 
        l1[1,0] = src.loudspeaker_triplet[0].position_y_nom 
        l1[2,0] = src.loudspeaker_triplet[0].position_z_nom 
    
        l2 = np.zeros((3,1))
        l2[0,0] = src.loudspeaker_triplet[1].position_x_nom 
        l2[1,0] = src.loudspeaker_triplet[1].position_y_nom 
        l2[2,0] = src.loudspeaker_triplet[1].position_z_nom 
        
        l3 = np.zeros((3,1))
        l3[0,0] = src.loudspeaker_triplet[2].position_x_nom  
        l3[1,0] = src.loudspeaker_triplet[2].position_y_nom 
        l3[2,0] = src.loudspeaker_triplet[2].position_z_nom 
        
        #vector to source
        p = np.zeros((3,1))
        p[0,0] = src.position_x_nom
        p[1,0] = src.position_y_nom
        p[2,0] = src.position_z_nom
        
        basis = np.reshape(np.array((l1,l2,l3)),(3,3)) #basis matrix 
    
        gain_vector = np.reshape(p.T @ np.linalg.inv(basis),3)
        
        
        #scaling
        gain_vector = np.sqrt(src.volume)*gain_vector/np.sqrt(gain_vector[0]**2 + gain_vector[1]**2 + gain_vector[2]**2)
        gain_vector = gain_vector.clip(min=0)
        
        vbap_matrix[i][ls_list.index(src.loudspeaker_triplet[0])]=gain_vector[0]
        vbap_matrix[i][ls_list.index(src.loudspeaker_triplet[1])]=gain_vector[1]
        vbap_matrix[i][ls_list.index(src.loudspeaker_triplet[2])]=gain_vector[2]
        
        i+=1
        
    print(vbap_matrix)
    return(vbap_matrix)