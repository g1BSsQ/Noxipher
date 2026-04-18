import abc
from typing import TypeVar

T = TypeVar("T", bound="FieldElement")

class FieldElement(abc.ABC):
    MODULUS: int
    value: int

    def __init__(self, value: int | bytes | "FieldElement") -> None:
        if isinstance(value, FieldElement):
            self.value = value.value
        elif isinstance(value, bytes):
            self.value = int.from_bytes(value, "little") % self.MODULUS
        else:
            self.value = value % self.MODULUS

    def __add__(self: T, other: T | int) -> T:
        other_val = other.value if isinstance(other, FieldElement) else other
        return self.__class__(self.value + other_val)

    def __sub__(self: T, other: T | int) -> T:
        other_val = other.value if isinstance(other, FieldElement) else other
        return self.__class__(self.value - other_val)

    def __mul__(self: T, other: T | int) -> T:
        other_val = other.value if isinstance(other, FieldElement) else other
        return self.__class__(self.value * other_val)

    def __truediv__(self: T, other: T | int) -> T:
        other_val = other.value if isinstance(other, FieldElement) else other
        # Modular inverse using Fermat's Little Theorem (modulus is prime)
        inv = pow(other_val, self.MODULUS - 2, self.MODULUS)
        return self.__class__(self.value * inv)

    def __pow__(self: T, exponent: int) -> T:
        return self.__class__(pow(self.value, exponent, self.MODULUS))

    def __neg__(self: T) -> T:
        return self.__class__(-self.value)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, (FieldElement, int)):
            return False
        other_val = other.value if isinstance(other, FieldElement) else other
        return bool((self.value % self.MODULUS) == (other_val % self.MODULUS))

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({hex(self.value)})"

    def to_bytes(self, length: int = 32) -> bytes:
        return self.value.to_bytes(length, "little")

    @classmethod
    def from_le_bytes(cls: type[T], data: bytes) -> T:
        """Create field element from little-endian bytes."""
        return cls(data)

    @classmethod
    def from_uniform_bytes(cls: type[T], data: bytes) -> T:
        """Wide reduction for field elements (e.g. from 64 bytes)."""
        return cls(int.from_bytes(data, "little"))

class Fr(FieldElement):
    """BLS12-381 Scalar Field (often called Fq in Midnight internal circuit code)."""
    MODULUS = 0x73eda753299d7d483339d80809a1d80553bda402fffe5bfeffffffff00000001

class EmbeddedFr(FieldElement):
    """JubJub Scalar Field."""
    MODULUS = 0x0e7db4ea6533afa906673b0101343b00a6682093ccc81082d0970e5ed6f72cb7

# Alias for clarity in Poseidon
PoseidonField = Fr
