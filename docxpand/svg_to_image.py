"""Implementation of an SVGToImage rendering using Chrome."""
import asyncio
import json
import os
import subprocess
import tempfile
import typing as tp

from playwright.async_api import async_playwright
from docxpand.geometry import BoundingBox, Point
from docxpand.image import ColorSpace, Image
from docxpand.utils import guess_mimetype

# HTML template to use with Chrome-based renderer.
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<body style="background: transparent; margin: 0">
<img style="background: transparent; margin: 0" id="svg-image" src="{svg_file}" width="{width}px" />
</body>
</html>
"""

SVG_FILENAME = "image.svg"
PNG_FILENAME = "image.png"
HTML_FILENAME = "page.html"

RSVG_CONVERT_EXECUTABLE = "rsvg-convert"


class SVGRenderer:
    """SVG renderer."""

    @staticmethod
    def check_arguments_and_load_content(
        filename: tp.Optional[str] = None,
        filecontent: tp.Optional[bytes] = None,
    ) -> bytes:
        """Check arguments and load content of file if applicable.
        
        Args:
            filename: path to a SVG file to render. Don't use it if you use
                content.
            filecontent: content of SVG file. Don't use it if you use path.

        Raises:
            ValueError: if the arguments are not set correctly, or the content is
                not a valid SVG
            FileNotFoundError: if filename doens't point to a valid file
            
        Returns:
            content of file with path `filename` if applicable, or `filecontent`
        """
        if filename and filecontent:
            raise ValueError(
                "Filename and filecontent cannot be set simultaneously."
            )
        if not filename and not filecontent:
            raise ValueError("Either filename or filecontent must be set.")
        if filename:
            if not os.path.isfile(filename):
                raise FileNotFoundError(
                    f"Filename is not a file, got filename={filename}."
                )
            with open(filename, "rb") as f_in:
                filecontent = f_in.read()
        assert filecontent is not None
        mimetype = guess_mimetype(filecontent=filecontent)
        if not mimetype.startswith("image/svg"):
            raise ValueError(
                "The given file or content does not seem to be valid SVG. "
                f"Expected image/svg+xml mimetype, got {mimetype} instead."
            )
        return filecontent

    def render(
        self,
        filename: tp.Optional[str] = None,
        filecontent: tp.Optional[bytes] = None,
        width: int = 1000,
    ) -> Image:
        """Render a SVG to an Image.

        Args:
            filename: path to a SVG file to render. Don't use it if you use
                content.
            filecontent: content of SVG file. Don't use it if you use path.
            width : width of the image to get. Height will be calculated from
                width by respecting the aspect ratio.

        Returns:
            rendered Image
        """
        filecontent = self.check_arguments_and_load_content(filename, filecontent)
        return self._render_image_from_content(filecontent, width)

    def _render_image_from_content(self, filecontent: bytes, width: int):
        """Perform the rendering.

        Args:
            filecontent: content of SVG file.
            width : width of the image to get. Height will be calculated from
                width by respecting the aspect ratio.

        Raises:
            NotImplementedError: it must be implemented in child class
        """
        raise NotImplementedError("Must be implemented in child class.")
    
    def get_coordinates(
            self,
            filename: tp.Optional[str] = None,
            filecontent: tp.Optional[bytes] = None,
            element_ids: tp.Union[
                str,
                tp.Tuple[str, bool],
                tp.List[tp.Union[str, tp.Tuple[str, bool]]], 
                None
            ] = None,
        ) -> tp.Dict[str, BoundingBox]:
        """Return the coordinates of an element in the viewport.
        
        Args:
            filename: path to a SVG file to render. Don't use it if you use
                content.
            filecontent: content of SVG file. Don't use it if you use path.
            element_ids: IDs of the elements for which the coordinates must be
                found. For each element of the list, if the element is a a tuple,
                then the second argument is a boolean telling if the field is
                multi-line.

        Returns:
            a dictionary containing the coordinates of each element in the
            viewport by element id
        """
        filecontent = self.check_arguments_and_load_content(filename, filecontent)
        if not element_ids:
            return {}

        return self._get_coordinates_for_elements(filecontent, element_ids)


    def _get_coordinates_for_elements(
        self,
        filecontent: bytes,
        element_ids: tp.Union[
            str,
            tp.Tuple[str, bool],
            tp.List[tp.Union[str, tp.Tuple[str, bool]]]
        ],
    ) -> tp.Dict[str, BoundingBox]:
        """Return the coordinates of an element in the viewport.
        
        Args:
            filename: path to a SVG file to render. Don't use it if you use
                content.
            filecontent: content of SVG file. Don't use it if you use path.
            width : width of the image to get. Height will be calculated from
                width by respecting the aspect ratio.
            element_ids: IDs of the elements for which the coordinates must be
                found. For each element of the list, if the element is a a tuple,
                then the second argument is a boolean telling if the field is
                multi-line.

        Returns:
            a dictionary containing the coordinates of each element in the
            viewport by element id
        """
        raise NotImplementedError("Must be implemented in child class.")


class PlaywrightSVGRenderer(SVGRenderer):
    """SVG renderer using headless Chrome and Playwright."""

    def __init__(self) -> None:
        """Init a PlaywrightSVGRenderer converter."""
        super().__init__()
        self.playwright = None
        self.browser = None

    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def _render_image_from_content(self, filecontent: bytes, width: int) -> Image:
        """Perform the rendering.
        Args:
            filecontent: content of SVG file.
            width : width of the image to get.
        """
        with tempfile.TemporaryDirectory() as tmp_dirname:
            svg_file_name = os.path.join(tmp_dirname, SVG_FILENAME)
            with open(svg_file_name, "wb") as svg_file:
                svg_file.write(filecontent)

            template_file_name = os.path.join(tmp_dirname, HTML_FILENAME)
            with open(template_file_name, "w") as template_file:
                template_file.write(
                    HTML_TEMPLATE.format(svg_file=f"file://{os.path.abspath(svg_file_name)}", width=width)
                )

            page = await self.browser.new_page()
            await page.goto(f"file://{os.path.abspath(template_file_name)}")
            element = page.locator("#svg-image")
            screenshot = await element.screenshot(omit_background=True)
            await page.close()

            return Image.read(screenshot, ColorSpace.BGRA)

    async def _get_coordinates_for_elements(
        self,
        filecontent: bytes,
        element_ids: tp.Union[
            str,
            tp.Tuple[str, bool],
            tp.List[tp.Union[str, tp.Tuple[str, bool]]]
        ],
    ) -> tp.Dict[str, BoundingBox]:
        """Return the coordinates of an element relative to the viewport."""
        coordinates = {}

        if not isinstance(element_ids, list):
            element_ids = [element_ids]

        async def get_bbox(element) -> BoundingBox:
            box = await element.bounding_box()
            if box is None:
                return None
            top_left = Point(x=box['x'], y=box['y'])
            bottom_right = Point(
                x=box['x'] + box['width'],
                y=box['y'] + box['height']
            )
            return BoundingBox(top_left, bottom_right)

        def rescale_and_clip(
                bbox: BoundingBox, viewport: BoundingBox
            ) -> BoundingBox:
            return BoundingBox(
                Point(
                    (bbox.left - viewport.left) / viewport.width,
                    (bbox.top - viewport.top) / viewport.height
                ),
                Point(
                    (bbox.right - viewport.left) / viewport.width,
                    (bbox.bottom - viewport.top) / viewport.height
                )
            ).clip(1.0, 1.0, 0, 0)

        with tempfile.TemporaryDirectory() as tmp_dirname:
            svg_file_name = os.path.join(tmp_dirname, SVG_FILENAME)
            with open(svg_file_name, "wb") as svg_file:
                svg_file.write(filecontent)

            page = await self.browser.new_page()
            await page.goto(f"file://{os.path.abspath(svg_file_name)}")

            viewport_element = page.locator("#BG")
            if not await viewport_element.is_visible():
                await page.close()
                return {element_id[0] if isinstance(element_id, tuple) else element_id: None for element_id in element_ids}

            viewport = await get_bbox(viewport_element)
            if viewport is None:
                await page.close()
                return {element_id[0] if isinstance(element_id, tuple) else element_id: None for element_id in element_ids}

            for element_id_and_multiline in element_ids:
                if isinstance(element_id_and_multiline, tuple):
                    element_id, multiline = element_id_and_multiline
                else:
                    element_id = element_id_and_multiline
                    multiline = False

                if multiline:
                    bbox = None
                    line_idx = 1
                    while True:
                        element_line = page.locator(f"#{element_id}_{line_idx}")
                        if not await element_line.is_visible():
                            break
                        bbox_line = await get_bbox(element_line)
                        if bbox_line is None:
                            break
                        bbox_line = rescale_and_clip(bbox_line, viewport)
                        if bbox is None:
                            bbox = bbox_line
                        else:
                            bbox = bbox.union(bbox_line)
                        line_idx += 1
                else:
                    element = page.locator(f"#{element_id}")
                    if await element.is_visible():
                        bbox = await get_bbox(element)
                        if bbox is not None:
                            bbox = rescale_and_clip(bbox, viewport)
                    else:
                        bbox = None

                coordinates[element_id] = bbox

            await page.close()

        return coordinates


class RSVGRenderer(SVGRenderer):
    """SVG renderer using librsvg2.

    Needs installing the package librsvg (e.g. `apt install librsvg2-bin` on
    Ubuntu, `brew install librsvg` on MacOS), and adding path to `rsvg-convert`
    in your `PATH` environment variable if you install it to a custom location.
    """

    def _render_image_from_content(self, filecontent: bytes, width: int) -> Image:
        """Perform the rendering.

        Args:
            filecontent: content of SVG file.
            width : width of the image to get.
        """
        with tempfile.TemporaryDirectory() as tmp_dirname:
            svg_file_name = os.path.join(tmp_dirname, SVG_FILENAME)
            with open(svg_file_name, mode="wb") as svg_file:
                svg_file.write(filecontent)

            png_file_name = os.path.join(tmp_dirname, PNG_FILENAME)
            command = [
                RSVG_CONVERT_EXECUTABLE,
                "-w",
                str(width),
                svg_file_name,
                "-o",
                png_file_name,
            ]
            completed_process = subprocess.run(command)
            if completed_process.returncode:
                raise RuntimeError(
                    f"{RSVG_CONVERT_EXECUTABLE} failed with code "
                    f"{completed_process.returncode} on file {svg_file_name} "
                    f"(command: {command})."
                )

            return Image.read(png_file_name, ColorSpace.BGRA)
