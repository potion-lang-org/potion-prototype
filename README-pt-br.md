# Potion Language — Documento de Design

> 🇺🇸 [English Version](./README.md)  
> 🤝 [Contributing (EN)](./.github/CONTRIBUTING.en.md) • [Contribuindo (PT-BR)](./.github/CONTRIBUTING.pt-br.md)  
> 📜 [Code of Conduct (EN)](./.github/CODE_OF_CONDUCT.en.md) • [Código de Conduta (PT-BR)](./.github/CODE_OF_CONDUCT.pt-br.md)
> 📘 [Language Spec (EN)](./docs/language-spec.md) • [Especificação da Linguagem (PT-BR)](./docs/language-spec.pt-br.md)

## 📖 Visão Geral

**Potion** é uma linguagem minimalista inspirada em Python, Go, Erlang e Rust. Ela foi pensada para aprendizado, experimentação e geração de código Erlang a partir de uma sintaxe simples e expressiva.  
O objetivo é facilitar a escrita de regras de negócio de forma clara e segura, produzindo código eficiente para ambientes concorrentes como a BEAM/Erlang VM.

---

## ✨ Objetivos

- Sintaxe moderna e enxuta (inspirada em Python/Rust) direcionada ao ecossistema Erlang/OTP.
- Suporte a declarações com `val` e a bindings mutáveis locais com `var`.
- Anotações de tipos opcionais com inferência básica.
- Primitivas de concorrência de primeira classe (`sp`, `send`, `receive`, `match`).
- Pattern matching ergonômico com literais de mapa que viram maps Erlang.
- Código Erlang gerado de forma idiomática (macros para globais, finais explícitos, uso de `ok`).
- Evolução para estruturas de dados mais ricas e módulos, em cima da fase atual de análise semântica.

---

## ✅ Funcionalidades Atuais

- Declarações `val` com anotações de tipo opcionais (`val total: int = 42`).
- Declarações `var` com anotações de tipo opcionais (`var current: none = none`).
- Parâmetros de função com anotações de tipo opcionais (`fn greet(name: str, age: int) { ... }`).
- Reatribuição local de `var` com sintaxe como `current = next_value`.
- Imports de módulos entre arquivos `.potion` com `import nome_do_modulo`.
- Funções com parâmetros, variáveis locais e `return` explícito.
- Literais para inteiros, strings, booleanos, mapas e `none`.
- Operadores aritméticos (`+`, `-`, `*`, `/`) e comparações (`==`, `!=`, `<`, `>`, `<=`, `>=`).
- Concatenação de strings com `+`, emitida como `++` em Erlang.
- Condicionais `if` / `else` traduzidas para `case` Erlang.
- Literais de mapa e pattern matching aninhado via blocos `match`.
- Construtores de concorrência: `sp` para spawn, `send` para envio de mensagens e `receive` para espera.
- Suporte embutido a `self()` para obter o pid atual do processo Erlang.
- Builtin `to_string(...)` para converter valores em string antes de concatenar.
- `print(...)` embutido mapeado para `io:format`.
- Análise semântica dedicada com checagem/inferência de tipos para `int`, `str`, `bool`, `none`, `pid` e `dynamic`.
- CLI (`potionc`) para transpilar `.potion`, compilar e opcionalmente executar.
- Exemplos `.potion` em [`examples/`](./examples/).

---

## 🏗️ Blocos de Construção

### Variáveis globais
```potion
val taxa = 5
val mensagem = "Olá"
```

→ Traduzido para macros Erlang:
```erlang
-define(TAXA, 5).
-define(MENSAGEM, "Olá").
```

> ℹ️ Nomes globais viram `?MACROS`; variáveis locais recebem estilo Capitalizado (`Valor`).
> Potion usa `val` para bindings de módulo e `var` para estado mutável local dentro de funções.

### Funções
```potion
fn calcular(delta: int) {
    val proximo = taxa + delta
    return proximo * 2
}
```

→ Erlang:
```erlang
calcular(Delta) ->
    Proximo = (?TAXA + Delta),
    (Proximo * 2).
```

### Módulos e imports
```potion
import module_helpers

fn main() {
    greet("Bruce")
}
```

