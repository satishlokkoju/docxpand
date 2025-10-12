import os
import tempfile
import unittest.mock

import numpy as np
from docxpand.generator import Generator
from docxpand.image import Image, ColorSpace
from docxpand.svg_to_image import SVGRenderer


class MockSVGRenderer(SVGRenderer):
    def render(self, svg_filename: str) -> Image:
        # Create an empty PNG file to simulate rendering
        png_filename = svg_filename.replace(".svg", ".png")
        with open(png_filename, "w") as f:
            pass
        return Image(np.zeros((1, 1, 3), dtype=np.uint8), ColorSpace.RGB)


def test_generate_images():
    with tempfile.TemporaryDirectory() as temp_dir:
        renderer = MockSVGRenderer()
        generator = Generator("id_card_td1_a", renderer, "")

        with unittest.mock.patch(
            "docxpand.generator.Generator.generate_photo",
            return_value=Image(
                np.zeros((100, 100, 3), dtype=np.uint8), ColorSpace.RGB
            ),
        ):
            entries = generator.generate_images(temp_dir)

        assert len(entries) == 2
        for entry in entries:
            assert os.path.exists(os.path.join(temp_dir, entry["filename"]))
