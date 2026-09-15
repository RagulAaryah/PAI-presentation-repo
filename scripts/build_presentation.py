"""Fill the three diagram placeholders in the resit presentation with the
generated images from docs/diagrams/ (run scripts/diagrams/*.py first).

Presentation-assembly script, not application code -- not unit tested,
same category as the other scripts/*.py tools. Reproducible: re-run
after regenerating any diagram and this rebuilds the slide images from
scratch rather than needing manual PowerPoint editing.
"""

from __future__ import annotations

import os

from PIL import Image
from pptx import Presentation
from pptx.util import Emu

PPTX_PATH = os.path.join("presentation", "WM9QF15_Resit_Presentation.pptx")

# slide index (0-based) -> diagram image
SLIDE_IMAGES = {
    2: os.path.join("docs", "diagrams", "er_diagram.png"),
    3: os.path.join("docs", "diagrams", "architecture_diagram.png"),
    5: os.path.join("docs", "diagrams", "benchmark_chart.png"),
}


def _fit_within(box_left, box_top, box_width, box_height, image_path):
    """Return (left, top, width, height) that fits image_path inside the
    given box, preserving aspect ratio and centering it in the box."""
    with Image.open(image_path) as im:
        img_w, img_h = im.size
    img_aspect = img_w / img_h
    box_aspect = box_width / box_height

    if img_aspect > box_aspect:
        new_width = box_width
        new_height = int(box_width / img_aspect)
    else:
        new_height = box_height
        new_width = int(box_height * img_aspect)

    left = box_left + (box_width - new_width) // 2
    top = box_top + (box_height - new_height) // 2
    return left, top, new_width, new_height


def main() -> None:
    prs = Presentation(PPTX_PATH)

    for slide_idx, image_path in SLIDE_IMAGES.items():
        slide = prs.slides[slide_idx]
        placeholder = next(
            shape for shape in slide.shapes
            if shape.has_text_frame and "Insert" in shape.text_frame.text
        )
        left, top, width, height = placeholder.left, placeholder.top, placeholder.width, placeholder.height

        # Remove the placeholder rectangle before adding the picture.
        placeholder._element.getparent().remove(placeholder._element)

        fit_left, fit_top, fit_w, fit_h = _fit_within(left, top, width, height, image_path)
        slide.shapes.add_picture(image_path, Emu(fit_left), Emu(fit_top), Emu(fit_w), Emu(fit_h))
        print(f"Slide {slide_idx + 1}: inserted {image_path}")

    prs.save(PPTX_PATH)
    print(f"Saved {PPTX_PATH}")


if __name__ == "__main__":
    main()
