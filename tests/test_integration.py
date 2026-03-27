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
