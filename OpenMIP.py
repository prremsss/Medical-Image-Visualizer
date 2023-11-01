#!/usr/bin/env python
# coding: utf-8

# In[1]:


import imageio
import numpy as np
import pydicom
import subprocess

import os

from skimage.filters import threshold_otsu
import random
from n2v.models import N2VConfig, N2V
import warnings
from intensity_normalization.normalize.nyul import NyulNormalize
import SimpleITK as sitk
import dicom2nifti
import tempfile
from scipy.ndimage import zoom
import n2v
import nibabel as nib
import numpy.ma as ma
import os


# In[56]:


class OpenMip:
    Organ_Dic = {'Brain': [80, 40], 'head subdural': [215, 75], 'head stroke1': [8, 32], 'head stroke2': [40, 40],
                 'head temporal bones': [2800, 600], 'head soft tissues': [375, 40],
                 'Lungs': [1500, -600], 'chest mediastinum': [350, 50], 'abdomen soft tissues': [400, 50],
                 'liver': [150, 30], 'spinal soft tissues': [250, 50], 'spinal bone': [1800, 400], 'Bone': [2000, 300],
                 'None': [4000, 0]}

    def full_prep(self, input_folder, output_folder, synthseg_path, scan_type, organ, denoising=False, windowing=True,
                  segmentation=True, bias_correction=True, standardization=True, skull_removal=True, num_slices=0,
                  auto_crop=True):
        """
        This function performs full preprocessing of a CT and MRI scan.
        organ:the name of the organ in the scan
                """

        data = imageio.volread(input_folder)
        is_nifti = self.is_nifti_file(input_folder)
        if is_nifti:
            file_type = "Niftii"
        else:
            file_type = "Dicom"

        # Denosoing the scans if denoising is set to true

        if denoising:
            model_name = organ
            basedir = 'models'
            model = N2V(config=None, name=model_name, basedir=basedir)
            for i in range(0, len(data) - 1):
                data[i] = model.predict(data[i].astype(np.float32), axes='YX', n_tiles=(2, 1))
        if scan_type == 'CT':
            if windowing:
                # Windowing
                data = self.window_image(data, self.Organ_Dic[organ][1], self.Organ_Dic[organ][0])

            if segmentation:
                # segmentation
                segmentation = self.organ_segmentation(data, organ, input_folder, output_folder, synthseg_path)

                if num_slices == 0:
                    # remove only slices that doesn't contain any part of the organ
                    data, selectedsegmentation = self.clean_scan(data, segmentation)

                elif num_slices > 0:
                    # keep only num_slices provided
                    data, selectedsegmentation = self.slice_selection(data, segmentation, num_slices)

                if auto_crop:
                    # cropping the slices so that only the organ is visible
                    data, segmantation = self.cropping(data, selectedsegmentation)

        if scan_type == 'MRI':
            if file_type == "Dicom":
                print(file_type)
                temp_dir = tempfile.mkdtemp()
                dicom2nifti.convert_directory(input_folder, temp_dir, compression=False)
                temp_files = os.listdir(temp_dir)
                print(f"Files in temporary directory: {temp_files}")
                temp_output_file = os.path.join(temp_dir, 'uploads/niftii.nii')
                input_folder = os.path.join(temp_dir, temp_files[0])
                data = imageio.volread(input_folder)
                print(data.shape)

            if bias_correction:
                # Bias Correction
                data = self.n4bias_corrector(data)

            if standardization:
                # Nyul standardization
                data = self.nyul_standardization(data)

            if segmentation:
                # segmentation
                segmentation = self.organ_segmentation(data, organ, input_folder, output_folder, synthseg_path)
                if skull_removal:
                    data = self.skull_removing(data, segmentation)

                if num_slices == 0:
                    # remove only slices that doesn't contain any part of the organ
                    data, selectedsegmentation = self.clean_scan(data, segmentation)

                elif num_slices > 0:
                    # keep only num_slices provided
                    data, selectedsegmentation = self.slice_selection(data, segmentation, num_slices)

                if auto_crop:
                    # cropping the slices so that only the organ is visible
                    data, segmantation = self.cropping(data, selectedsegmentation)

        # Normalisation
        data = self.normalize_scan(data)
        return data, segmentation

    def window_image(self, pixels, window_center, window_width):
        """
        This function performs Windowing of a CT scan, also known as gray-level mapping
        The windowing is performed directly on pixels parameter
        """
        img_min = window_center - window_width // 2
        img_max = window_center + window_width // 2
        pixels[pixels < img_min] = img_min
        pixels[pixels > img_max] = img_max
        return pixels

    def normalize_scan(self, volume):
        """
        This function normalizes a CT scan volume
        """
        min = np.min(volume)
        max = np.max(volume)
        volume = (volume - min) / (max - min)
        volume = volume.astype("float32")
        return volume

    def n4bias_corrector(self, data):
        arr = np.asarray(data)
        sitk_image = sitk.GetImageFromArray(arr)
        image = sitk.Cast(sitk_image, sitk.sitkFloat32)
        corrector = sitk.N4BiasFieldCorrectionImageFilter()
        return imageio.core.util.Image(sitk.GetArrayFromImage(corrector.Execute(image)))

    def nyul_standardization(self, data):
        new_nyul_normalizer = NyulNormalize()
        new_nyul_normalizer.load_standard_histogram("standard_histogram.npy")
        arr = np.asarray(data)
        data_corr = [new_nyul_normalizer(image) for image in arr]
        data_corr = imageio.core.util.Image(np.array(data_corr))
        return data_corr

    def is_nifti_file(self, file_path):
        try:

            nib.load(file_path)
            return True
        except nib.filebasedimages.ImageFileError:
            return False

    def organ_segmentation(self, data, organ, input_folder, output_folder, synthseg_path):
        if organ == "Lungs":
            print("Segmenting Lungs")
            from lungmask import LMInferer

            inferer = LMInferer()
            segmentation = inferer.apply(data)
        elif organ == "Brain":
            print("started segmentation")
            print(synthseg_path)
            command = f'python "{synthseg_path}" --i "{input_folder}" --o "{output_folder}" --cpu --threads 11 --fast'

            # Execute the command
            subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print("segmentation finished")
            file_name = os.path.basename(input_folder)
            segmentation_name = file_name.split('.')[0] + '_synthseg.' + file_name.split('.')[1]
            segmentation_path = os.path.join(output_folder, segmentation_name)
            segmentation = imageio.volread(segmentation_path)
            desired_shape = data.shape
            resize_factors = (
                desired_shape[0] / segmentation.shape[0],
                desired_shape[1] / segmentation.shape[1],
                desired_shape[2] / segmentation.shape[2]
            )

            segmentation = zoom(segmentation, resize_factors, order=1)
        return segmentation

    def cropping(self, data, segmentation):
        print("Cropping")
        print(segmentation.shape)
        print(data.shape)

        masked_image = data.copy()
        masked_image[np.where(segmentation == 0)] = 0
        _, rows, cols = np.where(segmentation != 0)
        min_row, max_row = np.min(rows), np.max(rows)
        min_col, max_col = np.min(cols), np.max(cols)
        data = data[:, min_row:max_row + 1, min_col:max_col + 1]
        segmentation = segmentation[:, min_row:max_row + 1, min_col:max_col + 1]
        return data, segmentation

    def clean_scan(self, data, segmentation):
        masked_image = data.copy()
        masked_image[np.where(segmentation == 0)] = 0
        print("clean scan")
        slices, _, _ = np.where(segmentation != 0)
        min_slice, max_slice = np.min(slices), np.max(slices)
        data = data[min_slice:max_slice + 1]
        segmentation = segmentation[min_slice:max_slice + 1]
        return data, segmentation

    def slice_selection(self, data, segmentation, num_slices):
        print("Slice selection")
        masked_image = data.copy()
        masked_image[np.where(segmentation == 0)] = 0
        zero_percentages = np.mean(masked_image == 0, axis=(1, 2))
        threshold = np.sort(zero_percentages)[num_slices - 1]
        high_zero_indexes = np.where(zero_percentages > threshold)
        data = np.delete(data, high_zero_indexes, axis=0)
        segmentation = np.delete(segmentation, high_zero_indexes, axis=0)
        return data, segmentation

    def skull_removing(self, data, segmentation):
        masked_image_brain = data.copy()
        masked_image_brain[np.where(segmentation == 0)] = 0
        return masked_image_brain


