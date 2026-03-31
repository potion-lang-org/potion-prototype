import unittest

from parser.potion_parser import Parser, tokenize
from semantic.potion_semantic import SemanticAnalyzer


class TestSemanticAnalyzer(unittest.TestCase):
    def test_infer_basic_types(self):
        analyzer = SemanticAnalyzer()
        self.assertEqual(analyzer.infer_type(1), "int")
        self.assertEqual(analyzer.infer_type("hello"), "str")
        self.assertEqual(analyzer.infer_type(True), "bool")
        self.assertEqual(analyzer.infer_type(None), "none")

    def test_to_string_evaluation(self):
        ast = Parser(tokenize("to_string(42)")).parse()
        analyzer = SemanticAnalyzer()
        value = analyzer.evaluate_expression(ast.statements[0])
        self.assertEqual(value, "42")

    def test_type_checking_records_annotation(self):
        ast = Parser(tokenize("val total: int = 5")).parse()
        analyzer = SemanticAnalyzer()
        analyzer.type_checking(ast.statements[0])
        self.assertEqual(analyzer.type_env["Total"], "int")

    def test_plus_rejects_mixed_int_and_string(self):
        ast = Parser(tokenize('1 + "a"')).parse()
        analyzer = SemanticAnalyzer()
        with self.assertRaises(Exception) as ctx:
            analyzer.evaluate_expression(ast.statements[0])
        self.assertIn("operador '+' recebeu tipos incompatíveis", str(ctx.exception))
        self.assertIn("Use to_string(...)", str(ctx.exception))

    def test_function_call_rejects_wrong_typed_argument(self):
        code = """
        fn greet(name: str) {
            return name
        }

        greet(1)
        """
        ast = Parser(tokenize(code)).parse()
        analyzer = SemanticAnalyzer()
        analyzer.functions["greet"] = {
            "params": ast.statements[0].params,
            "body": ast.statements[0].body,
        }
        with self.assertRaises(Exception) as ctx:
            analyzer.evaluate_expression(ast.statements[1])
        self.assertIn("Erro de tipo em chamada de função 'greet'", str(ctx.exception))

    def test_receive_guard_can_use_clause_bindings(self):
        code = """
        fn worker() {
            receive {
                on data(value, caller) when value > 10 {
                    print(value)
                    send(caller, {ok: value})
                }
            }
        }
        """
        ast = Parser(tokenize(code)).parse()
        analyzer = SemanticAnalyzer()
        value = analyzer.evaluate_expression(ast.statements[0].body[0])
        self.assertEqual(analyzer.infer_type(value), "dynamic")

    def test_receive_guard_rejects_undeclared_identifier(self):
        code = """
        fn worker() {
            receive {
                on data(value, caller) when missing > 10 {
                    print(value)
                }
            }
        }
        """
        ast = Parser(tokenize(code)).parse()
        analyzer = SemanticAnalyzer()
        with self.assertRaises(Exception) as ctx:
            analyzer.evaluate_expression(ast.statements[0].body[0])
        self.assertIn("Variável 'missing' não declarada", str(ctx.exception))

    def test_external_erlang_module_call_requires_import(self):
        code = """
        fn main() {
            val response = httpc.request("https://example.com")
        }
        """
        ast = Parser(tokenize(code)).parse()
        analyzer = SemanticAnalyzer()
        with self.assertRaises(Exception) as ctx:
            analyzer.evaluate_statement(ast.statements[0].body[0])
        self.assertIn("Módulo Erlang 'httpc' não foi importado", str(ctx.exception))

    def test_external_erlang_module_call_accepts_imported_module(self):
        code = """
        import erlang httpc

        fn main() {
            val response = httpc.request("https://example.com")
        }
        """
        ast = Parser(tokenize(code)).parse()
        analyzer = SemanticAnalyzer()
        analyzer.evaluate_statement(ast.statements[0])
        value = analyzer.evaluate_statement(ast.statements[1].body[0])
        self.assertEqual(analyzer.infer_type(value), "dynamic")
