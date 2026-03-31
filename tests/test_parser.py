import unittest
from parser.potion_parser import (
    Assignment,
    ErlangImportStatement,
    ExternalModuleCall,
    FunctionDef,
    ImportStatement,
    LiteralInt,
    LiteralNone,
    Parser,
    ReceiveBlock,
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

    def test_import_erlang_statement(self):
        tokens = tokenize("import erlang httpc")
        parser = Parser(tokens)
        ast = parser.parse()
        self.assertIsInstance(ast.statements[0], ErlangImportStatement)
        self.assertEqual(ast.statements[0].module_name, "httpc")

    def test_external_module_call_parsing(self):
        tokens = tokenize("""
        import erlang httpc
        fn main() {
            val response = httpc.request("https://example.com")
        }
        """)
        parser = Parser(tokens)
        ast = parser.parse()
        self.assertIsInstance(ast.statements[1].body[0].value, ExternalModuleCall)
        self.assertEqual(ast.statements[1].body[0].value.module_name, "httpc")
        self.assertEqual(ast.statements[1].body[0].value.function_name, "request")

    def test_external_module_call_with_list_literal_parsing(self):
        tokens = tokenize("""
        import erlang ets
        fn main() {
            val tid = ets.new("users", [])
        }
        """)
        parser = Parser(tokens)
        ast = parser.parse()
        self.assertIsInstance(ast.statements[1].body[0].value, ExternalModuleCall)
        self.assertEqual(len(ast.statements[1].body[0].value.args), 2)

    def test_receive_on_clause_parsing(self):
        tokens = tokenize("""
        fn worker() {
            receive {
                on hello(name, caller) {
                    print(name)
                }

                on any {
                    print("unexpected")
                }
            }
        }
        """)
        parser = Parser(tokens)
        ast = parser.parse()
        receive_block = ast.statements[0].body[0]
        self.assertIsInstance(receive_block, ReceiveBlock)
        self.assertEqual(len(receive_block.clauses), 2)
        self.assertEqual(receive_block.clauses[0].tag, "hello")
        self.assertEqual(receive_block.clauses[0].bindings, ["name", "caller"])
        self.assertTrue(receive_block.clauses[1].is_any)

    def test_receive_on_clause_with_guard_parsing(self):
        tokens = tokenize("""
        fn worker() {
            receive {
                on data(value, caller) when value > 10 {
                    print(value)
                }
            }
        }
        """)
        parser = Parser(tokens)
        ast = parser.parse()
        clause = ast.statements[0].body[0].clauses[0]
        self.assertEqual(clause.tag, "data")
        self.assertEqual(clause.bindings, ["value", "caller"])
        self.assertIsNotNone(clause.guard)
