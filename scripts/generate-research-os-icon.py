from pathlib import Path
import sys

from PIL import Image, ImageDraw


def build_icon(output: Path) -> None:
    size = 256
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Research OS mark: rounded dark tile with a connected research-node motif.
    draw.rounded_rectangle((8, 8, 248, 248), radius=52, fill=(20, 28, 44, 255))
    cyan = (53, 205, 230, 255)
    white = (245, 248, 252, 255)

    center = (128, 128)
    nodes = [(128, 66), (190, 128), (128, 190), (66, 128)]
    for node in nodes:
        draw.line((center[0], center[1], node[0], node[1]), fill=cyan, width=14)
        x, y = node
        draw.ellipse((x - 22, y - 22, x + 22, y + 22), fill=cyan)
        draw.ellipse((x - 10, y - 10, x + 10, y + 10), fill=white)

    draw.ellipse((92, 92, 164, 164), fill=white)
    draw.ellipse((108, 108, 148, 148), fill=(20, 28, 44, 255))

    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(
        output,
        format="ICO",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: generate-research-os-icon.py <output.ico>")
    build_icon(Path(sys.argv[1]))
