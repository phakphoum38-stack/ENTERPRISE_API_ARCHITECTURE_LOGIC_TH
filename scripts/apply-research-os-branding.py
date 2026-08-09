from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image


ANDROID = {
    "mipmap-mdpi": 48,
    "mipmap-hdpi": 72,
    "mipmap-xhdpi": 96,
    "mipmap-xxhdpi": 144,
    "mipmap-xxxhdpi": 192,
}

IOS = {
    "Icon-App-20x20@1x.png": 20,
    "Icon-App-20x20@2x.png": 40,
    "Icon-App-20x20@3x.png": 60,
    "Icon-App-29x29@1x.png": 29,
    "Icon-App-29x29@2x.png": 58,
    "Icon-App-29x29@3x.png": 87,
    "Icon-App-40x40@1x.png": 40,
    "Icon-App-40x40@2x.png": 80,
    "Icon-App-40x40@3x.png": 120,
    "Icon-App-60x60@2x.png": 120,
    "Icon-App-60x60@3x.png": 180,
    "Icon-App-76x76@1x.png": 76,
    "Icon-App-76x76@2x.png": 152,
    "Icon-App-83.5x83.5@2x.png": 167,
    "Icon-App-1024x1024@1x.png": 1024,
}

MACOS = {
    "app_icon_16.png": 16,
    "app_icon_32.png": 32,
    "app_icon_64.png": 64,
    "app_icon_128.png": 128,
    "app_icon_256.png": 256,
    "app_icon_512.png": 512,
    "app_icon_1024.png": 1024,
}


def save_png(image: Image.Image, path: Path, size: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.resize((size, size), Image.Resampling.LANCZOS).save(path, "PNG", optimize=True)


def save_ico(image: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(
        path,
        format="ICO",
        sizes=[
            (16, 16),
            (20, 20),
            (24, 24),
            (32, 32),
            (40, 40),
            (48, 48),
            (64, 64),
            (128, 128),
            (256, 256),
        ],
    )


def apply_shared(image: Image.Image, root: Path) -> None:
    branding = root / "assets" / "branding"
    save_png(image, branding / "research_os_512.png", 512)
    save_png(image, branding / "research_os_256.png", 256)
    save_ico(image, branding / "research_os.ico")
    print(f"Shared branding assets: {branding}")


def apply_windows(image: Image.Image, root: Path) -> None:
    target = root / "windows" / "runner" / "resources" / "app_icon.ico"
    save_ico(image, target)
    print(f"Windows icon: {target}")


def apply_android(image: Image.Image, root: Path) -> None:
    res = root / "android" / "app" / "src" / "main" / "res"
    for folder, size in ANDROID.items():
        target = res / folder / "ic_launcher.png"
        save_png(image, target, size)
        print(f"Android icon: {target}")


def apply_ios(image: Image.Image, root: Path) -> None:
    iconset = root / "ios" / "Runner" / "Assets.xcassets" / "AppIcon.appiconset"
    for name, size in IOS.items():
        target = iconset / name
        save_png(image, target, size)
        print(f"iOS icon: {target}")


def apply_macos(image: Image.Image, root: Path) -> None:
    iconset = root / "macos" / "Runner" / "Assets.xcassets" / "AppIcon.appiconset"
    for name, size in MACOS.items():
        target = iconset / name
        save_png(image, target, size)
        print(f"macOS icon: {target}")


def apply_web(image: Image.Image, root: Path) -> None:
    web = root / "web"
    save_png(image, web / "favicon.png", 48)
    save_png(image, web / "icons" / "Icon-192.png", 192)
    save_png(image, web / "icons" / "Icon-512.png", 512)
    save_png(image, web / "icons" / "Icon-maskable-192.png", 192)
    save_png(image, web / "icons" / "Icon-maskable-512.png", 512)
    print(f"Web/PWA icons: {web / 'icons'}")


def apply_linux(image: Image.Image, root: Path) -> None:
    assets = root / "linux" / "packaging" / "icons"
    for size in (16, 32, 48, 64, 128, 256, 512):
        target = assets / f"research-os-{size}.png"
        save_png(image, target, size)
        print(f"Linux icon: {target}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply the Research OS master icon to Flutter platform shells.")
    parser.add_argument("--app-root", required=True, help="Path to apps/research_os_flutter or generated app staging root")
    parser.add_argument(
        "--platform",
        action="append",
        choices=["windows", "android", "ios", "macos", "web", "linux", "all"],
        help="Platform to update; repeat for multiple platforms. Default: all existing platform directories.",
    )
    parser.add_argument("--master", help="Optional master image path")
    args = parser.parse_args()

    root = Path(args.app_root).resolve()
    master = Path(args.master).resolve() if args.master else root / "assets" / "branding" / "research_os_master.webp"
    if not master.exists():
        raise SystemExit(f"Research OS master icon not found: {master}")

    image = Image.open(master).convert("RGBA")
    apply_shared(image, root)

    requested = set(args.platform or ["all"])
    platforms = ["windows", "android", "ios", "macos", "web", "linux"] if "all" in requested else sorted(requested)
    handlers = {
        "windows": apply_windows,
        "android": apply_android,
        "ios": apply_ios,
        "macos": apply_macos,
        "web": apply_web,
        "linux": apply_linux,
    }

    applied = ["shared"]
    for platform in platforms:
        platform_dir = root / platform
        if not platform_dir.exists():
            print(f"Prepared shared assets; skip {platform} shell because it does not exist yet: {platform_dir}")
            continue
        handlers[platform](image, root)
        applied.append(platform)

    print("Research OS branding applied to: " + ", ".join(applied))


if __name__ == "__main__":
    main()
