# exemplo.py

from potion_parser import Parser, tokenize
from potion_codegen import ErlangCodegen

source_code = """
val valor = 0

val valor_boleano_true = true

val valor_boleano_false = false

fn verificar() {
    if valor > 0 {
        print("Maior que zero")
    } else {
        print("Menor ou igual a zero")
    }

    if valor_boleano_true == true {
        print("valor_boleano_true igual a true")
    }

    if valor_boleano_false == false {
        print("valor_boleano_false igual a false")
    }
}

val x = 5

fn calcular() {
    val y = x + 3
    return y * 2
}

fn vazio() {
}

fn apenas_retorno() {
    return 42
}

val base: int = 10

fn somar_valores() {
    val a: int = base + 5
    val b = a * 2
    return b + 3
}

fn printar() {
    print("rodando com duas funções")
}
"""

# Lexer
tokens = tokenize(source_code)

# Parser
parser = Parser(tokens)
ast = parser.parse()

# Codegen
codegen = ErlangCodegen(ast, module_name="verificar")
erlang_code = codegen.generate()

# Output
print(erlang_code)

# Opcional: Salvar em arquivo
with open("verificar.erl", "w") as f:
    f.write(erlang_code)
