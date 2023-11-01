#!/usr/bin/env python
# coding: utf-8

# In[28]:


import n2v
import tensorflow as tf
import imageio
import matplotlib.pyplot as plt
import ipywidgets as widgets
import numpy as np
import pydicom
import os
from skimage.filters import threshold_otsu
from scipy.signal import find_peaks
import numpy as np
import cv2
import random
from n2v.models import N2VConfig, N2V
from n2v.internals.N2V_DataGenerator import N2V_DataGenerator
import warnings
from intensity_normalization.normalize.nyul import NyulNormalize
import SimpleITK as sitk


# In[29]:


class MED_PREP:
    Organ_Dic = {'Brain': [80, 40], 'head subdural': [215, 75], 'head stroke1': [8, 32], 'head stroke2': [40, 40],
                 'head temporal bones': [2800, 600], 'head soft tissues': [375, 40],
                 'Lungs': [1500, -600], 'chest mediastinum': [350, 50], 'abdomen soft tissues': [400, 50],
                 'liver': [150, 30], 'spinal soft tissues': [250, 50], 'spinal bone': [1800, 400], 'Bone': [2000, 300],'None':[4000,0]}
    def full_prep(self,input_,organ,denoising=False):
        """
        This function performs full preprocessing of a CT and MRI scan.
        organ:the name of the organ in the scan
                """
        if os.path.exists(input_):
            data = imageio.volread (input_)
        else :
            data=input_.copy()
        #Denosoing the scans if denoising is set to true

        if denoising:
            model_name = organ
            basedir = 'models'
            model = N2V(config=None, name=model_name, basedir=basedir)
            for i in range(0 ,len(data)-1):
                data[i] = model.predict(data[i].astype(np.float32), axes='YX', n_tiles=(2,1))
        if data.meta.Modality=='CT':
            
            #Windowing
            data=self.window_image(data,self.Organ_Dic[organ][1],self.Organ_Dic[organ][0])
            #Normalisation
            data=self.normalize_scan(data)
        if data.meta.Modality=='MR':
            #N4 Bias Correction
            data=self.n4bias_corrector(data)
            #Nyul standardization
            data=self.nyul_standardization(data)
        return data 
    def window_image(self,pixels, window_center, window_width):
        """
        This function performs Windowing of a CT scan, also known as gray-level mapping
        The windowing is performed directly on pixels parameter
        """
        img_min = window_center - window_width // 2
        img_max = window_center + window_width // 2
        pixels[pixels < img_min] = img_min
        pixels[pixels > img_max] = img_max
        return pixels
    def normalize_scan(self,volume):
        """
        This function normalizes a CT scan volume
        """
        min =  np.min(volume)
        max =  np.max(volume)
        volume = (volume - min) / (max - min)
        volume = volume.astype("float32")
        return volume
    def n4bias_corrector(self,data):
        arr = np.asarray(data)
        sitk_image = sitk.GetImageFromArray(arr)
        image = sitk.Cast(sitk_image, sitk.sitkFloat32)
        corrector = sitk.N4BiasFieldCorrectionImageFilter()
        return imageio.core.util.Image(sitk.GetArrayFromImage(corrector.Execute(image)))
    def nyul_standardization(self,data):
        new_nyul_normalizer = NyulNormalize()
        new_nyul_normalizer.load_standard_histogram("standard_histogram.npy")
        arr = np.asarray(data)
        data_corr = [new_nyul_normalizer(image) for image in arr]
        data_corr = imageio.core.util.Image(np.array(data_corr))
        return data_corr


# In[ ]:




