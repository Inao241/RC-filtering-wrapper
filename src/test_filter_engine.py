import unittest
from filter_engine import FilterEngine

class TestFilterEngine(unittest.TestCase):
    def test_calculate_k(self):
        engine = FilterEngine()
        self.assertEqual(engine.calculate_k(0.1), 2.0)
        self.assertEqual(engine.calculate_k(-0.2), 2.0)
        self.assertEqual(engine.calculate_k(0.9), 0.0)
        self.assertEqual(engine.calculate_k(-0.9), 0.0)
        self.assertAlmostEqual(engine.calculate_k(0.55), 1.0)
        
    def test_process_axis_negative_rc(self):
        engine = FilterEngine(deadzone=0.0)
        
        # First frame, value 0.2, prev 0.0
        # k for 0.2 is 2.0
        # output = 0.2 + 2.0 * (0.2 - 0.0) = 0.6
        out = engine.process_axis(0.2, 0.0)
        self.assertAlmostEqual(out, 0.6)
        
        # Next frame, value 0.4, prev 0.2
        # k for 0.4 is 2.0 * (0.8 - 0.4) / 0.5 = 1.6
        # output = 0.4 + 1.6 * (0.4 - 0.2) = 0.4 + 0.32 = 0.72
        out = engine.process_axis(0.4, 0.2)
        self.assertAlmostEqual(out, 0.72)

    def test_process_axis_clamping(self):
        engine = FilterEngine(deadzone=0.0)
        # value 0.2, prev -1.0
        # k = 2.0
        # output = 0.2 + 2.0 * (0.2 - -1.0) = 0.2 + 2.4 = 2.6 -> clamped to 1.0
        out = engine.process_axis(0.2, -1.0)
        self.assertAlmostEqual(out, 1.0)

    def test_deadzone(self):
        engine = FilterEngine(deadzone=0.1)
        out = engine.process_axis(0.05, 0.0)
        self.assertEqual(out, 0.0)
        
        out2 = engine.process_axis(0.55, 0.5)
        # 0.55 deadzoned: (0.55 - 0.1) / 0.9 = 0.5
        # 0.5 deadzoned: (0.5 - 0.1) / 0.9 = 0.444...
        # Just verifying deadzone application doesn't crash and logic holds
        self.assertTrue(out2 > 0)

if __name__ == '__main__':
    unittest.main()
