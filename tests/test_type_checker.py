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

    def test_none_type_is_supported(self):
        tokens = tokenize("var current: none = none")
        parser = Parser(tokens)
        ast = parser.parse()
        codegen = ErlangCodegen(ast)
        codegen.type_checking(ast.statements[0])
        self.assertEqual(codegen.type_env["Current"], "none")

    def test_function_param_comparison_can_type_check(self):
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
        self.assertIn("Ok = (A >= B)", erlang_code)

    def test_to_string_infers_string_result(self):
        code = """
        fn show(age) {
            val rendered: str = to_string(age)
            return rendered
        }
        """
        tokens = tokenize(code)
        ast = Parser(tokens).parse()
        codegen = ErlangCodegen(ast)
        erlang_code = codegen.generate()
        self.assertIn('Rendered = potion_to_string_builtin(Age)', erlang_code)
