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

    def test_atom_declaration_and_print_codegen(self):
        code = """
        val status: atom = :ok

        fn main() {
            print(:ok)
            val response = {status: :not_found}
            print(response)
        }
        """
        tokens = tokenize(code)
        ast = Parser(tokens).parse()
        codegen = ErlangCodegen(ast)
        erlang_code = codegen.generate()
        self.assertIn("-define(STATUS, ok).", erlang_code)
        self.assertIn('io:format("~p~n", [ok])', erlang_code)
        self.assertIn("Response = #{status => not_found}", erlang_code)
        self.assertNotIn('"ok"', erlang_code)

    def test_atom_return_and_comparison_codegen(self):
        code = """
        fn get_status() {
            return :ok
        }

        fn main() {
            val status: atom = get_status()
            if status == :ok {
                print("status ok")
            } else {
                print("status error")
            }
            print(:not_found)
        }
        """
        tokens = tokenize(code)
        ast = Parser(tokens).parse()
        codegen = ErlangCodegen(ast)
        erlang_code = codegen.generate()
        self.assertIn("get_status() ->\n    ok.", erlang_code)
        self.assertIn("Status = get_status()", erlang_code)
        self.assertIn("case (Status == ok) of", erlang_code)
        self.assertIn('io:format("~p~n", [not_found])', erlang_code)
        self.assertNotIn('"not_found"', erlang_code)

    def test_atom_equality_semantics(self):
        equal_code = """
        fn main() {
            val same: bool = :ok == :ok
            print(same)
        }
        """
        different_code = """
        fn main() {
            val same: bool = :ok == :error
            print(same)
        }
        """

        equal_erlang = ErlangCodegen(Parser(tokenize(equal_code)).parse()).generate()
        different_erlang = ErlangCodegen(Parser(tokenize(different_code)).parse()).generate()

        self.assertIn("Same = (ok == ok)", equal_erlang)
        self.assertIn("Same = (ok == error)", different_erlang)

    def test_external_erlang_module_call_codegen_with_atom_argument(self):
        code = """
        import erlang application

        fn main() {
            val result = application.ensure_all_started(:ssl)
        }
        """
        tokens = tokenize(code)
        ast = Parser(tokens).parse()
        codegen = ErlangCodegen(ast)
        erlang_code = codegen.generate()
        self.assertIn("Result = application:ensure_all_started(ssl)", erlang_code)

    def test_atom_codegen_quotes_atoms_that_are_not_bare_erlang_atoms(self):
        code = """
        fn main() {
            print(:_private)
            print(:receive)
        }
        """
        tokens = tokenize(code)
        ast = Parser(tokens).parse()
        codegen = ErlangCodegen(ast)
        erlang_code = codegen.generate()
        self.assertIn("io:format(\"~p~n\", ['_private'])", erlang_code)
        self.assertIn("io:format(\"~p~n\", ['receive'])", erlang_code)

    def test_tuple_literal_codegen(self):
        code = """
        val result: tuple = {:ok, 123}

        fn main() {
            print({:ok, 42})
        }
        """
        tokens = tokenize(code)
        ast = Parser(tokens).parse()
        codegen = ErlangCodegen(ast)
        erlang_code = codegen.generate()
        self.assertIn("-define(RESULT, {ok, 123}).", erlang_code)
        self.assertIn('io:format("~p~n", [{ok, 42}])', erlang_code)

    def test_nested_tuple_literal_codegen(self):
        code = """
        fn main() {
            val nested = {:ok, {:user, 10}}
            print(nested)
        }
        """
        tokens = tokenize(code)
        ast = Parser(tokens).parse()
        codegen = ErlangCodegen(ast)
        erlang_code = codegen.generate()
        self.assertIn("Nested = {ok, {user, 10}}", erlang_code)

    def test_tuple_return_argument_variable_and_call_codegen(self):
        code = """
        fn get_value() {
            return 42
        }

        fn get_result() {
            return {:ok, get_value()}
        }

        fn wrap(result: tuple) {
            return {:reply, result}
        }

        fn main() {
            val result: tuple = get_result()
            val wrapped = wrap(result)
            val with_var = {:ok, result}
            print(wrapped)
            print(with_var)
        }
        """
        tokens = tokenize(code)
        ast = Parser(tokens).parse()
        codegen = ErlangCodegen(ast)
        erlang_code = codegen.generate()
        self.assertIn("get_result() ->\n    {ok, get_value()}.", erlang_code)
        self.assertIn("wrap(Result) ->\n    {reply, Result}.", erlang_code)
        self.assertIn("Wrapped = wrap(Result)", erlang_code)
        self.assertIn("With_var = {ok, Result}", erlang_code)

    def test_tuple_equality_codegen(self):
        code = """
        fn main() {
            val same: bool = {:ok, 1} == {:ok, 1}
            print(same)
        }
        """
        tokens = tokenize(code)
        ast = Parser(tokens).parse()
        codegen = ErlangCodegen(ast)
        erlang_code = codegen.generate()
        self.assertIn("Same = ({ok, 1} == {ok, 1})", erlang_code)

    def test_match_codegen_supports_literal_binding_tuple_and_list_patterns(self):
        code = """
        fn main() {
            val integer = match 1 {
                0 => "zero"
                1 => "one"
                _ => "many"
            }
            val string = match "hello" {
                "hello" => true
                _ => false
            }
            val boolean = match true {
                true => :yes
                false => :no
            }
            val atom = match :ok {
                :ok => "success"
                _ => "failure"
            }
            val tuple_value = match {:ok, "Potion"} {
                {:ok, value} => value
                {:error, reason} => reason
            }
            val list_value = match ["head", "tail"] {
                [head, tail] => head
                _ => "empty"
            }
            val map_value = match {status: :ok, payload: "map"} {
                {status: :ok, payload: map_payload} => map_payload
                _ => "missing"
            }
            match integer {
                name => {
                    print(name)
                }
            }
        }
        """
        erlang_code = ErlangCodegen(Parser(tokenize(code)).parse()).generate()

        self.assertIn("Integer = case 1 of", erlang_code)
        self.assertIn('0 ->\n        "zero";', erlang_code)
        self.assertIn('"hello" ->\n        true;', erlang_code)
        self.assertIn("true ->\n        yes;", erlang_code)
        self.assertIn("Atom = case ok of", erlang_code)
        self.assertIn("ok ->\n        \"success\";", erlang_code)
        self.assertIn("{ok, Value} ->", erlang_code)
        self.assertIn("[Head, Tail] ->", erlang_code)
        self.assertIn("#{status := ok, payload := Map_payload} ->", erlang_code)
        self.assertIn("Name ->", erlang_code)
        self.assertIn('io:format("~p~n", [Name])', erlang_code)

    def test_match_binding_shadows_outer_local_without_leaking_erlang_binding(self):
        code = """
        fn main() {
            val value = "outer"
            val result = match {:ok, "inner"} {
                {:ok, value} => value
            }
            print(value)
            print(result)
        }
        """
        erlang_code = ErlangCodegen(Parser(tokenize(code)).parse()).generate()

        self.assertIn("{ok, Value_Match1} ->", erlang_code)
        self.assertIn("Result = case", erlang_code)
        self.assertIn('io:format("~p~n", [Value])', erlang_code)

    def test_match_branches_have_independent_bindings_with_the_same_name(self):
        code = """
        fn unwrap(result) {
            return match result {
                {:ok, payload} => payload
                {:error, payload} => payload
            }
        }
        """
        erlang_code = ErlangCodegen(Parser(tokenize(code)).parse()).generate()

        self.assertIn("{ok, Payload} ->", erlang_code)
        self.assertIn("{error, Payload_Match1} ->", erlang_code)
