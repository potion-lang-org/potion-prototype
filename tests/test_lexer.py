import unittest
from parser.potion_parser import tokenize

class TestLexer(unittest.TestCase):
    def test_val_declaration(self):
        code = "val x: int = 5"
        tokens = tokenize(code)
        self.assertEqual(tokens[0][0], "VAL")
        self.assertEqual(tokens[1][0], "ID")
        self.assertEqual(tokens[2][0], "COLON")
        self.assertEqual(tokens[3][0], "ID")
        self.assertEqual(tokens[4][0], "ASSIGN")
        self.assertEqual(tokens[5][0], "NUMBER")

    def test_var_and_none_tokens(self):
        tokens = tokenize("var maybe = none")
        self.assertEqual(tokens[0][0], "VAR")
        self.assertEqual(tokens[1][0], "ID")
        self.assertEqual(tokens[2][0], "ASSIGN")
        self.assertEqual(tokens[3][0], "NONE")

    def test_import_token(self):
        tokens = tokenize("import helpers")
        self.assertEqual(tokens[0], ("IMPORT", "import"))
        self.assertEqual(tokens[1], ("ID", "helpers"))

    def test_import_erlang_tokens(self):
        tokens = tokenize("import erlang httpc")
        self.assertEqual(tokens[0], ("IMPORT", "import"))
        self.assertEqual(tokens[1], ("ERLANG", "erlang"))
        self.assertEqual(tokens[2], ("ID", "httpc"))

    def test_list_literal_tokens(self):
        tokens = tokenize("[]")
        self.assertEqual(tokens[0][0], "LBRACKET")
        self.assertEqual(tokens[1][0], "RBRACKET")

    def test_receive_clause_tokens(self):
        tokens = tokenize("receive { on data(value, caller) when value > 10 { print(value) } on any { print(\"ignored\") } }")
        token_types = [kind for kind, _ in tokens]
        self.assertIn("RECEIVE", token_types)
        self.assertIn("ON", token_types)
        self.assertIn("WHEN", token_types)
        self.assertIn("ANY", token_types)

    def test_atom_literal_tokens(self):
        tokens = tokenize(":ok :error :not_found :http_404")
        self.assertEqual(tokens, [
            ("ATOM", ":ok"),
            ("ATOM", ":error"),
            ("ATOM", ":not_found"),
            ("ATOM", ":http_404"),
        ])

    def test_invalid_atom_literals_raise(self):
        for code in [":123", ":Invalid", ":hello-world"]:
            with self.subTest(code=code):
                with self.assertRaises(RuntimeError):
                    tokenize(code)

    def test_tuple_literal_reuses_brace_and_comma_tokens(self):
        tokens = tokenize("{:ok, 123}")
        self.assertEqual([kind for kind, _ in tokens], [
            "LBRACE",
            "ATOM",
            "COMMA",
            "NUMBER",
            "RBRACE",
        ])

    def test_match_arrow_token_is_fat_arrow_only(self):
        tokens = tokenize('match value { 0 => "zero" _ => "other" }')
        arrows = [token for token in tokens if token[0] == "ARROW"]
        self.assertEqual(arrows, [("ARROW", "=>"), ("ARROW", "=>")])

        thin_arrow_tokens = tokenize('match value { 0 -> "zero" }')
        self.assertNotIn("ARROW", [kind for kind, _ in thin_arrow_tokens])
