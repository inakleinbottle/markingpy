


def euclidean(a, b):
    while b:
        a, b = b, a % b
    return a
