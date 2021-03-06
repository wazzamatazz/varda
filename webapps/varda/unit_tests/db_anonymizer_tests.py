import unittest
from anonymizer.python.generate_anonymized_data import get_syntymaaika, get_sukupuoli


class DbAnonymizerTests(unittest.TestCase):
    def test_get_syntymaaika_century_20(self):
        hetu = '010397-1232'
        date = get_syntymaaika(hetu)
        self.assertEqual('1997-03-01', date)

    def test_get_syntymaaika_century_21(self):
        hetu = '050115A459P'
        date = get_syntymaaika(hetu)
        self.assertEqual('2015-01-05', date)

    def test_get_sukupuoli_man(self):
        hetu = '021115A7164'
        gender = get_sukupuoli(hetu)
        self.assertEqual('1', gender)

    def test_get_sukupuoli_woman(self):
        hetu = '130816-9930'
        gender = get_sukupuoli(hetu)
        self.assertEqual('2', gender)
