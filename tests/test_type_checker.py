import unittest
from parser.potion_parser import Parser, tokenize
from codegen.potion_codegen import ErlangCodegen

class TestTypeChecker(unittest.TestCase):
    def test_type_error(self):
        tokens = tokenize("val x: float = 5")
        parser = Parser(tokens)
        ast = parser.parse()
        codegen = ErlangCodegen(ast)
        with self.assertRaises(Exception) as ctx:
            codegen.type_checking(ast.statements[0])
        self.assertIn("Tipo desconhecido (local) em 'x': float", str(ctx.exception))
