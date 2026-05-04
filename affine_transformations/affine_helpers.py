import math

# BGRA (Blue, Green, Red, Alpha) bajty, 8-bit na kanál

def _get_pixel_bgra(src: bytes, w: int, x: int, y: int):
    i = (y * w + x) * 4
    return src[i], src[i + 1], src[i + 2], src[i + 3]

def _set_pixel_bgra(dst: bytearray, w: int, x: int, y: int, b: int, g: int, r: int, a: int):
    i = (y * w + x) * 4
    dst[i] = b
    dst[i + 1] = g
    dst[i + 2] = r
    dst[i + 3] = a

def _invert_2x2(a: float, b: float, c: float, d: float):
    det = a * d - b * c
    if abs(det) < 1e-12:
        return None
    inv_det = 1.0 / det
    return ( d * inv_det, -b * inv_det,
            -c * inv_det,  a * inv_det)

def apply_affine_bgra_u8(
    src_bytes: bytes,
    w: int,
    h: int,
    a: float, b: float, tx: float,
    c: float, d: float, ty: float,
    background_transparent: bool = True
) -> bytes:
    """
    Afinni transformácia (affine transformation):
      [x']   [a b tx] [x]
      [y'] = [c d ty] [y]
      [1 ]   [0 0  1] [1]

    Robíme inverse mapping (z výstupu do zdroja):
      pre každý (x', y') spočítame (x, y) cez inverziu 2x2 a posun.
    Vzorkovanie: nearest-neighbor (najbližší sused).
    """
    inv = _invert_2x2(a, b, c, d)
    if inv is None:
        # degenerovaná matica -> vráť pôvodné
        return src_bytes

    ia, ib, ic, id = inv

    dst = bytearray(w * h * 4)

    # ak chceš pozadie čierne nepriehľadné, zmeň toto:
    bg_b, bg_g, bg_r, bg_a = (0, 0, 0, 0) if background_transparent else (0, 0, 0, 255)

    for y_out in range(h):
        for x_out in range(w):
            # odčítaj transláciu
            x0 = x_out - tx
            y0 = y_out - ty

            # inverse 2x2
            x_src = ia * x0 + ib * y0
            y_src = ic * x0 + id * y0

            # nearest neighbor
            xs = int(round(x_src))
            ys = int(round(y_src))

            if 0 <= xs < w and 0 <= ys < h:
                b0, g0, r0, a0 = _get_pixel_bgra(src_bytes, w, xs, ys)
                _set_pixel_bgra(dst, w, x_out, y_out, b0, g0, r0, a0)
            else:
                _set_pixel_bgra(dst, w, x_out, y_out, bg_b, bg_g, bg_r, bg_a)

    return bytes(dst)

def build_affine_matrix(
    mode: str,
    w: int, h: int,
    dx: float = 0.0, dy: float = 0.0,
    angle_deg: float = 0.0,
    sx: float = 1.0, sy: float = 1.0,
    shx: float = 0.0, shy: float = 0.0
):
    """
    Vráti (a,b,tx,c,d,ty) pre zvolený režim.
    Rotácia/scale/shear sú okolo stredu obrázka.
    """
    cx = (w - 1) / 2.0
    cy = (h - 1) / 2.0

    if mode == "translate":
        return (1.0, 0.0, dx,
                0.0, 1.0, dy)

    if mode == "rotate":
        theta = math.radians(angle_deg)
        cos_t = math.cos(theta)
        sin_t = math.sin(theta)

        # R okolo stredu: T(c) * R * T(-c)
        a = cos_t
        b = -sin_t
        c = sin_t
        d = cos_t
        tx = cx - a * cx - b * cy
        ty = cy - c * cx - d * cy
        return (a, b, tx, c, d, ty)

    if mode == "scale":
        # S okolo stredu: T(c) * S * T(-c)
        a = sx
        b = 0.0
        c = 0.0
        d = sy
        tx = cx - a * cx
        ty = cy - d * cy
        return (a, b, tx, c, d, ty)

    if mode == "shear":
        # shear okolo stredu:
        # [1 shx; shy 1]
        a = 1.0
        b = shx
        c = shy
        d = 1.0
        tx = cx - a * cx - b * cy
        ty = cy - c * cx - d * cy
        return (a, b, tx, c, d, ty)

    # fallback
    return (1.0, 0.0, 0.0,
            0.0, 1.0, 0.0)
