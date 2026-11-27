"""Redraw the engineering EPUB's bookshelf cover using the project's photo and type."""
from PIL import Image, ImageDraw, ImageFont

from build_engineering import BOOK_EDITION, BOOK_NAME, ENGINEERING, ROOT


def main() -> None:
    fonts = ROOT / "analog/analog-book/fonts"
    serif = fonts / "NotoSerifSC-Bold.woff2"
    sans = fonts / "NotoSansSC-Regular.woff2"
    cover = Image.new("RGB", (1080, 1500), "#fcfbf6")
    draw = ImageDraw.Draw(cover)
    green, cream = "#193c32", "#fcfbf6"
    draw.rectangle((0, 0, 1080, 610), fill=green)
    draw.line((74, 88, 1006, 88), fill="#93ad98", width=2)
    draw.text((74, 114), BOOK_EDITION, font=ImageFont.truetype(sans, 36), fill=cream)
    acronym, title = BOOK_NAME.split(" ", 1)
    draw.text((68, 206), acronym, font=ImageFont.truetype(serif, 158), fill=cream)
    draw.text((68, 409), title, font=ImageFont.truetype(serif, 107), fill=cream)

    with Image.open(ROOT / "docs/circuits/assets/photos/libresolar-bms-c1.jpg") as photo:
        photo.thumbnail((960, 580), Image.Resampling.LANCZOS)
        cover.paste(photo, ((cover.width - photo.width) // 2, 685))
    draw.line((74, 1285, 1006, 1285), fill="#93ad98", width=2)
    draw.text((74, 1310), "Libre Solar BMS C1", font=ImageFont.truetype(serif, 42), fill=green)
    draw.text((74, 1380), "Libre Solar  ·  CC BY-SA 4.0", font=ImageFont.truetype(sans, 30), fill=green)
    cover.save(ENGINEERING / "cover.jpg", quality=91, optimize=True, subsampling=0)


if __name__ == "__main__":
    main()
