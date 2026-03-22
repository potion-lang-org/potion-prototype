import unittest
from parser.potion_parser import (
    Assignment,
    FunctionDef,
    ImportStatement,
    LiteralInt,
    LiteralNone,
    Parser,
    ValDeclaration,
    VarDeclaration,
    tokenize,
)

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

    def test_assignment_statement(self):
        tokens = tokenize("""
        fn main() {
            var total: int = 1
            total = total + 1
        }
        """)
        parser = Parser(tokens)
        ast = parser.parse()
        self.assertIsInstance(ast.statements[0].body[1], Assignment)
        self.assertEqual(ast.statements[0].body[1].name, "total")

    def test_function_param_type_annotation(self):
        tokens = tokenize("""
        fn greet(name: str, age: int) {
            return name
        }
        """)
        parser = Parser(tokens)
        ast = parser.parse()
        self.assertIsInstance(ast.statements[0], FunctionDef)
        self.assertEqual(ast.statements[0].params[0].name, "name")
        self.assertEqual(ast.statements[0].params[0].type_annotation, "str")
        self.assertEqual(ast.statements[0].params[1].name, "age")
        self.assertEqual(ast.statements[0].params[1].type_annotation, "int")

    def test_import_statement(self):
        tokens = tokenize("import helpers")
        parser = Parser(tokens)
        ast = parser.parse()
        self.assertIsInstance(ast.statements[0], ImportStatement)
        self.assertEqual(ast.statements[0].module_name, "helpers")
