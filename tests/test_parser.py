import unittest
from potion_parser import Parser, ValDeclaration, LiteralInt, tokenize

class TestParser(unittest.TestCase):
    def test_simple_val(self):
        tokens = tokenize("val x: int = 5")
        parser = Parser(tokens)
        ast = parser.parse()
        self.assertIsInstance(ast.statements[0], ValDeclaration)
        self.assertEqual(ast.statements[0].name, "x")
        self.assertIsInstance(ast.statements[0].value, LiteralInt)
        self.assertEqual(ast.statements[0].value.value, 5)
