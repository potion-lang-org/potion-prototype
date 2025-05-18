import unittest
import subprocess
import os
from potion_parser import Parser, tokenize
from potion_codegen import ErlangCodegen

class TestIntegration(unittest.TestCase):
    def test_full_pipeline(self):
        code = """
        val v: int = 5
        fn get_v() {
            return v
        }
        """
        tokens = tokenize(code)
        ast = Parser(tokens).parse()
        codegen = ErlangCodegen(ast)
        output = codegen.generate()

        path_file = "./tests/test"
        with open(f"{path_file}.erl", "w") as f:
            f.write(output)
        result = subprocess.run(["erlc", "teste.erl"], capture_output=True)
        self.assertEqual(result.returncode, 1, msg=result.stderr.decode())
        os.remove(f"{path_file}.erl")
        #os.remove(f"{path_file}.beam")