Potion resolve `import module_helpers` para `module_helpers.potion` no mesmo diretório do arquivo importador.
Chamadas de funções importadas são escritas sem qualificação em Potion e emitidas internamente como chamadas remotas em Erlang.

### Tipos e `none`
```potion
val atual: none = none
val pronto: bool = true
val meu_pid: pid = self()
```

→ `none` é emitido como `undefined` em Erlang.

### Reatribuição de `var`
```potion
fn acumular() {
    var total: int = 1
    total = total + 2
    print(total)
}
```

Potion compila a reatribuição local de `var` para variáveis Erlang versionadas internamente.
Isso preserva a semântica de single-assignment do Erlang, enquanto expõe sintaxe mutável no nível de Potion.

### Condicionais
```potion
fn verificar(pontos) {
    if pontos > 0 {
        print("Positivo")
    } else {
        print("Zero ou negativo")
    }
}
```

→ Erlang:
```erlang
verificar(Pontos) ->
    case (Pontos > 0) of
        true ->
            io:format("~p~n", ["Positivo"]);
        _ ->
            io:format("~p~n", ["Zero ou negativo"])
    end.
```

### Literais de mapa e pattern matching
```potion
fn descrever(pessoa) {
    match pessoa {
        {nome: quem, idade: anos} => print("Nome: " + quem)
        _ => print("Pessoa desconhecida")
    }
}
```

→ Erlang:
```erlang
descrever(Pessoa) ->
    case Pessoa of
        #{nome := Quem, idade := Anos} ->
            io:format("~p~n", ["Nome: " ++ Quem]);
        _ ->
            io:format("~p~n", ["Pessoa desconhecida"])
    end.
```

> 🔒 As chaves precisam ser identificadores (emitidos como átomos) e os valores podem ser outros mapas ou identificadores.

### Concorrência (`sp`, `send`, `receive`, `match`)
```potion
fn worker() {
    receive msg {
        match msg {
            {hello: nome, reply_to: caller} => {
                print("Oi, " + nome)
                send(caller, {ok: "Mensagem recebida"})
            }
        }
    }
}

fn main() {
    val pid = sp worker()
    send(pid, {hello: "Bruce", reply_to: self()})

    receive resposta {
        match resposta {
            {ok: texto} => print(texto)
            _ => print("Sem resposta")
        }
    }
}
```

→ Erlang:
```erlang
worker() ->
    receive Msg ->
        case Msg of
            #{hello := Nome, reply_to := Caller} ->
                io:format("~p~n", ["Oi, " ++ Nome]),
                Caller ! #{ok => "Mensagem recebida"}
        end
    end.

main() ->
    Pid = spawn(fun () -> worker() end),
    Pid ! #{hello => "Bruce", reply_to => self()},
    receive Resposta ->
        case Resposta of
            #{ok := Texto} ->
                io:format("~p~n", [Texto]);
            _ ->
                io:format("~p~n", ["Sem resposta"])
        end
    end.
```

### Impressão e strings
```potion
print("Total: " + to_string(resultado))
print("Age: " + to_string(idade))
```

→ `io:format("~p~n", ["Total: " ++ potion_to_string_builtin(Resultado)])`

Potion não faz coerção implícita em expressões mistas com `+`.
Isto falha em tempo de compilação:

```potion
val idade: int = 42
val mensagem = "Age: " + idade
```

Use `to_string(...)` explicitamente quando quiser concatenação textual:

```potion
val mensagem = "Age: " + to_string(idade)
```

Para a lista completa de palavras-chave reservadas, builtins, tipos e regras de sintaxe, veja [`docs/language-spec.pt-br.md`](./docs/language-spec.pt-br.md).

### Resumo da Sintaxe Atual

```potion
val total: int = 10
var fallback: none = none

fn main() {
    var aprovado: bool = false
    aprovado = total >= 5

    if aprovado {
        print("ok")
    } else {
        print("not ok")
    }
}
```

Tipos suportados hoje:

- `int`
- `str`
- `bool`
- `none`
- `pid`
- `dynamic`

---

## 🧰 CLI (`potionc`)

