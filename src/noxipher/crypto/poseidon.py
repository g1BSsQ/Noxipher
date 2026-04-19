from .fields import Fr
from .poseidon_constants import MDS, ROUND_CONSTANTS


class Poseidon:
    """
    Implementation of Poseidon hash function for BLS12-381 scalar field.
    Matches Midnight's circuits/src/hash/poseidon/poseidon_cpu.rs.
    """

    WIDTH = 3
    RATE = 2
    FULL_ROUNDS = 8
    PARTIAL_ROUNDS = 60

    def __init__(self) -> None:
        # We use the raw CPU implementation (no skips) for maximum clarity and 1:1 parity
        pass

    @staticmethod
    def sbox(x: Fr) -> Fr:
        """x^5 S-box."""
        return x**5

    def linear_layer(self, state: list[Fr], round_index: int) -> list[Fr]:
        """Matrix multiplication + addition of round constants."""
        new_state = [Fr(0)] * self.WIDTH

        # Determine next round constants
        if round_index + 1 < len(ROUND_CONSTANTS):
            constants = ROUND_CONSTANTS[round_index + 1]
        else:
            constants = [0, 0, 0]

        for i in range(self.WIDTH):
            val = Fr(0)
            for j in range(self.WIDTH):
                val += Fr(MDS[i][j]) * state[j]
            new_state[i] = val + Fr(constants[i])

        return new_state

    def permutation(self, state: list[Fr]) -> list[Fr]:
        """The core Poseidon permutation."""
        # 1. Add first round constants
        for i in range(self.WIDTH):
            state[i] += Fr(ROUND_CONSTANTS[0][i])

        total_rounds = self.FULL_ROUNDS + self.PARTIAL_ROUNDS
        half_full = self.FULL_ROUNDS // 2

        # 2. First half of full rounds
        for r in range(half_full):
            # S-box on all elements
            for i in range(self.WIDTH):
                state[i] = self.sbox(state[i])
            state = self.linear_layer(state, r)

        # 3. Partial rounds
        for r in range(half_full, half_full + self.PARTIAL_ROUNDS):
            # S-box on LAST element only
            state[self.WIDTH - 1] = self.sbox(state[self.WIDTH - 1])
            state = self.linear_layer(state, r)

        # 4. Second half of full rounds
        for r in range(half_full + self.PARTIAL_ROUNDS, total_rounds):
            # S-box on all elements
            for i in range(self.WIDTH):
                state[i] = self.sbox(state[i])
            state = self.linear_layer(state, r)

        return state

    def hash(self, inputs: list[Fr]) -> Fr:
        """Sponge-based hashing of multiple field elements."""
        # Matches SpongeCPU::init
        register = [Fr(0), Fr(0), Fr(len(inputs))]

        # Absorb chunks
        for i in range(0, len(inputs), self.RATE):
            chunk = inputs[i : i + self.RATE]
            # If the last chunk is partial, padding is handled by the caller or implicitly?
            # Actually, midnight's PoseidonChip::hash expects fixed length or handles padding.
            # Most transient_hash calls are on fixed-size structs.
            for j, val in enumerate(chunk):
                register[j] += val
            register = self.permutation(register)

        return register[0]


def transient_hash(elems: list[Fr]) -> Fr:
    """Convenience function for Poseidon hashing."""
    p = Poseidon()
    return p.hash(elems)
