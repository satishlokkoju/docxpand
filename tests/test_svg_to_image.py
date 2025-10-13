import os
import tempfile
from pathlib import Path
import asyncio
import pytest
from docxpand.svg_to_image import PlaywrightSVGRenderer


@pytest.fixture
def renderer():
    renderer_instance = PlaywrightSVGRenderer()
    asyncio.run(renderer_instance.__aenter__())
    yield renderer_instance
    asyncio.run(renderer_instance.__aexit__(None, None, None))


@pytest.mark.asyncio
async def test_render_svg_to_image(renderer: PlaywrightSVGRenderer):
    svg_content = b'<svg height="100" width="100"><circle cx="50" cy="50" r="40" stroke="black" stroke-width="3" fill="red" /></svg>'
    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as temp_svg:
        temp_svg.write(svg_content)
        temp_svg_path = temp_svg.name

    image = await renderer._render_image_from_content(filecontent=svg_content, width=100)

    assert image is not None
    assert image.width > 0
    assert image.height > 0

    os.remove(temp_svg_path)


@pytest.mark.asyncio
async def test_get_coordinates_for_elements(renderer: PlaywrightSVGRenderer):
    svg_content = b"""
    <svg width="200" height="200">
        <rect id="BG" x="0" y="0" width="200" height="200" fill="lightblue" />
        <rect id="rect1" x="10" y="10" width="50" height="50" fill="red" />
        <text id="text1" x="70" y="70">Hello</text>
    </svg>
    """
    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as temp_svg:
        temp_svg.write(svg_content)
        temp_svg_path = temp_svg.name

    element_ids = ["rect1", "text1"]
    coordinates = await renderer._get_coordinates_for_elements(filecontent=svg_content, element_ids=element_ids)

    assert "rect1" in coordinates
    assert "text1" in coordinates
    assert coordinates["rect1"] is not None
    assert coordinates["text1"] is not None

    os.remove(temp_svg_path)
