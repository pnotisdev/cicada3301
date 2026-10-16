"""Page-30 grid: every cell is |3301 - p_k| with Fibonacci-step prime indices, laid out as a spiral."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import grid30  # noqa: E402


class Grid30(unittest.TestCase):
    def test_reconstruction_matches_page(self):
        ks, ps, rec = grid30.reconstruct()
        self.assertEqual(ks[:8], [1, 2, 3, 4, 6, 9, 14, 22])
        self.assertEqual(rec, grid30.grid_values())

    def test_index_steps_are_fibonacci(self):
        ks = grid30.fib_indices(16)
        steps = [b - a for a, b in zip(ks, ks[1:])]
        self.assertEqual(steps[3:], [steps[i + 1] + steps[i + 2] for i in range(len(steps) - 3)])


if __name__ == "__main__":
    unittest.main()
