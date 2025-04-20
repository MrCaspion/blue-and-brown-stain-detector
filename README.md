# Biology Image Tool

## Overview
It detects and counts blue nuclei and brown-stained spots in histological samples, useful for quantifying biological markers in research.

## Requirements
* Python 3.6+
* Required packages:
  * numpy
  * scipy
  * scikit-image
  * opencv-python
  * pillow
  * pandas
  * tkinter (included with Python)

## Installation
1. Clone this repository
2. Install the required packages:
pip install -r requirements.txt
3. Run the application:
python main.py

Only used to:
* Detecting blue nuclei and brown staining
* Adjusting detection parameters
* Batch processing multiple images

## Parameter Adjustment
Fine-tune detection with sliders for:
* Blue/brown stain detection sensitivity
* Noise filtering
* Nucleus separation
* Minimum object sizes

## Troubleshooting
* For inaccurate detection: Adjust blue/brown thresholds
* For densely packed nuclei: Decrease minimum distance value
* For small artifacts: Increase minimum size parameters
* For noisy images: Increase noise filtering strength