import math

from collections import deque

def to_gray(pixel_bytes: bytes, w: int, h: int) -> list:
    """
    in: 8 bit BGRA 
    out: matrix of grayscaled pixels
    """
    gray = [[0.0] * w for _ in range(h)]
    i = 0
    for y in range(h):
        row = gray[y]
        for x in range(w):
            b = pixel_bytes[i + 0]
            g = pixel_bytes[i + 1]
            r = pixel_bytes[i + 2]
            i += 4

            # Luma-like grayscale
            v = 0.299 * r + 0.587 * g + 0.114 * b
            row[x] = v
    return gray


def gaussian_kernel(kernel_size: int, sigma: float) -> list:
    """generate gaussian kernel (normalized)"""
    
    # size must be odd
    assert kernel_size % 2 == 1 and kernel_size >= 3

    kernel = [[0.0] * kernel_size for _ in range(kernel_size)]
    center = kernel_size // 2
    sum = 0.0

    for y in range(kernel_size):
        for x in range(kernel_size):
            dy = y - center
            dx = x - center
            weight = math.exp(-(dx * dx + dy * dy) / 2.0 * sigma * sigma)
            kernel[y][x] = weight
            sum += weight

    # normalize
    inv = 1.0
    if sum != 0:
        inv = 1.0 / sum

    for y in range(kernel_size):
        for x in range(kernel_size):
            kernel[y][x] *= inv

    return kernel


def convolve(image: list, kernel: list) -> list:
    """edge-replicating convolution (clamp at borders)."""
    height = len(image)
    width = len(image[0])
    kernel_size = len(kernel)
    kernel_center = kernel_size // 2
    out = [[0.0] * width for _ in range(height)]

    for y in range(height):
        for x in range(width):
            sum = 0.0
            for ky in range(kernel_size):
                src_y = y + (ky - kernel_center)
                if src_y < 0:
                    src_y = 0
                elif src_y >= height:
                    src_y = height - 1
                row_img = image[src_y]
                row_k = kernel[ky]
                for kx in range(kernel_size):
                    src_x = x + (kx - kernel_center)
                    if src_x < 0:
                        src_x = 0
                    elif src_x >= width:
                        src_x = width - 1
                    sum += row_img[src_x] * row_k[kx]
            out[y][x] = sum

    return out


def sobel(image: list) -> tuple:
    """
    Sobel gradient.
    out:
      mag[h][w] : gradient magnitude
      ang[h][w] : angle in degrees in <0, 180)
    """
    h = len(image)
    w = len(image[0])

    gxk = [[-1, 0, 1],
           [-2, 0, 2],
           [-1, 0, 1]]
    gyk = [[ 1, 2, 1],
           [ 0, 0, 0],
           [-1,-2,-1]]

    mag = [[0.0] * w for _ in range(h)]
    ang = [[0.0] * w for _ in range(h)]

    for y in range(1, h - 1):
        for x in range(1, w - 1):
            gx = 0.0
            gy = 0.0
            for j in range(3):
                yy = y + j - 1
                row = image[yy]
                for i in range(3):
                    xx = x + i - 1
                    v = row[xx]
                    gx += v * gxk[j][i]
                    gy += v * gyk[j][i]

            m = math.hypot(gx, gy)
            a = math.degrees(math.atan2(gy, gx))
            if a < 0.0:
                a += 180.0

            mag[y][x] = m
            ang[y][x] = a

    return mag, ang


def non_max_suppression(mag: list, ang: list) -> list:
    """Thin edges by suppressing non-maxima along gradient direction."""
    h = len(mag)
    w = len(mag[0])
    out = [[0.0] * w for _ in range(h)]

    for y in range(1, h - 1):
        for x in range(1, w - 1):
            a = ang[y][x]

            # Quantize to 4 directions
            if (0 <= a < 22.5) or (157.5 <= a < 180):
                n1 = mag[y][x - 1]
                n2 = mag[y][x + 1]
            elif 22.5 <= a < 67.5:
                n1 = mag[y - 1][x + 1]
                n2 = mag[y + 1][x - 1]
            elif 67.5 <= a < 112.5:
                n1 = mag[y - 1][x]
                n2 = mag[y + 1][x]
            else:
                n1 = mag[y - 1][x - 1]
                n2 = mag[y + 1][x + 1]

            m = mag[y][x]
            out[y][x] = m if (m >= n1 and m >= n2) else 0.0

    return out

def double_threshold_and_hysteresis(nms: list, low_ratio: float, high_ratio: float) -> list:
    """
    - edges stores 0=none, 1=weak, 2=strong
    - BFS promotes weak->strong if connected to any strong (8-neighborhood)
    - final output is 0/255
    """
    h = len(nms)
    w = len(nms[0])

    maxv = max(max(row) for row in nms)
    if maxv <= 1e-9:
        return [[0] * w for _ in range(h)]

    high = high_ratio * maxv
    low = low_ratio * high

    edges = [[0] * w for _ in range(h)]
    q = deque()

    # classify pixels
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            v = nms[y][x]
            if v >= high:
                edges[y][x] = 2  # strong
                q.append((y, x))
            elif v >= low:
                edges[y][x] = 1  # weak

    # hysteresis (8-connected)
    neighbors = [(-1,-1),(-1,0),(-1,1),
                 ( 0,-1),       ( 0,1),
                 ( 1,-1),( 1,0),( 1,1)]

    while q:
        y, x = q.popleft()
        for dy, dx in neighbors:
            yy, xx = y + dy, x + dx
            if edges[yy][xx] == 1:      # weak -> strong
                edges[yy][xx] = 2
                q.append((yy, xx))

    # convert labels -> 0/255
    for y in range(h):
        row = edges[y]
        for x in range(w):
            row[x] = 255 if row[x] == 2 else 0

    return edges



def edges_to_BGRA(edges: list) -> bytes:
    """Convert edge map (0/255) to BGRA bytes (opaque)."""
    h = len(edges)
    w = len(edges[0])
    out = bytearray(w * h * 4)
    i = 0
    for y in range(h):
        row = edges[y]
        for x in range(w):
            v = row[x]
            out[i + 0] = v  # B
            out[i + 1] = v  # G
            out[i + 2] = v  # R
            out[i + 3] = 255
            i += 4
    return bytes(out)
