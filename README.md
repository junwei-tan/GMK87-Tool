# GMK87 Tool

Python tool for configuring the Zuoya GMK87 keyboard — lighting, display images, and animated GIFs — over USB HID.

Inspired by [ikkentim/gmk87-usb-reverse](https://github.com/ikkentim/gmk87-usb-reverse).

---

## Features

- Upload custom images and animated GIFs to the LCD display (240×135, RGB565)
- Switch between clock, image slot 1, and image slot 2
- Configure underglow and backlight effects, colors, speed, brightness
- Sync time and date to the keyboard clock
- Lock/unlock the Windows key
- Works on **macOS (Apple Silicon & Intel)** and Linux

---

## Requirements

- Python 3.10+
- [python-hidapi](https://github.com/trezor/cython-hidapi)
- [Pillow](https://pillow.readthedocs.io/) (for image/GIF upload)

**macOS:**
```bash
brew install hidapi
pip install hid pillow
```

**Linux (Arch):**
```bash
pacman -S python-hidapi
pip install pillow
```

**Linux (Debian/Ubuntu):**
```bash
apt install libhidapi-hidraw0
pip install hid pillow
```

---

## Setup

```bash
git clone https://github.com/junwei-tan/GMK87-Tool.git
cd GMK87-Tool
```

Verify your keyboard is detected:
```bash
python HIDList.py
```

You should see entries with `vendor_id: 12815`, `product_id: 20565`.

---

## Uploading Images and GIFs

Use `upload_image.py` to upload a static image or animated GIF to one of two display slots. The image is automatically resized to 240×135.

```bash
# Upload a static image to slot 1
python upload_image.py photo.jpg

# Upload an animated GIF to slot 1 at 10fps
python upload_image.py animation.gif --slot 1 --fps 10

# Upload to slot 2
python upload_image.py other.png --slot 2
```

The script automatically updates `config.json` and activates the image on the display.

**Note:** Uploading to either slot clears both slots, as the keyboard has a single shared image buffer. If you use both slots, upload them together by running the script twice in sequence before switching away.

To switch back to the clock:
```bash
# Edit config.json: set "show_image": 0
python GMK87Tool.py -c config.json
```

---

## Configuring Lighting

Edit `config.json` and run:

```bash
python GMK87Tool.py -c config.json
```

On Linux you may need `sudo` (or reassign device ownership — see below).

### config.json reference

```json
{
    "keyboard": {
        "vendor_id": "12815",
        "product_id": "20565",
        "usage_config": 146,
        "usage_check": 97
    },
    "config": {
        "underglow_effect": 1,
        "underglow_brightness": 2,
        "underglow_speed": 2,
        "underglow_orientation": 0,
        "underglow_rainbow": 1,
        "underglow_hue": {
            "red": 255,
            "green": 255,
            "blue": 255
        },
        "winlock": 0,
        "led_mode": 0,
        "led_saturation": 0,
        "led_rainbow": 0,
        "led_color": 0,
        "show_image": 0,
        "frame_interval_ms": 100,
        "image1": { "frames": 0 },
        "image2": { "frames": 0 }
    },
    "debug": false
}
```

| Field | Values | Description |
|---|---|---|
| `underglow_effect` | 0–18 | 0=off, 1=wave, 5=breathing, 6=solid, 11=rainbow cycle, [full list in GMK87Tool.py] |
| `underglow_brightness` | 0–9 | 0=off, 9=max |
| `underglow_speed` | 0–9 | 0=fast, 9=slow |
| `underglow_orientation` | 0–1 | 0=left→right, 1=right→left |
| `underglow_rainbow` | 0–1 | 0=single hue, 1=multi-color |
| `underglow_hue` | 0–255 per channel | RGB color when rainbow=0 |
| `winlock` | 0–1 | 1=lock Windows key |
| `led_mode` | 0–4 | Big LED (display surround) mode |
| `led_saturation` | 0–9 | Big LED brightness |
| `led_rainbow` | 0–1 | 0=single hue, 1=rainbow |
| `led_color` | 0–8 | 0=red, 1=orange, 2=yellow, 3=green, 4=teal, 5=blue, 6=purple, 7=white, 8=off |
| `show_image` | 0–2 | 0=clock, 1=image slot 1, 2=image slot 2 |
| `frame_interval_ms` | ms | Animation speed, e.g. 100=10fps, 200=5fps |
| `image1.frames` | int | Number of animation frames in slot 1 |
| `image2.frames` | int | Number of animation frames in slot 2 |

---

## Linux: Running Without sudo

Find the HID device path:
```bash
python HIDList.py
# Look for: vendor_id=12815, product_id=20565, usage=146
# Note the path, e.g. /dev/hidraw3
```

Reassign ownership:
```bash
sudo chown $USER:$USER /dev/hidraw3
```

---

## Example: Notification Flash

Flash the keyboard red when a notification fires, then restore:
```bash
python GMK87Tool.py -c config-notification.json && sleep 2 && python GMK87Tool.py -c config.json
```
