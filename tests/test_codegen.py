import unittest
from parser.potion_parser import Parser, tokenize
from codegen.potion_codegen import ErlangCodegen

class TestCodegen(unittest.TestCase):
    def test_simple_function(self):
        code = """
        val base: int = 10
        fn somar() {
            val x = base + 1
            return x
        }
        """
        tokens = tokenize(code)
        ast = Parser(tokens).parse()
        codegen = ErlangCodegen(ast)
        erlang_code = codegen.generate()
        self.assertIn("-module(", erlang_code)
        self.assertIn("somar()", erlang_code)
