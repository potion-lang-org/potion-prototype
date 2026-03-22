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

    def test_mixed_string_and_int_addition_raises(self):
        code = """
        fn main() {
            val message = "Age: " + 42
            print(message)
        }
        """
        tokens = tokenize(code)
        ast = Parser(tokens).parse()
        codegen = ErlangCodegen(ast)
        with self.assertRaises(Exception) as ctx:
            codegen.generate()
        self.assertIn("operador '+' recebeu tipos incompatíveis", str(ctx.exception))
        self.assertIn("Use to_string(...)", str(ctx.exception))

    def test_explicit_to_string_allows_textual_concat(self):
        code = """
        fn main() {
            val message = "Age: " + to_string(42)
            print(message)
        }
        """
        tokens = tokenize(code)
        ast = Parser(tokens).parse()
        codegen = ErlangCodegen(ast)
        erlang_code = codegen.generate()
        self.assertIn('Message = ("Age: " ++ potion_to_string_builtin(42))', erlang_code)

    def test_reassignment_requires_var(self):
        code = """
        fn main() {
            val total: int = 1
            total = 2
        }
        """
        tokens = tokenize(code)
        ast = Parser(tokens).parse()
        codegen = ErlangCodegen(ast)
        with self.assertRaises(Exception) as ctx:
            codegen.generate()
        self.assertIn("não foi declarada com var", str(ctx.exception))

    def test_reassignment_preserves_declared_type(self):
        code = """
        fn main() {
            var total: int = 1
            total = 2
            print(total)
        }
        """
        tokens = tokenize(code)
        ast = Parser(tokens).parse()
        codegen = ErlangCodegen(ast)
        erlang_code = codegen.generate()
        self.assertIn("Total_1 = 2", erlang_code)

    def test_reassignment_inside_if_preserves_type(self):
        code = """
        fn main() {
            var total: int = 1
            if true {
                total = 2
            } else {
                total = 3
            }
            print(total)
        }
        """
        tokens = tokenize(code)
        ast = Parser(tokens).parse()
        codegen = ErlangCodegen(ast)
        erlang_code = codegen.generate()
        self.assertIn("Total_2 = case true of", erlang_code)

    def test_reassignment_to_wrong_type_raises(self):
        code = """
        fn main() {
            var total: int = 1
            total = "wrong"
        }
        """
        tokens = tokenize(code)
        ast = Parser(tokens).parse()
        codegen = ErlangCodegen(ast)
        with self.assertRaises(Exception) as ctx:
            codegen.generate()
        self.assertIn("Erro de tipo (local) em reatribuição de 'total'", str(ctx.exception))
