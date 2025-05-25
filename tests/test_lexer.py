import unittest
from parser.potion_parser import tokenize

class TestLexer(unittest.TestCase):
    def test_val_declaration(self):
        code = "val x: int = 5"
        tokens = tokenize(code)
        self.assertEqual(tokens[0][0], "VAL")
        self.assertEqual(tokens[1][0], "ID")
        self.assertEqual(tokens[2][0], "COLON")
        self.assertEqual(tokens[3][0], "ID")
        self.assertEqual(tokens[4][0], "ASSIGN")
        self.assertEqual(tokens[5][0], "NUMBER")
