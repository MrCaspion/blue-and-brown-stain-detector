# Configuration parameters for dot counter application
import os
import json

# Default parameters file location
DEFAULT_PARAMS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "default_params.json")

# Display settings
DISPLAY_MAX_WIDTH = 400
DISPLAY_MAX_HEIGHT = 400

# Processing parameters
DISK_SIZE = 1
GAUSSIAN_SIGMA = 1
MIN_DISTANCE = 5
MIN_AREA_H = 2
MIN_AREA_D = 5
MARKER_RADIUS = 2

# The paramter range for the slider
PARAM_RANGES = {
    'h_threshold': {'min': 0, 'max': 1, 'step': 0.01, 'length': 250},
    'd_threshold': {'min': 0, 'max': 1, 'step': 0.01, 'length': 250},
    'disk_size': {'min': 1, 'max': 10, 'step': 1, 'length': 250, 'default': DISK_SIZE},
    'gaussian_sigma': {'min': 0.1, 'max': 5.0, 'step': 0.1, 'length': 250, 'default': GAUSSIAN_SIGMA},
    'min_distance': {'min': 1, 'max': 20, 'step': 1, 'length': 250, 'default': MIN_DISTANCE},
    'min_area_h': {'min': 1, 'max': 20, 'step': 1, 'length': 250, 'default': MIN_AREA_H},
    'min_area_d': {'min': 1, 'max': 50, 'step': 1, 'length': 250, 'default': MIN_AREA_D},
    'marker_radius': {'min': 1, 'max': 10, 'step': 1, 'length': 250, 'default': MARKER_RADIUS}
}

# Higher level param names
PARAM_NAMES = {
    'h_threshold': 'Blue Nuclei Threshold',
    'd_threshold': 'Brown Stain Threshold',
    'disk_size': 'Noise Filter Size',
    'gaussian_sigma': 'Nucleus Separation',
    'min_distance': 'Marker Spacing',
    'min_area_h': 'Min Blue Nucleus Size',
    'min_area_d': 'Min Brown Spot Size',
    'marker_radius': 'Dot Display Size'
}

# Tips on what to change based on what is happening
TROUBLESHOOTING_TIPS = (
    "• Blue nuclei merged together → ↓ Nucleus Separation or ↓ Marker Spacing\n"
    "• Blue nuclei oversplit → ↑ Nucleus Separation or ↑ Marker Spacing\n"
    "• Brown/red speckles (noise) → ↑ Noise Filter Size or ↑ Min Brown Spot Size\n"
    "• Missing small blobs → ↓ Noise Filter Size or ↓ Min Blue/Brown Size"
) 