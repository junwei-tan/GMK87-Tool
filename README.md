# GMK87 Tool

Configure the Zuoya GMK87 keyboard over USB — upload images/GIFs to the LCD, control lighting, and sync the clock. Works on macOS and Linux.

*Based on [ikkentim/gmk87-usb-reverse](https://github.com/ikkentim/gmk87-usb-reverse).*

## Install

**macOS**
```bash
brew install hidapi
pip install hid pillow
```

**Linux (Arch)**
```bash
pacman -S python-hidapi
pip install pillow
```

**Linux (Debian/Ubuntu)**
```bash
apt install libhidapi-hidraw0
pip install hid pillow
```

Then clone and verify your keyboard is detected:
```bash
git clone https://github.com/junwei-tan/GMK87-Tool.git
cd GMK87-Tool
python HIDList.py  # should show vendor_id=12815, product_id=20565
```

## Upload an image or GIF

The display is 240×135. Any image format works — it's auto-resized.

```bash
python upload_image.py photo.jpg              # static image, slot 1
python upload_image.py animation.gif --slot 2 # animated GIF, slot 2
```

Config and activation happen automatically. To switch back to the clock, set `"show_image": 0` in `config.json` and run `python GMK87Tool.py -c config.json`.

> **Note:** Uploading clears both image slots at once (hardware limitation).

## Configure lighting

Edit `config.json` then run:
```bash
python GMK87Tool.py -c config.json
```

Key settings:

| Field | Values | Description |
|---|---|---|
| `show_image` | 0–2 | 0=clock, 1=slot 1, 2=slot 2 |
| `frame_interval_ms` | ms | GIF speed — 100=10fps, 200=5fps |
| `underglow_effect` | 0–18 | 0=off, 1=wave, 5=breathing, 6=solid, 11=rainbow |
| `underglow_brightness` | 0–9 | 0=off, 9=max |
| `underglow_speed` | 0–9 | 0=fast, 9=slow |
| `underglow_hue` | 0–255 RGB | Color when `underglow_rainbow=0` |
| `led_color` | 0–8 | 0=red 1=orange 2=yellow 3=green 4=teal 5=blue 6=purple 7=white 8=off |

Full config reference: see comments in `GMK87Tool.py`.

## Examples

Flash red on a notification, then restore:
```bash
python GMK87Tool.py -c config-notification.json && sleep 2 && python GMK87Tool.py -c config.json
```

## Linux: no sudo

```bash
python HIDList.py  # find path for usage=146, e.g. /dev/hidraw3
sudo chown $USER:$USER /dev/hidraw3
```
