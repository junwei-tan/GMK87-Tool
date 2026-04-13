#!/usr/bin/env python3
"""Upload a custom image or animated GIF to the GMK87 LCD display.

Protocol reverse-engineered by ikkentim/gmk87-usb-reverse.

Display: 240 x 135 pixels, RGB565 big-endian.

Upload sequence:
  0x01  init
  0x02  save
  0x23  buffer reset / freeze TFT
  0x01  init
  0x21  image frames (28 pixels = 56 bytes per HID packet), frame_idx 0..N-1
  0x02  save

After uploading, config.json is updated automatically and GMK87Tool.py is run.
"""

import hid
import time
import argparse
import json
import os
import sys
import subprocess
from PIL import Image

VENDOR_ID    = 12815   # 0x320F
PRODUCT_ID   = 20565   # 0x5055
USAGE_CONFIG = 146

LCD_W = 240
LCD_H = 135
BYTES_PER_PIXEL   = 2
PIXELS_PER_PACKET = 28
BYTES_PER_PACKET  = PIXELS_PER_PACKET * BYTES_PER_PIXEL  # 56 = 0x38

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH  = os.path.join(SCRIPT_DIR, 'config.json')
TOOL_PATH    = os.path.join(SCRIPT_DIR, 'GMK87Tool.py')


def checksum(buf):
    return sum(buf) & 0xFFFF


def build_packet(payload):
    """Wrap payload in a 64-byte HID packet with report ID and checksum."""
    pkt = bytearray(64)
    pkt[0] = 0x04
    for i, b in enumerate(payload[:61]):
        pkt[3 + i] = b
    chk = checksum(pkt[3:])
    pkt[1] = chk & 0xFF
    pkt[2] = (chk >> 8) & 0xFF
    return pkt


def send_cmd(dev, cmd_byte):
    dev.write(bytes(build_packet([cmd_byte])))
    time.sleep(0.02)


def frame_to_rgb565(img):
    """Convert a PIL Image to 240x135 RGB565 big-endian bytes."""
    img = img.convert('RGB').resize((LCD_W, LCD_H), Image.LANCZOS)
    buf = bytearray()
    for y in range(LCD_H):
        for x in range(LCD_W):
            r, g, b = img.getpixel((x, y))
            v = ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)
            buf.append((v >> 8) & 0xFF)
            buf.append(v & 0xFF)
    return buf


def load_frames(path):
    """Return list of RGB565 byte buffers, one per animation frame."""
    img = Image.open(path)
    frames = []

    if getattr(img, 'is_animated', False) or img.format == 'GIF':
        n = getattr(img, 'n_frames', 1)
        print(f"  GIF detected: {n} frames")
        for i in range(n):
            img.seek(i)
            frames.append(frame_to_rgb565(img.copy()))
            if (i + 1) % 5 == 0 or i == n - 1:
                print(f"  converted {i+1}/{n} frames", flush=True)
    else:
        frames.append(frame_to_rgb565(img))

    return frames


def upload_frame(dev, pixel_bytes, frame_idx):
    """Stream one full image frame to the keyboard."""
    total = LCD_W * LCD_H * BYTES_PER_PIXEL

    packets = 0
    for offset in range(0, total, BYTES_PER_PACKET):
        chunk = pixel_bytes[offset : offset + BYTES_PER_PACKET]

        payload = bytearray(61)
        payload[0] = 0x21
        payload[1] = BYTES_PER_PACKET
        payload[2] = offset & 0xFF
        payload[3] = (offset >> 8) & 0xFF
        payload[4] = frame_idx
        for i, b in enumerate(chunk):
            payload[5 + i] = b

        dev.write(bytes(build_packet(payload)))
        packets += 1
        time.sleep(0.002)

    return packets


def update_config(slot, n_frames):
    """Update config.json with the new frame count and show_image setting."""
    with open(CONFIG_PATH) as f:
        cfg = json.load(f)

    cfg['config']['show_image'] = slot
    if slot == 1:
        cfg['config']['image1']['frames'] = n_frames
    else:
        cfg['config']['image2']['frames'] = n_frames

    # Turn off debug for cleaner output
    cfg['debug'] = False

    with open(CONFIG_PATH, 'w') as f:
        json.dump(cfg, f, indent=4)

    print(f"  config.json updated: show_image={slot}, frames={n_frames}")


def find_device():
    devs = hid.enumerate(VENDOR_ID, PRODUCT_ID)
    info = next((d for d in devs if d['usage'] == USAGE_CONFIG), None)
    if not info:
        print("GMK87 not found. Make sure it is connected via USB cable.")
        sys.exit(1)
    return info


def main():
    parser = argparse.ArgumentParser(
        description='Upload an image or GIF to the GMK87 LCD (240x135).')
    parser.add_argument('image', help='Image or GIF file to upload')
    parser.add_argument('--slot', type=int, default=1, choices=[1, 2],
                        help='Image slot (1 or 2, default: 1)')
    parser.add_argument('--fps', type=int, default=10,
                        help='Playback FPS for GIFs (default: 10)')
    args = parser.parse_args()

    if not os.path.exists(args.image):
        print(f"Error: file not found: {args.image}")
        sys.exit(1)

    info = find_device()
    dev = hid.device()
    dev.open_path(info['path'])

    try:
        print(f"Connected: {dev.get_product_string()}")
        print(f"Loading {args.image}...")
        all_frames = load_frames(args.image)
        n = len(all_frames)
        print(f"  {n} frame(s), {len(all_frames[0])} bytes each")

        print("Sending upload sequence...")
        send_cmd(dev, 0x01)
        send_cmd(dev, 0x02)
        send_cmd(dev, 0x23)
        send_cmd(dev, 0x01)

        total_packets = 0
        for i, frame_bytes in enumerate(all_frames):
            print(f"  uploading frame {i+1}/{n}...", flush=True)
            total_packets += upload_frame(dev, frame_bytes, frame_idx=i)

        send_cmd(dev, 0x02)
        print(f"  {total_packets} packets sent total")

        print("Updating config.json...")
        update_config(args.slot, n)

        print("Activating on display...")
        subprocess.run([sys.executable, TOOL_PATH, '-c', CONFIG_PATH], check=True)

        print(f"\nDone! {n}-frame animation playing on slot {args.slot} at {args.fps}fps.")

    finally:
        dev.close()


if __name__ == '__main__':
    main()
