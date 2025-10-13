import os
import tempfile
import unittest.mock

import numpy as np
import pytest
from docxpand.image import ColorSpace, Image
from docxpand.providers.photo import IDPhoto
from docxpand.scene_insertion import detect_faces


def test_detect_faces():
    # Create a dummy image with a face
    image = Image(np.zeros((200, 200, 3), dtype=np.uint8), ColorSpace.BGR)

    # Mock the DeepFace.extract_faces function
    with unittest.mock.patch("deepface.DeepFace.extract_faces") as mock_extract_faces:
        mock_extract_faces.return_value = [
            {
                "facial_area": {"x": 10, "y": 10, "w": 50, "h": 50},
                "confidence": 0.99,
            }
        ]

        faces = detect_faces(image)

        assert len(faces) == 1
        assert faces[0].left == 0
        assert faces[0].top == 0
        assert faces[0].width == 70.0
        assert faces[0].height == 70.0


def test_id_photo_from_image():
    # Create a dummy image
    image = Image(np.zeros((200, 200, 3), dtype=np.uint8), ColorSpace.BGR)

    # Mock the DeepFace.analyze function
    with unittest.mock.patch("deepface.DeepFace.analyze") as mock_analyze:
        mock_analyze.return_value = {
            "region": {"x": 10, "y": 10, "w": 50, "h": 50},
            "gender": "Man",
            "age": 30,
            "race": "white",
        }

        id_photo, _ = IDPhoto.from_image(image)

        assert id_photo.gender == "male"
        assert id_photo.age == 30
        assert id_photo.ethnicity == "white"
