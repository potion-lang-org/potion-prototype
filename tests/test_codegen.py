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

    def test_var_and_none_codegen(self):
        code = """
        var fallback: none = none
        fn load() {
            var current: none = fallback
            return current
        }
        """
        tokens = tokenize(code)
        ast = Parser(tokens).parse()
        codegen = ErlangCodegen(ast)
        erlang_code = codegen.generate()
        self.assertIn("-define(FALLBACK, undefined).", erlang_code)
        self.assertIn("Current = ?FALLBACK", erlang_code)

    def test_comparison_codegen_and_type_checking(self):
        code = """
        fn compare(a, b) {
            val ok: bool = a >= b
            return ok
        }
        """
        tokens = tokenize(code)
        ast = Parser(tokens).parse()
        codegen = ErlangCodegen(ast)
        erlang_code = codegen.generate()
        self.assertIn("(A >= B)", erlang_code)

    def test_to_string_builtin_codegen(self):
        code = """
        fn show(age) {
            print("Age: " + to_string(age))
        }
        """
        tokens = tokenize(code)
        ast = Parser(tokens).parse()
        codegen = ErlangCodegen(ast)
        erlang_code = codegen.generate()
        self.assertIn('potion_to_string_builtin(Age)', erlang_code)
        self.assertIn('potion_to_string_builtin(Value) when is_integer(Value) ->', erlang_code)
