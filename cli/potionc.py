from cli.module_loader import build_external_function_map, load_module_graph, sanitize_module_name
from codegen.potion_codegen import ErlangCodegen
import sys
import os
import subprocess
import argparse


def main():
    parser = argparse.ArgumentParser(
        description="Potion Compiler - Compile .potion files to Erlang"
    )
    parser.add_argument("source", help="Path to the .potion file")
    parser.add_argument("--emit-ast", action="store_true", help="Print AST instead of compiling")
    parser.add_argument("--no-beam", action="store_true", help="Skip compilation to .beam")
    parser.add_argument("--run", action="store_true", help="Run the compiled module (calls main/0)")
    parser.add_argument("--outdir", default="target", help="Output directory [default: target/]")

    args = parser.parse_args()
    input_path = args.source
    abs_path = os.path.abspath(input_path)

    if not os.path.isfile(abs_path):
        print(f"Error: file '{input_path}' not found.")
        sys.exit(1)

    if not abs_path.endswith(".potion"):
        print("Error: the file must have the extension .potion")
        sys.exit(1)

    filename = os.path.basename(abs_path)
    source_module_name = os.path.splitext(filename)[0]

    try:
        entry_module, loaded_modules = load_module_graph(abs_path)
        module_name = entry_module.module_name

        if args.emit_ast:
            print("📦 AST:")
            print(entry_module.ast)
            return

        modules_by_source_name = {module.source_name: module for module in loaded_modules}

        # Criar diretório target/ ou personalizado se não existir
        os.makedirs(args.outdir, exist_ok=True)

        generated_outputs = []
        for loaded_module in loaded_modules:
            external_functions = build_external_function_map(loaded_module, modules_by_source_name)
            codegen = ErlangCodegen(
                loaded_module.ast,
                module_name=loaded_module.module_name,
                external_functions=external_functions,
            )
            erlang_code = codegen.generate()

            output_path = os.path.join(args.outdir, f"{loaded_module.module_name}.erl")
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(erlang_code)
            generated_outputs.append(output_path)

            print(f"\n✅ Erlang file generated: {output_path}")
            if loaded_module is entry_module and loaded_module.module_name != source_module_name:
                print(f"ℹ️ Sanitized Erlang module name: {loaded_module.module_name}")

        if not args.no_beam:
            print("🔧 Compiling with erlc...")
            result = subprocess.run(["erlc", "-o", args.outdir, *generated_outputs], capture_output=True, text=True)

            if result.returncode != 0:
                print("❌ erlc compilation failed:")
                print(result.stderr)
                sys.exit(1)

            beam_path = os.path.join(args.outdir, f"{module_name}.beam")
            print(f"✅ Compilation successful! BEAM file: {beam_path}")

            if args.run:
                print("🚀 Running main/0...\n")
                os.system(f'erl -noshell -pa {args.outdir} -eval "{module_name}:main(), halt()."')

    except Exception as e:
        print(f"Error compiling file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
