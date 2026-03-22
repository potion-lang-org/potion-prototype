from cli.parse_potion_file import parse_potion_file
from codegen.potion_codegen import ErlangCodegen
import sys
import os
import subprocess
import argparse
import re


def sanitize_module_name(source_name: str) -> str:
    module_name = re.sub(r"[^a-zA-Z0-9_]", "_", source_name).lower()
    if not module_name:
        return "potion_module"
    if not module_name[0].isalpha():
        module_name = f"potion_{module_name}"
    return module_name


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
    module_name = sanitize_module_name(source_module_name)

    try:
        ast = parse_potion_file(abs_path)

        if args.emit_ast:
            print("📦 AST:")
            print(ast)
            return

        codegen = ErlangCodegen(ast, module_name=module_name)
        erlang_code = codegen.generate()

        # Criar diretório target/ ou personalizado se não existir
        os.makedirs(args.outdir, exist_ok=True)

        # Salvar .erl
        output_path = os.path.join(args.outdir, f"{module_name}.erl")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(erlang_code)

        print(f"\n✅ Erlang file generated: {output_path}")
        if module_name != source_module_name:
            print(f"ℹ️ Sanitized Erlang module name: {module_name}")

        if not args.no_beam:
            # Compilar com erlc
            print("🔧 Compiling with erlc...")
            result = subprocess.run(["erlc", "-o", args.outdir, output_path], capture_output=True, text=True)

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
