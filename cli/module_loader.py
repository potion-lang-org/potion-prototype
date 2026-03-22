import os
import re
from dataclasses import dataclass

from parser.potion_parser import FunctionDef, ImportStatement

from cli.parse_potion_file import parse_potion_file


def sanitize_module_name(source_name: str) -> str:
    module_name = re.sub(r"[^a-zA-Z0-9_]", "_", source_name).lower()
    if not module_name:
        return "potion_module"
    if not module_name[0].isalpha():
        module_name = f"potion_{module_name}"
    return module_name


@dataclass
class LoadedModule:
    source_name: str
    module_name: str
    file_path: str
    ast: object
    imports: list


def collect_module_imports(ast):
    return [stmt.module_name for stmt in ast.statements if isinstance(stmt, ImportStatement)]


def collect_module_functions(ast):
    return [stmt for stmt in ast.statements if isinstance(stmt, FunctionDef)]


def load_module_graph(entry_path):
    modules = {}
    loading = set()

    def load(file_path):
        abs_path = os.path.abspath(file_path)
        if abs_path in modules:
            return modules[abs_path]
        if abs_path in loading:
            raise Exception(f"Import cíclico detectado: {abs_path}")
        if not os.path.isfile(abs_path):
            raise Exception(f"Módulo não encontrado: {file_path}")

        loading.add(abs_path)
        source_name = os.path.splitext(os.path.basename(abs_path))[0]
        ast = parse_potion_file(abs_path)
        imports = collect_module_imports(ast)
        loaded_module = LoadedModule(
            source_name=source_name,
            module_name=sanitize_module_name(source_name),
            file_path=abs_path,
            ast=ast,
            imports=imports,
        )
        modules[abs_path] = loaded_module

        base_dir = os.path.dirname(abs_path)
        for imported_name in imports:
            imported_path = os.path.join(base_dir, f"{imported_name}.potion")
            load(imported_path)

        loading.remove(abs_path)
        return loaded_module

    entry_module = load(entry_path)
    ordered_modules = list(modules.values())
    return entry_module, ordered_modules


def build_external_function_map(module, modules_by_source_name):
    external_functions = {}
    for imported_name in module.imports:
        if imported_name not in modules_by_source_name:
            raise Exception(f"Módulo importado não encontrado: {imported_name}")
        imported_module = modules_by_source_name[imported_name]
        for function_def in collect_module_functions(imported_module.ast):
            key = (function_def.name, len(function_def.params))
            if key in external_functions:
                raise Exception(
                    f"Conflito de import: função '{function_def.name}/{len(function_def.params)}' "
                    f"foi importada de mais de um módulo."
                )
            external_functions[key] = {
                "module_name": imported_module.module_name,
                "params": function_def.params,
            }
    return external_functions
