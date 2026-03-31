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

    def test_typed_function_params_codegen(self):
        code = """
        fn greet(name: str, age: int) {
            val message = name + "!"
            print(message)
        }
        """
        tokens = tokenize(code)
        ast = Parser(tokens).parse()
        codegen = ErlangCodegen(ast)
        erlang_code = codegen.generate()
        self.assertIn("greet(Name, Age) ->", erlang_code)
        self.assertIn('Message = (Name ++ "!")', erlang_code)

    def test_imported_function_call_codegen(self):
        imported_ast = Parser(tokenize("""
        fn greet(name: str) {
            print(name)
        }
        """)).parse()
        external_functions = {
            ("greet", 1): {
                "module_name": "helpers",
                "params": imported_ast.statements[0].params,
            }
        }
        code = """
        import helpers
        fn main() {
            greet("Bruce")
        }
        """
        tokens = tokenize(code)
        ast = Parser(tokens).parse()
        codegen = ErlangCodegen(ast, external_functions=external_functions)
        erlang_code = codegen.generate()
        self.assertIn('helpers:greet("Bruce")', erlang_code)

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

    def test_receive_on_codegen(self):
        code = """
        fn worker() {
            receive {
                on hello(name, caller) {
                    print("Hello, " + name)
                    send(caller, {ok: "received"})
                }

                on any {
                    print("unexpected message")
                }
            }
        }
        """
        tokens = tokenize(code)
        ast = Parser(tokens).parse()
        codegen = ErlangCodegen(ast)
        erlang_code = codegen.generate()
        self.assertIn("receive", erlang_code)
        self.assertIn("#{hello := Name, reply_to := Caller} ->", erlang_code)
        self.assertIn('Caller ! #{ok => "received"}', erlang_code)
        self.assertIn('_ ->', erlang_code)

    def test_receive_on_with_guard_codegen(self):
        code = """
        fn worker() {
            receive {
                on data(value, caller) when value > 10 {
                    print(value)
                }

                on any {
                    print("ignored")
                }
            }
        }
        """
        tokens = tokenize(code)
        ast = Parser(tokens).parse()
        codegen = ErlangCodegen(ast)
        erlang_code = codegen.generate()
        self.assertIn("#{data := Value, reply_to := Caller} when (Value > 10) ->", erlang_code)
        self.assertIn('io:format("~p~n", [Value])', erlang_code)

    def test_receive_on_complex_payload_codegen(self):
        code = """
        fn worker() {
            receive {
                on data(payload, caller) {
                    print(payload.nome)
                    print(payload.idade)
                }
            }
        }
        """
        tokens = tokenize(code)
        ast = Parser(tokens).parse()
        codegen = ErlangCodegen(ast)
        erlang_code = codegen.generate()
        self.assertIn("#{data := Payload, reply_to := Caller} ->", erlang_code)
        self.assertIn("maps:get(nome, Payload)", erlang_code)
        self.assertIn("maps:get(idade, Payload)", erlang_code)

    def test_receive_rejects_too_many_bindings_for_current_convention(self):
        code = """
        fn worker() {
            receive {
                on data(value, caller, extra) {
                    print(value)
                }
            }
        }
        """
        tokens = tokenize(code)
        ast = Parser(tokens).parse()
        codegen = ErlangCodegen(ast)
        with self.assertRaises(Exception) as ctx:
            codegen.generate()
        self.assertIn("suporta no máximo 2 binding(s)", str(ctx.exception))

    def test_external_erlang_module_call_codegen(self):
        code = """
        import erlang httpc

        fn main() {
            val response = httpc.request("https://example.com")
        }
        """
        tokens = tokenize(code)
        ast = Parser(tokens).parse()
        codegen = ErlangCodegen(ast)
        erlang_code = codegen.generate()
        self.assertIn('Response = httpc:request("https://example.com")', erlang_code)

    def test_external_erlang_module_call_codegen_with_empty_list(self):
        code = """
        import erlang ets

        fn main() {
            val tid = ets.new("users", [])
        }
        """
        tokens = tokenize(code)
        ast = Parser(tokens).parse()
        codegen = ErlangCodegen(ast)
        erlang_code = codegen.generate()
        self.assertIn('Tid = ets:new("users", [])', erlang_code)
