import unittest
from parser.potion_parser import Parser, ValDeclaration, VarDeclaration, LiteralInt, LiteralNone, tokenize

class TestParser(unittest.TestCase):
    def test_simple_val(self):
        tokens = tokenize("val x: int = 5")
        parser = Parser(tokens)
        ast = parser.parse()
        self.assertIsInstance(ast.statements[0], ValDeclaration)
        self.assertEqual(ast.statements[0].name, "x")
        self.assertIsInstance(ast.statements[0].value, LiteralInt)
        self.assertEqual(ast.statements[0].value.value, 5)

    def test_var_declaration_with_none(self):
        tokens = tokenize("var current: none = none")
        parser = Parser(tokens)
        ast = parser.parse()
        self.assertIsInstance(ast.statements[0], VarDeclaration)
        self.assertEqual(ast.statements[0].name, "current")
        self.assertEqual(ast.statements[0].type_annotation, "none")
        self.assertIsInstance(ast.statements[0].value, LiteralNone)
