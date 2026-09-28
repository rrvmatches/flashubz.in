import math
import wave
from pathlib import Path

from PIL import Image, ImageDraw


OUT_DIR = Path("/app/tests/fixtures")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def make_tone(path: Path, hz: float, seconds: float, rate: int = 44100) -> None:
    amplitude = 18000
    total_frames = int(rate * seconds)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        frames = bytearray()
        for i in range(total_frames):
            value = int(amplitude * math.sin(2 * math.pi * hz * (i / rate)))
            frames.extend(value.to_bytes(2, byteorder="little", signed=True))
        wav.writeframes(bytes(frames))


def make_cover(path: Path) -> None:
    img = Image.new("RGB", (1024, 1024), "#070708")
    draw = ImageDraw.Draw(img)
    draw.ellipse((170, 170, 854, 854), outline="#e22a47", width=20)
    draw.ellipse((250, 250, 774, 774), fill="#22070d", outline="#d0d0d5", width=8)
    draw.polygon([(460, 410), (460, 620), (640, 515)], fill="#f0f0f2")
    draw.text((50, 940), "TEST_ONLY_FLASHUBZ", fill="#f12a43")
    img.save(path, format="PNG", optimize=True)


def main() -> None:
    make_tone(OUT_DIR / "TEST_ONLY_tone_1.wav", hz=220, seconds=1.7)
    make_tone(OUT_DIR / "TEST_ONLY_tone_2.wav", hz=330, seconds=1.5)
    make_tone(OUT_DIR / "TEST_ONLY_tone_3.wav", hz=440, seconds=2.0)
    make_cover(OUT_DIR / "TEST_ONLY_cover.png")
    print(f"Created fixtures in {OUT_DIR}")


if __name__ == "__main__":
    main()
