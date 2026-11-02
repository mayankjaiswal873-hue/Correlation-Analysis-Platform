
import unittest

from services.data_generator import generate_data
from services.analysis import analyze_data
from services.insights import explain_correlation, generate_insights


class CorrelationAnalysisTests(unittest.TestCase):

    def test_generated_data_has_requested_rows(self):
        data = generate_data(50, seed=42)
        self.assertEqual(len(data), 50)

    def test_generated_data_has_expected_columns(self):
        data = generate_data(30, seed=42)
        self.assertIn("Study_Hours", data.columns)
        self.assertIn("Marks", data.columns)

    def test_correlation_matrix_is_square(self):
        data = generate_data(40, seed=42)
        result = analyze_data(data)
        matrix = result["correlation"]
        self.assertEqual(matrix.shape[0], matrix.shape[1])

    def test_correlation_values_are_in_valid_range(self):
        data = generate_data(40, seed=42)
        matrix = analyze_data(data)["correlation"]
        values = matrix.to_numpy()
        self.assertTrue((values >= -1).all())
        self.assertTrue((values <= 1).all())

    def test_one_column_is_rejected(self):
        import pandas as pd
        with self.assertRaises(ValueError):
            analyze_data(pd.DataFrame({"Marks": [50, 60, 70]}))

    def test_invalid_row_count_is_rejected(self):
        with self.assertRaises(ValueError):
            generate_data(10)

    def test_insight_mentions_causation_warning(self):
        text = explain_correlation(0.85, "Study_Hours", "Marks")
        self.assertIn("does not prove causation", text)

    def test_insights_are_generated(self):
        data = generate_data(40, seed=42)
        matrix = analyze_data(data)["correlation"]
        insights = generate_insights(matrix)
        self.assertGreater(len(insights), 0)


if __name__ == "__main__":
    unittest.main()
