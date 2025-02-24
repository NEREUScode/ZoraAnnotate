"""

ImageLabel module for the Image Annotator application.

This module contains the ImageLabel class, which is responsible for
displaying the image and handling annotation interactions.

"""

from PyQt5.QtWidgets import QLabel, QApplication, QMessageBox
from PyQt5.QtGui import (QPainter, QPen, QColor, QFont, QPolygonF, QBrush, QPolygon,
                         QPixmap, QImage, QWheelEvent, QMouseEvent, QKeyEvent)
from PyQt5.QtCore import Qt, QPoint, QPointF, QRectF, QSize
from PIL import Image
import os
import warnings
import cv2
import numpy as np

warnings.filterwarnings("ignore", category=UserWarning) # ignore any warning 

class ImageLabel(QLabel):
    """
    A custom Qlabel for displaying images and handling annotations
    """

    def __init__(self, parent= None): # parent to None for flexible parent
        super.__init__(parent)
        self.annotations = {}
        self.current_annotation = []
        self.temp_point = None # for polygone
        self.current_tool = None # either polygine or rectangle
        self.zoom_factor = 1.0
        self.class_colors = {}
        self.class_visibilty = {}
        self.start_point = None
        self.end_point = None
        self.highlighted_annotations = []
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus) # capable of receiving both mouse and keyboard events.
        self.original_pixmap = None
        self.scaled_pixmap = None
        self.pan_start_pos = None
        self.main_window = None
        self.offset_x = 0
        self.offset_y = 0
        self.drawing_polygon = False
        self.editing_polygon = None
        self.editing_point_index = None
        self.hover_point_index = None
        self.fill_opacity = 0.3
        self.drawing_rectangle = False 
        self.current_rectangle = None
        self.bit_depth = None
        self.image_path = None
        self.dark_mode = False

        self.paint_mask = None
        self.eraser_mask = None 
        self.temp_paint_mask = None
        self.is_painting = False
        self.temp_eraser_mask = None
        self.is_erasing = None
        self.cursor_pos = None

        # sam 

    def set_main_window(self, main_window):
        self.main_window = main_window

    # TODO : check the system for the mode
    def set_dark_mode(self, is_dark ):
        self.dark_mode = is_dark
        self.update()

    def setPixmap(self, pixmap): # this function take the image turn it to pixels and scale it if needed to fit the gui
        """set the pixmap and update the scaled version """
        if isinstance(pixmap, QImage):
            pixmap = QPixmap.fromImage(pixmap)
        self.original_pixmap = pixmap
        self.update_scaled_pixmap()

    def detect_bit_depth(self): # get the bit depth of the image and update the gui with this info ()
        """Detect and store the actual image bit depth using PIL"""
        if self.image_path and os.path.exists(self.image_path):
            with Image.open(self.image_path) as img :
                if img.mode == '1': # Black and white images (binary)
                    self.bit_depth = 1 
                elif img.mode == 'L' : # Grayscale images.
                    self.bit_depth = 8 
                elif img.mode == 'I;16': # High-quality grayscale images (16 bits per pixel)
                    self.bit_depth = 16 
                elif img.mode in ['RGB', 'HSV']: # Standard color images (8 bits per channel × 3 channels = 24 bits)
                    self.bit_depth = 24
                elif img.mode in ['RGBA', 'CMYK']: #  Images with transparency or CMYK color mode (8 bits per channel × 4 channels = 32 bits).
                    self.bit_depth = 32
                else :
                    self.bit_depth = img.bits 
                    #f the mode doesn't match the above, it attempts to use img.bits to determine the bit depth.
                
                if self.main_window:
                    self.main_window.update_image_info()

    def update_scaled_pixmap(self):
        if self.original_pixmap and not self.original_pixmap.isNull():
            scaled_size = self.original_pixmap.size() * self.zoom_factor
            self.scaled_pixmap = self.original_pixmap.scaled(
                scaled_size.width(),
                scaled_size.height(),
                Qt.KeepAspectRatio, # ensures the image does not get stretched or squished when resized
                Qt.SmoothTransformation # ensures smooth transformation
            )
            super().setPixmap(self.scaled_pixmap)
            self.setMinimumSize(self.scaled_pixmap.size())
            self.update_offset()
        else :
            self.scaled_pixmap = None
            super().setPixmap(QPixmap())
            self.setMinimumSize(QSize(0, 0))
    
    def update_offset(self):
        """update the offset for centred image display"""
        if self.scaled_pixmap:
            self.offset_x = int((self.width() - self.scaled_pixmap.width())/2)
            self.offset_y = int((self.height() - self.scaled_pixmap.height())/2)

    def reset_annotation_state(self):
        """reset the annotation state """
        self.temp_point = None
        self.start_point = None
        self.end_point = None

    def clear_current_annotation(self):
        """clear the currznt annotation"""
        self.current_annotation = []
    
    def resizeEvent(self, event):
        """handle resize events"""
        super().resizeEvent(event)
        self.update_offset()

    def start_painting(self, pos):
        if self.temp_paint_mask is None:
            self.temp_paint_mask = np.zeros((self.original_pixmap.height(), self.original_pixmap.width()), dtype = np.uint8)
            #uint8:
                # unsigned (no negative values)
                # integer
                # 8 bits (1 byte) per element
        self.is_painting = True
        self.continue_painting(pos)

    def continue_painting(self, pos):
        if not self.is_painting:
            return
        brush_size = self.main_window.paint_brush_size
        cv2.circle(self.temp_paint_mask, (int(pos[0]), int(pos[1])), brush_size, 255, -1)
    
    def finish_painting(self):
        if  not self.is_painting:
            return
        self.is_painting = False
        
    def commit_paint_annotation(self):
        if self.temp_paint_mask is not None and self.main_window.current_class:
            class_name = self.main_window.current_class
            contours, _ = cv2.findContours(self.temp_paint_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE) # countor in numpy array (x,y)
            for contour in contours : 
                if cv2.contourArea(contour) > 10 : # minimum area threshold
                    segmentation = contour.flatten().tolist() 
                    new_annotation = {
                        "segmentation" : segmentation,
                        "category_id" : self.main_window.class_mapping[class_name],
                        "category_name" : class_name ,
                    }
                    self.annotations.setdefault(class_name, []).append(new_annotation) # multiple annotations for the same class are grouped together
                    self.main_window.add_annotation_to_list(new_annotation)
            self.temp_paint_mask = None
            self.main_window.save_current_annotations()
            self.main_window.update_slice_list_colors()
            self.update()

    def discard_paint_annotation(self):
        self.temp_paint_mask = None
        self.update()

    def start_erasing(self, pos):
        if self.temp_eraser_mask is None:
            self.temp_eraser_mask = np.zeros((self.original_pixmap.height(), self.original_pixmap.width()), dtype=np.uint8)
        self.is_erasing = True
        self.continue_erasing(pos)

    def continue_erasing(self, pos):
        if not self.is_erasing:
            return
        eraser_size = self.main_window.eraser_size
        cv2.circle(self.temp_eraser_mask, (int(pos[0]), int(pos[1])), eraser_size, 255, -1)
        self.update()

    def finish_erasing(self):
        if not self.is_erasing:
            return
        self.is_erasing = False

    def commit_eraser_changes(self):
        if self.temp_eraser_mask is not None :
            eraser_mask = self.temp_eraser_mask.astype(bool)
            current_name = self.main_window.current_slice or self.main_window.image_file_name
            annotations_changed = False

            for class_name, annotations in self.annotations.items():
                updated_annotations = []
                max_number = max([ann.get('number', 0) for ann in annotations]+[0])
                for annotation in annotations:
                    if "segmentation" in annotation :
                        points = np.array(annotation["segmentation"]).reshape(-1,2).astype(int)
                        mask = np.zeros_like(self.temp_eraser_mask)
                        cv2.fillPoly(mask, [points], 255)
                        mask = mask.astype(bool)
                        mask[eraser_mask] = False
                        contours, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_CCOMP , cv2.CHAIN_APPROX_SIMPLE)
                        for i, contour in enumerate(contours) : 
                            if cv2.contourArea(contour)>10: # Minimum area threshold
                                new_segmentation = contour.flatten().tolist()
                                new_annotation = annotation.copy()
                                new_annotation["segmentation"] = new_segmentation
                                if i == 0 :
                                    new_annotation["number"] = annotation.get("number", max_number + 1)
                                else:
                                    max_number += 1
                                    new_annotation["number"] = max_number
                                updated_annotations.append(new_annotation)
                        if len(contours) > 1:
                                annotations_changed = True
                    else :
                        updated_annotations.append(annotation)
                self.annotations[class_name] = updated_annotations
                
            self.temp_eraser_mask = None

            # update the all_annotations dictionary in the main window
            self.main_window.all_annotations[current_name] = self.annotations

            #call update_annotations_list directly
            self.main_window.update_annotation_list()
            self.main_window.save_current_annotations()
            self.main_window.update_slice_list_colors()
            self.update()

    def discard_eraser_changes(self):
        self.temp_eraser_mask = None
        self.update()

    # the painter event
                
