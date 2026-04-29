"""Generate tracker.ico — a 32x32 + 48x48 multi-size ICO using only stdlib."""
import os
import struct

HERE = os.path.dirname(os.path.abspath(__file__))


def make_image(size):
    """Returns BGRA pixel bytes (top-down) for a `size`x`size` icon.
    Design: rounded teal square, white clipboard outline, blue check-mark stripe."""
    BG_OUT  = (0, 0, 0, 0)              # transparent
    TEAL    = (0xA0, 0x9D, 0x14, 0xFF)  # BGRA: deep teal
    TEAL_LT = (0xC0, 0xBE, 0x3D, 0xFF)
    WHITE   = (0xFF, 0xFF, 0xFF, 0xFF)
    GREEN   = (0x4C, 0xAF, 0x50, 0xFF)
    GREY    = (0xCC, 0xCC, 0xCC, 0xFF)

    s = size
    pad = max(1, s // 16)
    radius = s // 6

    pixels = [[BG_OUT] * s for _ in range(s)]

    def in_rounded(x, y, x0, y0, x1, y1, r):
        if x < x0 or x > x1 or y < y0 or y > y1:
            return False
        # corner check
        for cx, cy in ((x0+r, y0+r), (x1-r, y0+r), (x0+r, y1-r), (x1-r, y1-r)):
            if (x < cx and y < cy and ((cx-x)**2 + (cy-y)**2) > r*r and (x < x0+r and y < y0+r)):
                return False
            if (x > cx and y < cy and ((x-cx)**2 + (cy-y)**2) > r*r and (x > x1-r and y < y0+r)):
                return False
            if (x < cx and y > cy and ((cx-x)**2 + (y-cy)**2) > r*r and (x < x0+r and y > y1-r)):
                return False
            if (x > cx and y > cy and ((x-cx)**2 + (y-cy)**2) > r*r and (x > x1-r and y > y1-r)):
                return False
        return True

    # Background rounded square (teal with subtle vertical gradient)
    for y in range(s):
        for x in range(s):
            if in_rounded(x, y, pad, pad, s-1-pad, s-1-pad, radius):
                # gradient from TEAL_LT (top) to TEAL (bottom)
                t = y / s
                b = int(TEAL_LT[0] + (TEAL[0]-TEAL_LT[0])*t)
                g = int(TEAL_LT[1] + (TEAL[1]-TEAL_LT[1])*t)
                r_ = int(TEAL_LT[2] + (TEAL[2]-TEAL_LT[2])*t)
                pixels[y][x] = (b, g, r_, 0xFF)

    # Clipboard body (white rounded rect)
    cb_x0, cb_y0 = int(s*0.25), int(s*0.28)
    cb_x1, cb_y1 = int(s*0.75), int(s*0.82)
    cb_r = max(1, s // 20)
    for y in range(cb_y0, cb_y1+1):
        for x in range(cb_x0, cb_x1+1):
            if in_rounded(x, y, cb_x0, cb_y0, cb_x1, cb_y1, cb_r):
                pixels[y][x] = WHITE

    # Clipboard clip on top (grey)
    clip_w = int(s*0.22)
    clip_h = max(2, s // 12)
    clip_x0 = (s - clip_w) // 2
    clip_y0 = cb_y0 - clip_h // 2
    for y in range(clip_y0, clip_y0 + clip_h):
        for x in range(clip_x0, clip_x0 + clip_w):
            if 0 <= x < s and 0 <= y < s:
                pixels[y][x] = GREY

    # Three text-like lines (teal)
    line_h = max(1, s // 24)
    for i in range(3):
        ly = int(s*0.42) + i * int(s*0.12)
        lx0 = cb_x0 + int(s*0.08)
        lx1 = cb_x1 - int(s*0.08)
        for y in range(ly, ly + line_h):
            for x in range(lx0, lx1):
                if 0 <= x < s and 0 <= y < s:
                    pixels[y][x] = TEAL

    # Green checkmark over bottom-right of clipboard
    thick = max(2, s // 14)
    cx, cy = int(s*0.62), int(s*0.66)
    # Short stroke: from (cx-d, cy) down-right to (cx, cy+d)
    d = int(s*0.08)
    for k in range(d):
        for t in range(thick):
            x, y = cx - d + k, cy + k + t - thick//2
            if 0 <= x < s and 0 <= y < s:
                pixels[y][x] = GREEN
    # Long stroke: from (cx, cy+d) up-right to (cx+2d, cy-d)
    for k in range(2*d):
        for t in range(thick):
            x, y = cx + k, cy + d - k + t - thick//2
            if 0 <= x < s and 0 <= y < s:
                pixels[y][x] = GREEN

    # Flatten BGRA bytes (top-down)
    flat = bytearray()
    for row in pixels:
        for px in row:
            flat += bytes(px)
    return bytes(flat)


def bmp_for_ico(size, bgra_topdown):
    """Build the DIB (BITMAPINFOHEADER + pixels bottom-up + AND mask) for ICO."""
    # BITMAPINFOHEADER: biHeight is doubled (image + AND mask)
    header = struct.pack("<IIIHHIIIIII",
                         40,            # biSize
                         size,          # biWidth
                         size * 2,      # biHeight (doubled)
                         1,             # biPlanes
                         32,            # biBitCount
                         0, 0, 0, 0, 0, 0)
    # Convert top-down BGRA to bottom-up
    row_bytes = size * 4
    rows = [bgra_topdown[i*row_bytes:(i+1)*row_bytes] for i in range(size)]
    pixels = b"".join(reversed(rows))
    # AND mask: 1 bit per pixel, all 0 (fully visible). Row size padded to 4 bytes.
    mask_row_bytes = ((size + 31) // 32) * 4
    and_mask = b"\x00" * (mask_row_bytes * size)
    return header + pixels + and_mask


def write_ico(path, sizes=(16, 32, 48, 64)):
    images = [(s, bmp_for_ico(s, make_image(s))) for s in sizes]
    out = bytearray()
    out += struct.pack("<HHH", 0, 1, len(images))  # ICONDIR
    offset = 6 + 16 * len(images)
    entries = bytearray()
    blobs = bytearray()
    for s, blob in images:
        w = 0 if s >= 256 else s
        h = 0 if s >= 256 else s
        entries += struct.pack("<BBBBHHII", w, h, 0, 0, 1, 32, len(blob), offset)
        blobs += blob
        offset += len(blob)
    out += entries + blobs
    with open(path, "wb") as f:
        f.write(out)


if __name__ == "__main__":
    out = os.path.join(HERE, "tracker.ico")
    write_ico(out)
    print(f"Wrote {out} ({os.path.getsize(out)} bytes)")
