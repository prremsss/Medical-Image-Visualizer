import json
import random
import shutil
import pydicom
from MedPrep import MED_PREP
from scipy.ndimage import zoom
from OpenMIP import OpenMip
import tempfile
import nibabel as nib
from pydicom.dataset import Dataset, FileDataset

import numpy as np
from flask import Flask, jsonify, render_template, request, send_file
import matplotlib.pyplot as plt
from skimage.transform import resize
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'  # Set the folder where uploaded files will be saved

import imageio



@app.route('/')
def index():
    return render_template('index.html')


def create_upload_folder():
    upload_folder = app.config['UPLOAD_FOLDER']
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    else:
        # Remove existing files from the uploads folder
        files = os.listdir(upload_folder)
        for file in files:
            file_path = os.path.join(upload_folder, file)
            if os.path.isfile(file_path):
                os.remove(file_path)


@app.route('/upload', methods=['POST'])
def upload_files():
    global data
    global  file_path
    global isNiftii
    create_upload_folder()
    if request.method == 'POST':
        if 'dicom_files' not in request.files:
            return 'No file part in the request.'

        files = request.files.getlist('dicom_files')

        for file in files:
            file.save(os.path.join('uploads', file.filename))
        file_path=os.path.join('uploads', file.filename)
        data = imageio.volread(file_path)
        print (data.shape)
        try:
            nib.load(file_path)
            isNiftii=True
        except nib.filebasedimages.ImageFileError:
            isNiftii=False

        if data.shape[1]!=data.shape[2]:
            data = np.transpose(data, (2, 0, 1))

        print(file_path)

    return render_template('viewer.html')


@app.route('/pixeldata')
def get_pixel_data():
    min_vals = np.min(data, axis=(1, 2))
    max_vals = np.max(data, axis=(1, 2))

    range_vals = max_vals - min_vals
    rescaled_data = ((data - min_vals[:, np.newaxis, np.newaxis]) / range_vals[:, np.newaxis, np.newaxis]) * 255
    stretched_data = np.clip(rescaled_data, 0, 255).astype(np.uint8)

    width, height = data[0].shape[:2]
    response_data = json.dumps(stretched_data.tolist())

    return jsonify({
        'pixels': response_data,
        'width': width,
        'height': height
    })


@app.route('/preprocess', methods=['POST'])
def preprocess():
    global data_prep

    values = request.json
    selected_value = values.get('selectedValue')
    organ=values.get('organ')
    denoising=values.get('denoising')
    numSlices=values.get('desiredNumSlices')
    segmentation = values.get('segmentation')
    standardization = values.get('standardization')

    biasCorrection =values.get('biasCorrection')

    skullRemoval = values.get('skullRemoval')

    crop = values.get('crop')
    print(selected_value)
    print(organ)
    print(denoising)
    print(numSlices)
    print(segmentation)
    print(standardization)
    print(biasCorrection)
    print(skullRemoval)
    print(crop)
    if numSlices=="":
        numSlices=0
    print(numSlices)
    temp_dir = tempfile.mkdtemp()
    synthseg_path = 'C:/Users/LEGION/Desktop/MASTER/PFE/segmentation/SynthSeg/scripts/commands/SynthSeg_predict.py'
    medprep = OpenMip()
    print(file_path)
    data_prep,_ = medprep.full_prep("uploads", temp_dir,synthseg_path,scan_type=selected_value,organ=organ,denoising=denoising,segmentation=segmentation,num_slices=int(numSlices),bias_correction=biasCorrection,standardization=standardization,skull_removal=skullRemoval,auto_crop=crop)
    data_prep.shape

    min_vals = np.min(data_prep, axis=(1, 2))
    max_vals = np.max(data_prep, axis=(1, 2))
    range_vals = max_vals - min_vals
    rescaled_data = ((data_prep - min_vals[:, np.newaxis, np.newaxis]) / range_vals[:, np.newaxis, np.newaxis]) * 255
    stretched_data = np.clip(rescaled_data, 0, 255).astype(np.uint8)

    width, height = data_prep[0].shape[:2]
    response_data = json.dumps(stretched_data.tolist())
    print('preprocessing done')
    return jsonify({
        'pixels': response_data,
        'width': width,
        'height': height
    })
@app.route('/download_dicom', methods=['POST'])
def download_dicom():
    nifti_image = nib.Nifti1Image(data_prep, affine=None)
    nifti_filename = "Preprocessedata.nii"
    nib.save(nifti_image, nifti_filename)
    return send_file(nifti_filename, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)