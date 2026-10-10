
import base64
import hashlib
import secrets
import time
from math import gcd
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import dsa, ec, padding, rsa


"""
Our two key holders will be approprietly named Alice and Bob. Bob is Receiver, Alice is Sender.
We will suppose that the message has already been sent and Bob want s to verify it with its signature.
The message shall be the same for all. All algorithms have been split in 3, key creation, signage and
verification for simplicity. The time it takes is calculated from the moment that it takes to sign,
till the momment that it takes to sign (considering that the keys are not meant to be generated from
scratch every time).
"""
Alice = {
    "private_key": None,
}

Bob = {
    "Alices_public_key": None
}

plaintext = "This is a test message"


def hash_message(M):
    return int.from_bytes(hashlib.sha256(M).digest(), "big")

hash=hashes.SHA256()
pad=padding.PKCS1v15()

def curve_order(curve):
    low, high = 1, 2 ** curve.key_size
    while high - low > 1:
        mid = (low + high) // 2
        try:
            ec.derive_private_key(mid, curve)
            low = mid
        except ValueError:
            high = mid
    return high

n = curve_order(ec.SECP256R1())

def library_point(k):
    nums = ec.derive_private_key(k, ec.SECP256R1()).public_key().public_numbers()
    return nums.x, nums.y

def curve_check(pts):
    (x1, y1), (x2, y2), (x3, y3) = pts
    f1, f2, f3 = y1*y1 - x1**3, y2*y2 - x2**3, y3*y3 - x3**3
    return f1*(x2 - x3) + f2*(x3 - x1) + f3*(x1 - x2)

pts = [library_point(k) for k in range(1, 6)]
P = gcd(gcd(curve_check(pts[0:3]), curve_check(pts[1:4])), curve_check(pts[2:5]))
for f in range(2, 10000):
    while P % f == 0 and P // f > 2**255:
        P //= f

(x1, y1), (x2, y2) = pts[0], pts[1]
A = ((y2*y2 - x2**3) - (y1*y1 - x1**3)) * pow(x2 - x1, -1, P) % P
G = pts[0]

#DSA###########################################################

def d_sign(message, User):
    PRa = User["private_key"].private_numbers()
    x = PRa.x                                   #private key
    p = PRa.public_numbers.parameter_numbers.p  #these are the PUg
    q = PRa.public_numbers.parameter_numbers.q
    g = PRa.public_numbers.parameter_numbers.g
    H_M = hash_message(message)
    while True:
        k = secrets.randbelow(q - 1) + 1        #the randomly generated k
        r = pow(g, k, p) % q
        s = (pow(k, -1, q) * (H_M + x * r)) % q
        if r != 0 and s != 0:
            return [r, s]


def d_verify(message, signature, User):
    PUa = User["Alices_public_key"].public_numbers()
    y = PUa.y                                         #public key y
    p = PUa.parameter_numbers.p                       #PUg
    q = PUa.parameter_numbers.q
    g = PUa.parameter_numbers.g
    r, s = signature
    if not (0 < r < q and 0 < s < q):
        return False
    H_M = hash_message(message)
    w = pow(s, -1, q)
    u1 = (H_M * w) % q
    u2 = (r * w) % q
    v = ((pow(g, u1, p) * pow(y, u2, p)) % p) % q
    return v == r


def DSA(Sender, Receiver, message):
    start = time.perf_counter()
    signature = d_sign(message, Sender)
    print(f"Signature: {signature}")
    is_valid = d_verify(message, signature, Receiver)
    end = time.perf_counter()
    print(f"DSA Time: {end - start}")
    return is_valid, end - start


#RSA################################################################

def r_sign(message, User):
    PRa = User["private_key"].private_numbers()
    d = PRa.d                       #private key
    n = PRa.public_numbers.n
    H_M = hash_message(message)
    signature = pow(H_M, d, n)
    return signature


