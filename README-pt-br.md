# Potion Language — Documento de Design

> 🇺🇸 [English Version](./README.md)  
> 🤝 [Contributing (EN)](./.github/CONTRIBUTING.en.md) • [Contribuindo (PT-BR)](./.github/CONTRIBUTING.pt-br.md)  
> 📜 [Code of Conduct (EN)](./.github/CODE_OF_CONDUCT.en.md) • [Código de Conduta (PT-BR)](./.github/CODE_OF_CONDUCT.pt-br.md)

## 📖 Visão Geral

**Potion** é uma linguagem minimalista inspirada em Python, Go, Erlang e Rust. Ela foi pensada para aprendizado, experimentação e geração de código Erlang a partir de uma sintaxe simples e expressiva.  
O objetivo é facilitar a escrita de regras de negócio de forma clara e segura, produzindo código eficiente para ambientes concorrentes como a BEAM/Erlang VM.

---

## ✨ Objetivos

- Sintaxe moderna e enxuta (inspirada em Python/Rust) direcionada ao ecossistema Erlang/OTP.
- Suporte atual a variáveis imutáveis (`val`) e plano futuro para variáveis mutáveis (`var`).
- Anotações de tipos opcionais com inferência básica.
- Primitivas de concorrência de primeira classe (`sp`, `send`, `receive`, `match`).
- Pattern matching ergonômico com literais de mapa que viram maps Erlang.
- Código Erlang gerado de forma idiomática (macros para globais, finais explícitos, uso de `ok`).
- Evolução para estruturas de dados mais ricas, módulos e uma fase de análise semântica.

---

## ✅ Funcionalidades Atuais

- Declarações `val` com anotações de tipo opcionais (`val total: int = 42`).
- Funções com parâmetros, variáveis locais e `return` explícito.
- Operadores aritméticos (`+`, `-`, `*`, `/`) e comparações (`==`, `!=`, `<`, `>`, `<=`, `>=`).
- Concatenação de strings com `+`, emitida como `++` em Erlang.
- Condicionais `if` / `else` traduzidas para `case` Erlang.
- Literais de mapa e pattern matching aninhado via blocos `match`.
- Construtores de concorrência: `sp` para spawn, `send` para envio de mensagens e `receive` para espera.
- `print(...)` embutido mapeado para `io:format`.
- CLI (`potionc`) para transpilar `.potion`, compilar e opcionalmente executar.

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

### Funções
```potion
fn calcular() {
    val proximo = taxa + 3
    return proximo * 2
}
```

→ Erlang:
```erlang
calcular() ->
    Proximo = (?TAXA + 3),
    (Proximo * 2).
```

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
print("Total: " + resultado)
```

→ `io:format("~p~n", ["Total: " ++ Resultado])`

---

## 🧰 CLI (`potionc`)

O `potionc` é o ponto de entrada em Python localizado em `cli/potionc.py`.

**Requisitos**
- Python 3.10+
- Erlang/OTP (`erlc` e `erl` configurados no PATH)

**Uso**
```bash
python -m cli.potionc caminho/para/arquivo.potion [opções]
# após instalar com `pip install .`, basta executar:
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
- [x] Literais de mapa com pattern matching básico.
- [x] Primitivas de concorrência (`sp`, `send`, `receive`, `match`).
- [x] CLI oficial para transpilar/compilar/executar.
- [ ] Variáveis mutáveis (`var`).
- [ ] Listas, tuplas e coleções adicionais.
- [ ] Sistema de módulos e imports.
- [ ] Analisador semântico e checagens estáticas.
- [ ] Geração direta de BEAM (sem Erlang intermediário).

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
            {result: total} => print("Resultado: " + total)
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
