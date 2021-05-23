def clamp(n, min_n, max_n):
    return max(min(n, max_n), min_n)

def renormalize(n, from_min, from_max, to_min, to_max):
    delta1 = from_max - from_min
    delta2 = to_max - to_min
    return clamp((delta2 * (n - from_min) / delta1) + to_min, to_min, to_max)

def hsv_lerp(start_col, end_col, prog, increasing=None, loops=0):
    (start_hue, start_sat, start_val) = start_col
    (end_hue, end_sat, end_val) = end_col
    if increasing == True and end_hue < start_hue: end_hue += 360
    if increasing == False and start_hue < end_hue: start_hue += 360

    end_hue += (1 if increasing else -1) * loops * 360

    hue = (start_hue + prog * (end_hue - start_hue)) % 360
    sat = (start_sat + prog * (end_sat - start_sat))
    val = (start_val + prog * (end_val - start_val))

    return (hue, sat, val)

def rgb_lerp(start_col, end_col, prog):
    (start_r, start_g, start_b) = start_col
    (end_r, end_g, end_b) = end_col

    r = (start_r + prog * (end_r - start_r))
    g = (start_g + prog * (end_g - start_g))
    b = (start_b + prog * (end_b - start_b))

    return (r, g, b)

# i didnt write this, apparently its faster than other solutions, and we do love speed
def hsv_to_rgb(col):
    (h, s, v) = col
    h/=360.0
    if s == 0.0: v*=255; return (v, v, v)
    i = int(h*6.) # XXX assume int() truncates!
    f = (h*6.)-i; p,q,t = int(255*(v*(1.-s))), int(255*(v*(1.-s*f))), int(255*(v*(1.-s*(1.-f)))); v*=255; i%=6
    if i == 0: return (v, t, p)
    if i == 1: return (q, v, p)
    if i == 2: return (p, v, t)
    if i == 3: return (p, q, v)
    if i == 4: return (t, p, v)
    if i == 5: return (v, p, q)

def rgb_to_hsv(col):
    (r, g, b) = col
    r, g, b = r/255.0, g/255.0, b/255.0
    mx = max(r, g, b)
    mn = min(r, g, b)
    df = mx-mn
    if mx == mn:
        h = 0
    elif mx == r:
        h = (60 * ((g-b)/df) + 360) % 360
    elif mx == g:
        h = (60 * ((b-r)/df) + 120) % 360
    elif mx == b:
        h = (60 * ((r-g)/df) + 240) % 360
    if mx == 0:
        s = 0
    else:
        s = (df/mx)
    v = mx
    return (h, s, v)