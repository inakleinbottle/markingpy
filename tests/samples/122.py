
def gcd(a,b):
    for i in range(10):
        t = b
        b = b % a
        a = t
        if b == 0:
            return a