def r_verify(message, signature, User):
    PUa = User["Alices_public_key"].public_numbers()
    e= PUa.e                        #public key
    n= PUa.n
    H_M = hash_message(message)
    decrypted = pow(signature, e, n)
    return decrypted == H_M


def RSA(Sender, Receiver, message):
    start = time.perf_counter()
    signature = r_sign(message, Sender)
    print(f"Signature: {signature}")
    is_valid = r_verify(message, signature, Receiver)
    end = time.perf_counter()
    print(f"RSA Time: {end - start}")
    return is_valid, end - start

#ECDSA#################################################################################


def e_sign(message, User):
    PRa = User["private_key"].private_numbers()
    d = PRa.private_value                            #private key
    H_M = hash_message(message)
    while True:
        k = secrets.randbelow(n - 1) + 1
        kG = ec.derive_private_key(k, ec.SECP256R1()).public_key().public_numbers()
        r = kG.x % n
        s = (pow(k, -1, n) * (H_M + d * r)) % n
        if r != 0 and s != 0:
            return [r, s]


def point_add(P1, P2):
    if P1 is None: return P2
    if P2 is None: return P1
    x1, y1 = P1
    x2, y2 = P2
    if x1 == x2 and (y1 + y2) % P == 0: return None
    if P1 == P2: lam = (3 * x1 * x1 + A) * pow(2 * y1, -1, P) % P
    else:        lam = (y2 - y1) * pow(x2 - x1, -1, P) % P
    x3 = (lam * lam - x1 - x2) % P
    return (x3, (lam * (x1 - x3) - y1) % P)

def point_mul(k, P1):
    result = None
    while k:
        if k & 1: result = point_add(result, P1)
        P1 = point_add(P1, P1)
        k >>= 1
    return result

def e_verify(M, signature, User):
    PUa = User["Alices_public_key"].public_numbers()
    Q = (PUa.x, PUa.y)                                #public key
    r, s = signature
    if not (0 < r < n and 0 < s < n):
        return False
    H_M = hash_message(M)
    w = pow(s, -1, n)
    u1 = (H_M * w) % n
    u2 = (r * w) % n
    point = point_add(point_mul(u1, G), point_mul(u2, Q))   #(x2, y2) = u1*G + u2*Q
    v = point[0] % n
    return v == r

def ECDSA(Sender, Receiver, message):
    start = time.perf_counter()
    signature = e_sign(message, Sender)
    print(f"Signature: {signature}")
    is_valid = e_verify(message, signature, Receiver)
    end = time.perf_counter()
    print(f"ECDSA Time: {end - start}")
    return is_valid, end - start



def generate_keys(algorithm):
    match algorithm:
        case "DSA":
            Alice["private_key"] = dsa.generate_private_key(key_size=2048)      #the private key will aslo contain the public key
            Bob["Alices_public_key"] = Alice["private_key"].public_key()
        case "RSA":
            Alice["private_key"] = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            Bob["Alices_public_key"] = Alice["private_key"].public_key()
        case "ECDSA":
            Alice["private_key"] = ec.generate_private_key(ec.SECP256R1())
            Bob["Alices_public_key"] = Alice["private_key"].public_key()
        case _:
            raise ValueError(f"Unsupported algorithm: {algorithm}")

def main():
    generate_keys("DSA")
    DSA_valid, DSA_time = DSA(Alice, Bob, plaintext.encode())
    print(f"DSA Signature Valid: {DSA_valid}")
    generate_keys("RSA")
    RSA_valid, RSA_time = RSA(Alice, Bob, plaintext.encode())
    print(f"RSA Signature Valid: {RSA_valid}")
    generate_keys("ECDSA")
    ECDSA_valid, ECDSA_time = ECDSA(Alice, Bob, plaintext.encode())
    print(f"ECDSA Signature Valid: {ECDSA_valid}")

    


if __name__ == "__main__":
	main()
