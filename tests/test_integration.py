import unittest
import subprocess
import shutil
import tempfile
from pathlib import Path
from parser.potion_parser import Parser, tokenize
from codegen.potion_codegen import ErlangCodegen

class TestIntegration(unittest.TestCase):
    def test_full_pipeline(self):
        code = """
        val base: int = 10

        fn worker() {
            receive {
                on compute(value, caller) {
                    val doubled = value * 2
                    send(caller, {result: doubled + base})
                }

                on any {
                    print("unexpected")
                }
            }
        }

        fn main() {
            val pid: pid = sp worker()
            send(pid, {compute: 5, reply_to: self()})

            receive {
                on result(total) {
                    print("Result: " + to_string(total))
                }

                on any {
                    print("No response")
                }
            }
        }
        """
        if shutil.which("erlc") is None:
            self.skipTest("erlc não está disponível no ambiente")

        tokens = tokenize(code)
        ast = Parser(tokens).parse()
        module_name = "integration_receive"
        codegen = ErlangCodegen(ast, module_name=module_name)
        output = codegen.generate()

        with tempfile.TemporaryDirectory() as tmpdir:
            erl_path = Path(tmpdir) / f"{module_name}.erl"
            erl_path.write_text(output)
            result = subprocess.run(["erlc", erl_path.name], capture_output=True, text=True, cwd=tmpdir)
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertTrue((Path(tmpdir) / f"{module_name}.beam").exists())

    def test_pattern_matching_compiles_and_runs(self):
        if shutil.which("erlc") is None or shutil.which("erl") is None:
            self.skipTest("Erlang toolchain não está disponível no ambiente")

        code = """
        fn main() {
            val response = {:ok, "Potion"}
            val message = match response {
                {:ok, value} => value
                {:error, reason} => reason
            }
            val first = match ["head", "tail"] {
                [head, tail] => head
                _ => "empty"
            }
            print(message)
            print(first)
        }
        """
        module_name = "integration_pattern_matching"
        output = ErlangCodegen(
            Parser(tokenize(code)).parse(), module_name=module_name
        ).generate()

        with tempfile.TemporaryDirectory() as tmpdir:
            erl_path = Path(tmpdir) / f"{module_name}.erl"
            erl_path.write_text(output)
            compile_result = subprocess.run(
                ["erlc", erl_path.name], capture_output=True, text=True, cwd=tmpdir
            )
            self.assertEqual(compile_result.returncode, 0, msg=compile_result.stderr)

            run_result = subprocess.run(
                [
                    "erl",
                    "-noshell",
                    "-pa",
                    tmpdir,
                    "-eval",
                    f"{module_name}:main(), halt().",
                ],
                capture_output=True,
                text=True,
                cwd=tmpdir,
            )
            self.assertEqual(run_result.returncode, 0, msg=run_result.stderr)
            self.assertEqual(run_result.stdout, '"Potion"\n"head"\n')
