# Potion Language — Design Document

## 📖 Visão Geral

**Potion** é uma linguagem minimalista inspirada em Python, Erlang e Rust, criada para aprendizado, experimentação e geração de código Erlang a partir de uma sintaxe simples e expressiva.  
Seu foco está em facilitar a escrita de lógica de negócios clara e segura, gerando código eficiente para ambientes concorrentes como BEAM/Erlang VM.

---

## ✨ Objetivos

- Sintaxe enxuta, próxima de linguagens modernas (ex.: Python, Rust).
- Suporte a variáveis imutáveis (`val`) e mutáveis (`var`) no futuro.
- Funções puras e com efeitos colaterais (ex.: `print`).
- Condicionais simples (`if`, `else`).
- Tipos básicos: inteiros, booleanos, strings.
- Compilação para Erlang legível, usando boas práticas (ex.: `ok`, finalização de blocos, uso correto de variáveis locais e globais).
- Extensibilidade futura: listas, maps, pattern matching, módulos.

---

## 🏗️ Estrutura da Linguagem

### Variáveis globais
```potion
val x = 5
val nome = "João"
```

→ Traduzido como macros Erlang:
```erlang
-define(X, 5).
-define(NOME, "João").
```

---

### Funções
```potion
fn calcular() {
    val y = x + 3
    return y * 2
}
```

→ Traduzido para Erlang:
```erlang
calcular() ->
    Y = (?X + 3),
    (Y * 2).
```

---

### Condicionais (`if`, `else`)
```potion
fn verificar() {
    if valor > 0 {
        print("Maior que zero")
    } else {
        print("Menor ou igual a zero")
    }
}
```

→ Traduzido para Erlang:
```erlang
verificar() ->
    case (?VALOR > 0) of
        true ->
            io:format("~p~n", ["Maior que zero"]);
        _ ->
            io:format("~p~n", ["Menor ou igual a zero"])
    end.
```

---

### Impressão
```potion
print("Olá Mundo")
```

→ Erlang:
```erlang
io:format("~p~n", ["Olá Mundo"])
```

---

## 🛠️ Arquitetura do Compilador

- **Parser** → Constrói AST (Abstract Syntax Tree).
- **Codegen** → Percorre AST e gera código Erlang.
- **Transpiler** → Usa os dois módulos acima para transformar `.potion` → `.erl`.

---

## ⚡ Roadmap (Próximas Features)

- [ ] Tipagem opcional: `val x: int = 5`
- [ ] Variáveis mutáveis: `var contador = 0`
- [ ] Estruturas compostas: listas, maps.
- [ ] Pattern matching.
- [ ] Módulos e imports.
- [ ] CLI oficial para compilação e execução.

---

## 🔥 Exemplo Completo

```potion
val base = 10

fn somar_valores() {
    val a = base + 5
    val b = a * 2
    return b + 3
}

fn main() {
    somar_valores()
}
```

→ Erlang:
```erlang
-define(BASE, 10).

somar_valores() ->
    A = (?BASE + 5),
    B = (A * 2),
    (B + 3).

main() ->
    somar_valores().
```

---

## 📜 Filosofia

- **Clareza sobre mágica:** Código explícito vence automação obscura.
- **Foco pedagógico:** Ajudar novos programadores a entender compiladores e geração de código.
- **Interoperação:** Integrar bem com o ecossistema Erlang.