from typing import Optional
from .fields import Fr, EmbeddedFr

class JubJubPoint:
    """
    Implementation of JubJub elliptic curve point in Twisted Edwards coordinates.
    Matches Midnight's curves/src/jubjub/curve.rs.
    Equation: -x^2 + y^2 = 1 + d*x^2*y^2
    """
    # d = -(10240/10241) mod p
    D = Fr(0x2a9318e74bfa2b48f5fd9207e6bd7fd4292d7f6d37579d2601065fd6d6343eb1)
    A = Fr(-1)

    def __init__(self, u: Fr, v: Fr):
        self.u = u
        self.v = v

    @classmethod
    def identity(cls) -> 'JubJubPoint':
        return cls(Fr(0), Fr(1))

    @classmethod
    def generator(cls) -> 'JubJubPoint':
        # From JubjubAffine::generator() in Rust
        u = Fr(0x62edcbb8bf3787c88b0f03ddd60a8187caf55d1b29bf81afe4b3d35df1a7adfe)
        v = Fr(11)
        return cls(u, v)

    def __add__(self, other: 'JubJubPoint') -> 'JubJubPoint':
        # Twisted Edwards addition formula (a = -1)
        # x3 = (x1y2 + y1x2) / (1 + dx1x2y1y2)
        # y3 = (y1y2 + x1x2) / (1 - dx1x2y1y2)
        
        x1, y1 = self.u, self.v
        x2, y2 = other.u, other.v
        
        common = self.D * x1 * x2 * y1 * y2
        
        new_u = (x1 * y2 + y1 * x2) / (Fr(1) + common)
        new_v = (y1 * y2 + x1 * x2) / (Fr(1) - common)
        
        return JubJubPoint(new_u, new_v)

    def __mul__(self, scalar: EmbeddedFr) -> 'JubJubPoint':
        """Scalar multiplication using double-and-add."""
        res = JubJubPoint.identity()
        temp = self
        
        # We use the raw integer value of the scalar for bit-wise operations
        n = scalar.value
        while n > 0:
            if n & 1:
                res = res + temp
            temp = temp + temp
            n >>= 1
        return res

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, JubJubPoint):
            return False
        return self.u == other.u and self.v == other.v

    def __repr__(self) -> str:
        return f"JubJubPoint(u={self.u}, v={self.v})"

    def to_bytes(self) -> bytes:
        """
        Compressed encoding: v-coordinate (32 bytes LE) 
        with the sign of u in the MSB.
        Matches JubjubAffine::to_bytes.
        """
        v_bytes = bytearray(self.v.to_bytes())
        u_bytes = self.u.to_bytes()
        
        # Sign bit of u is encoded in the highest bit of the 32nd byte
        # (Since JubJub is over BLS Fq, and Fq is < 2^255, the top bit is always 0)
        # Actually, Midnight's implementation: tmp[31] |= u[0] << 7;
        # Wait, u[0] is the LEAST significant byte of u.
        # So it takes the parity of u? No, it's just a sign bit.
        # Let's check: tmp[31] |= u[0] << 7; 
        # In Rust, u.to_bytes_le()[0] is the first byte. 
        # So it's bit 0 of the first byte of u.
        if u_bytes[0] & 1:
            v_bytes[31] |= 0x80
            
        return bytes(v_bytes)