O `potionc` é o ponto de entrada em Python localizado em `cli/potionc.py`.

**Requisitos**
- Python 3.8+
- Erlang/OTP (`erlc` e `erl` configurados no PATH)

**Instalação**
```bash
# fluxo de desenvolvimento: mantém o comando apontando para o checkout local
pip install -e .

# instalação comum
pip install .
```

Após `pip install -e .`, mudanças no compilador passam a ser usadas pelo comando `potionc` instalado sem reinstalar a cada edição.

**Uso**
```bash
python -m cli.potionc caminho/para/arquivo.potion [opções]
# após instalar com `pip install -e .` ou `pip install .`, basta executar:
potionc caminho/para/arquivo.potion [opções]
```

**Opções**
- `--outdir DIR` – diretório para os arquivos `.erl`/`.beam` (padrão: `target/`).
- `--no-beam` – pula a compilação Erlang, gera apenas o `.erl`.
- `--emit-ast` – imprime o AST em vez de gerar código.
- `--run` – após compilar, executa `module:main/0` via `erl -noshell`.

**Exemplos**
```bash
# Transpila e compila
python -m cli.potionc exemplo.potion

# Gera apenas o .erl
python -m cli.potionc send_message.potion --no-beam

# Compila para outro diretório e roda main/0
python -m cli.potionc send_message.potion --outdir build --run

# instala a CLI em modo editável para desenvolvimento
pip install -e .
```

---

## 🛠️ Arquitetura do Compilador

- **Lexer** → Tokeniza o código Potion.
- **Parser** → Constrói o AST com declarações, literais, controle de fluxo e nós de concorrência.
- **Codegen** → Percorre o AST e gera Erlang legível.
- **CLI** → Coordena parsing, geração, `erlc` e execução opcional.

---

## ⚡ Roadmap

- [x] Tipagem opcional em declarações `val`.
- [x] Tipagem opcional em declarações `var`.
- [x] Suporte ao literal `none`.
- [x] Literais de mapa com pattern matching básico.
- [x] Primitivas de concorrência (`sp`, `send`, `receive`, `match`).
- [x] CLI oficial para transpilar/compilar/executar.
- [x] Sintaxe de reatribuição / atualização mutável para `var` local.
- [x] Tipagem opcional em parâmetros de função.
- [x] Imports básicos entre arquivos `.potion` no mesmo diretório.
- [ ] Listas, tuplas e coleções adicionais.
- [x] Analisador semântico e checagens estáticas.
- [ ] Geração direta de BEAM (sem Erlang intermediário).

---

## 📐 Limites Atuais

- Literais numéricos são tratados como inteiros no parser e no codegen.
- `print(...)` atualmente aceita um único argumento.
- Chaves de mapa precisam ser identificadores simples e são emitidas como átomos Erlang.
- `var` é voltado para estado mutável local de função, não para estado mutável no nível de módulo.
- A checagem de tipos ainda é propositalmente leve e incompleta em comparação com um sistema de tipos completo.
- Imports atualmente resolvem apenas arquivos `.potion` irmãos e expõem funções importadas, não valores globais importados.

---

## 🔥 Exemplo Estendido

```potion
val base: int = 10

fn worker() {
    receive msg {
        match msg {
            {compute: valor, reply_to: caller} => {
                val dobrado = valor * 2
                send(caller, {result: dobrado + base})
            }
        }
    }
}

fn main() {
    val pid = sp worker()
    send(pid, {compute: 5, reply_to: self()})

    receive resposta {
        match resposta {
            {result: total} => print("Resultado: " + to_string(total))
        }
    }
}
```

→ Gera Erlang com macros, variáveis capitalizadas, padrões de mapa e troca de mensagens pronta para a BEAM.

---

## 📜 Filosofia

- **Clareza antes da mágica:** transformações explícitas deixam a curva de aprendizado suave.
- **Foco pedagógico:** desmistificar compiladores, ASTs e o ecossistema BEAM.
- **Interop em primeiro lugar:** o Erlang gerado deve conviver bem com código OTP existente.

> 🧪 Potion ainda é experimental; quebras de compatibilidade podem ocorrer durante a evolução da linguagem.
