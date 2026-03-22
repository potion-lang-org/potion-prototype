import os
import tempfile
import unittest

from cli.module_loader import build_external_function_map, load_module_graph


class TestModuleLoader(unittest.TestCase):
    def test_load_module_graph_and_external_map(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            main_path = os.path.join(tmpdir, "main.potion")
            helper_path = os.path.join(tmpdir, "helpers.potion")

            with open(helper_path, "w", encoding="utf-8") as f:
                f.write(
                    """
                    fn greet(name: str) {
                        print(name)
                    }
                    """
                )

            with open(main_path, "w", encoding="utf-8") as f:
                f.write(
                    """
                    import helpers
                    fn main() {
                        greet("Bruce")
                    }
                    """
                )

            entry_module, loaded_modules = load_module_graph(main_path)
            self.assertEqual(entry_module.source_name, "main")
            self.assertEqual(len(loaded_modules), 2)

            modules_by_source_name = {module.source_name: module for module in loaded_modules}
            external_map = build_external_function_map(entry_module, modules_by_source_name)
            self.assertIn(("greet", 1), external_map)
            self.assertEqual(external_map[("greet", 1)]["module_name"], "helpers")
