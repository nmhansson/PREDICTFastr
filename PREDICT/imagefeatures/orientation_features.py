#!/usr/bin/env python

# Copyright 2011-2017 Biomedical Imaging Group Rotterdam, Departments of
# Medical Informatics and Radiology, Erasmus MC, Rotterdam, The Netherlands
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import numpy as np
import PREDICT.helpers.orientation_functions as of
import SimpleITK as sitk
import scipy.spatial as sp
from skimage import morphology

_FLOAT_EPS_4 = np.finfo(float).eps * 4.0


def get_orientation_features(mask):
    if type(mask) == sitk.SimpleITK.Image:
        mask = sitk.GetArrayFromImage(mask)

    # Get nonzero point indices if convex hull for memory reduction
    data = np.transpose(np.nonzero(mask))
    try:
        points = sp.ConvexHull(data).points

        success = False
        while not success:
            try:
                center, radii, evecs, v = of.ellipsoid_fit(points)
                success = True
            except np.linalg.linalg.LinAlgError:
                print("Encountered singular matrix, segmentation too small, dilating.")
                elem = morphology.ball(2)
                mask = morphology.binary_dilation(mask, elem)
                data = np.transpose(np.nonzero(mask))
                points = sp.ConvexHull(data).points
                points = of.data_regularize(points, divs=8)

        # Convert evecs to angles
        X = evecs[:, 0]
        Y = evecs[:, 1]
        Z = evecs[:, 2]

        alpha = np.arctan2(Z[0], Z[1])
        beta = np.arccos(Z[2])
        gamma = np.arctan2(X[2], Y[2])

    except sp.qhull.QhullError:
        # TODO: 2D ellipse fit
        alpha = 0
        beta = 0
        gamma = 0

    orientation_labels = ['of_theta_x', 'of_theta_y', 'of_theta_z']
    orientation_features = [alpha, beta, gamma]

    return orientation_features, orientation_labels
