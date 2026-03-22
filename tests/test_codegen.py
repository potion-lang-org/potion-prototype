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
        self.assertIn("Current_0 = ?FALLBACK", erlang_code)

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

    def test_var_reassignment_codegen(self):
        code = """
        fn main() {
            var total: int = 1
            total = total + 2
            print(total)
        }
        """
        tokens = tokenize(code)
        ast = Parser(tokens).parse()
        codegen = ErlangCodegen(ast)
        erlang_code = codegen.generate()
        self.assertIn("Total_0 = 1", erlang_code)
        self.assertIn("Total_1 = (Total_0 + 2)", erlang_code)
        self.assertIn('io:format("~p~n", [Total_1])', erlang_code)

    def test_var_reassignment_inside_if_codegen(self):
        code = """
        fn main() {
            var total: int = 1
            if true {
                total = total + 2
            } else {
                total = total + 3
            }
            print(total)
        }
        """
        tokens = tokenize(code)
        ast = Parser(tokens).parse()
        codegen = ErlangCodegen(ast)
        erlang_code = codegen.generate()
        self.assertIn("Total_0 = 1", erlang_code)
        self.assertIn("Total_2 = case true of", erlang_code)
        self.assertIn("Total_1 = (Total_0 + 2)", erlang_code)
        self.assertIn("Total_1 = (Total_0 + 3)", erlang_code)
        self.assertIn('io:format("~p~n", [Total_2])', erlang_code)

    def test_var_reassignment_inside_match_codegen(self):
        code = """
        fn main() {
            var total: int = 1
            match {ok: 2} {
                {ok: value} => total = value
                _ => total = 0
            }
            print(total)
        }
        """
        tokens = tokenize(code)
        ast = Parser(tokens).parse()
        codegen = ErlangCodegen(ast)
        erlang_code = codegen.generate()
        self.assertIn("Total_2 = case #{ok => 2} of", erlang_code)
        self.assertIn("Total_1 = Value", erlang_code)
        self.assertIn("Total_1 = 0", erlang_code)
