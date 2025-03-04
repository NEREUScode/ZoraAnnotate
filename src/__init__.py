"""
ZoraVision
==========
is an advanced image annotation tool for segmentation and object detection, built as a standalone app.
Based on digitalsreeni-image-annotator, it offers enhanced usability, new features, and a refined UI.
Supporting formats like COCO JSON, YOLO v8, and Pascal VOC, it provides manual and semi-automated annotation with the Segment Anything Model (SAM-2). 
ZoraVision also handles multi-dimensional images (TIFF stacks, CZI files) and offers a user-friendly experience with dark mode and adjustable fonts. 
For full details, refer to the license and documentation.
"""
__version__ = "0.1.0"
__author__ = "Ben Yamna Mohammed"

from .annotator_window import ImageAnnotator
from .image_label import ImageLabel
from .utils import calculate_area, calculate_bbox
from .sam_utils import SAMUtils  

__all__ = ['ImageAnnotator', 'ImageLabel', 'calculate_area', 'calculate_bbox', 'SAMUtils'] 