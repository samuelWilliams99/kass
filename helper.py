def clamp(n, min_n, max_n):
    return max(min(n, max_n), min_n)

def renormalize(n, from_min, from_max, to_min, to_max):
    delta1 = from_max - from_min
    delta2 = to_max - to_min
    return clamp((delta2 * (n - from_min) / delta1) + to_min, to_min, to_max)