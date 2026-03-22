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
