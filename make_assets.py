# -*- coding: utf-8 -*-
"""기본 펫 이미지(assets/pet.png)와 exe 아이콘(assets/pet.ico)을 생성한다. 빌드 전에 한 번 실행."""
import os
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "assets")
os.makedirs(OUT, exist_ok=True)


def draw_pet(size: int) -> Image.Image:
    s = size
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    u = s / 160.0  # 160px 기준 좌표계

    # 몸통 (둥근 젤리)
    body = (20 * u, 30 * u, 140 * u, 150 * u)
    d.ellipse(body, fill=(255, 196, 92, 255), outline=(120, 80, 30, 255), width=max(1, int(3 * u)))
    # 하이라이트
    d.ellipse((40 * u, 45 * u, 70 * u, 70 * u), fill=(255, 235, 180, 160))
    # 눈
    for cx in (60 * u, 100 * u):
        d.ellipse((cx - 9 * u, 80 * u, cx + 9 * u, 98 * u), fill=(40, 30, 30, 255))
        d.ellipse((cx - 4 * u, 83 * u, cx + 1 * u, 88 * u), fill=(255, 255, 255, 255))
    # 볼터치
    d.ellipse((38 * u, 100 * u, 56 * u, 110 * u), fill=(255, 140, 140, 150))
    d.ellipse((104 * u, 100 * u, 122 * u, 110 * u), fill=(255, 140, 140, 150))
    # 입
    d.arc((68 * u, 98 * u, 92 * u, 118 * u), start=10, end=170, fill=(120, 60, 40, 255), width=max(1, int(3 * u)))
    # 머리 위 새싹
    d.line((80 * u, 32 * u, 80 * u, 14 * u), fill=(60, 140, 60, 255), width=max(1, int(4 * u)))
    d.ellipse((66 * u, 2 * u, 82 * u, 16 * u), fill=(90, 190, 90, 255))
    d.ellipse((80 * u, 4 * u, 96 * u, 18 * u), fill=(90, 190, 90, 255))
    return im


if __name__ == "__main__":
    pet = draw_pet(160)
    pet.save(os.path.join(OUT, "pet.png"))
    icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    draw_pet(256).save(os.path.join(OUT, "pet.ico"), sizes=icon_sizes)
    print("generated: assets/pet.png, assets/pet.ico")
