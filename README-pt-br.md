# Potion

Linguagem experimental para a BEAM com sintaxe simples, concorrência explícita e interop com Erlang.

Potion é um projeto de linguagem pequeno, feito para compilar código `.potion` em Erlang e rodar na BEAM hoje. Ele existe como um experimento prático de design de linguagem, construção de compilador e estrutura de aplicações concorrentes, não como substituto de Erlang ou Elixir. O compilador atual já executa um pipeline real `.potion -> .erl -> .beam` e inclui uma demo funcional de feature server em [`demo/`](./demo/).

> 🇺🇸 [English Version](./README.md)  
> 📘 [Language Spec (EN)](./docs/language-spec.md) • [Especificação da Linguagem (PT-BR)](./docs/language-spec.pt-br.md)  
> 🏗️ [Notas de Arquitetura](./docs/architecture.md)  
> 🤝 [Contributing (EN)](./.github/CONTRIBUTING.en.md) • [Contribuindo (PT-BR)](./.github/CONTRIBUTING.pt-br.md)  
> 📜 [Code of Conduct (EN)](./.github/CODE_OF_CONDUCT.en.md) • [Código de Conduta (PT-BR)](./.github/CODE_OF_CONDUCT.pt-br.md)

## Por Que Potion Existe

Potion existe para explorar como pode ser, na prática, uma linguagem menor e mais direta para programas que rodam na BEAM:

- sintaxe simples para regras de negócio e fluxos baseados em troca de mensagens
- concorrência explícita com `sp`, `send` e `receive`
- interop direto com Erlang, sem fingir que o ecossistema BEAM não existe
- um pipeline de compilação real, ainda legível o suficiente para experimentação e aprendizado

Potion não está tentando substituir Erlang ou Elixir. A direção atual é mais estreita: um experimento prático em simplicidade, concorrência e interop em cima de Erlang/OTP.

## O Que Já Funciona Hoje

- Compilar código `.potion` em `.erl` e depois em `.beam`
- Funções, `val`, `var` local de função e `return` explícito
- Anotações básicas de tipo e checagens semânticas leves
- Mapas, listas, `if`/`else`, `match` e `none`
- Imports entre módulos `.potion` irmãos
- Interop com Erlang via `import erlang <modulo>`
- Concorrência com `sp`, `send`, `receive` e `self()`
- Fluxo de CLI com `potionc`
- Uma demo real de feature server em [`demo/`](./demo/)

## Demo Real

A prova mais rápida de que Potion já faz trabalho real é a POC de feature server em [`demo/`](./demo/). Ela compila módulos Potion, usa código de suporte em Erlang para HTTP/Mnesia e coordena requisições por meio de um processo concorrente gerente.

Rode a demo a partir do diretório `demo/`:

```bash
cd demo
potionc --run main.potion
```

A demo atualmente espera encontrar `demo_support.erl` por caminho relativo, então executar de dentro de `demo/` é o caminho prático hoje.

Depois acesse o servidor em `http://localhost:4040`:

```bash
curl -i -X POST http://localhost:4040/features \
  -H 'content-type: application/json' \
  -d '{
    "name": "new_checkout",
    "environment": "prod",
    "enabled": true,
    "description": "novo fluxo de checkout"
  }'
```

Resposta representativa:

```json
{
  "name": "new_checkout",
  "environment": "prod",
  "enabled": true,
  "description": "novo fluxo de checkout",
  "updated_at": "2026-04-13T12:34:56Z"
}
```

```bash
curl -i "http://localhost:4040/features/new_checkout?environment=prod"
```

```json
{
  "name": "new_checkout",
  "environment": "prod",
  "enabled": true,
  "description": "novo fluxo de checkout",
  "updated_at": "2026-04-13T12:34:56Z"
}
```

```bash
curl -i http://localhost:4040/features
```

```json
[
  {
    "name": "new_checkout",
    "environment": "prod",
    "enabled": true,
    "description": "novo fluxo de checkout",
    "updated_at": "2026-04-13T12:34:56Z"
  }
]
```

Mais detalhes da demo estão em [`demo/README.md`](./demo/README.md).

## Um Gosto Rápido Da Linguagem

Função e bindings locais:

```potion
val base: int = 10

fn soma(delta: int) {
    var total: int = base
    total = total + delta
    return total
}
```

Concorrência:

```potion
fn worker() {
    receive {
        on hello(nome, caller) {
            send(caller, {ok: "ola " + nome})
        }
    }
}

fn main() {
    val pid: pid = sp worker()
    send(pid, {hello: "Bruce", reply_to: self()})
}
```

Interop com módulos Erlang:

```potion
import erlang lists

fn main() {
    print(lists.reverse([1, 2, 3]))
}
```

Para detalhes de sintaxe e semântica, use [`docs/language-spec.pt-br.md`](./docs/language-spec.pt-br.md).

## Instalação E Uso

Requisitos:

- Python 3.8+
- Erlang/OTP com `erlc` e `erl` no `PATH`

Instalação para desenvolvimento:

```bash
pip install -e .
```

Uso básico:

```bash
potionc examples/01_values_and_functions.potion --run
potionc examples/05_spawn_send_receive.potion
potionc demo/main.potion --outdir demo/target --no-beam
```

Instalação por pacote:

```bash
# Gerar instalador .deb
bash packaging/packaging-potion-deb.sh

# Debian/Ubuntu
sudo apt install ./dist/potion-lang_0.1.0_all.deb

# Gerar instalador .rpm
bash packaging/packaging-potion-rpm.sh

# Fedora/RHEL
sudo dnf install ./dist/rpmbuild/RPMS/noarch/potion-lang-0.1.0-1.noarch.rpm
```

## Estado Atual

- Experimental e ainda em evolução
- Breaking changes podem acontecer enquanto a sintaxe e o pipeline do compilador se estabilizam
- A checagem de tipos é intencionalmente leve
- Algumas capacidades práticas hoje ainda dependem de módulos bridge em Erlang em vez de Potion puro
- O interop com Erlang já existe, mas o compilador ainda não valida existência de função nem aridade

## Roadmap

- Feito: `val` tipado, `var` tipado, parâmetros tipados, `none`, mapas, listas, `match`, `if`/`else`
- Feito: primitivas de concorrência, análise semântica, fluxo de CLI para compilar/rodar, imports entre módulos irmãos
- Em andamento: cobertura maior da linguagem, ergonomia melhor de interop e checagens estáticas mais completas
- Ainda falta: literais de átomo, sintaxe de tupla, sistema de módulos mais rico e geração direta de BEAM sem Erlang como etapa intermediária

## Documentação

- [`docs/language-spec.pt-br.md`](./docs/language-spec.pt-br.md): sintaxe e semântica atualmente implementadas
- [`docs/architecture.md`](./docs/architecture.md): lexer, parser, análise semântica, codegen e pipeline da CLI
- [`README.md`](./README.md): visão geral em inglês
- [`demo/README.md`](./demo/README.md): walkthrough da demo de feature server
- [`examples/README.md`](./examples/README.md): exemplos da linguagem
- [`./.github/CONTRIBUTING.pt-br.md`](./.github/CONTRIBUTING.pt-br.md): guia de contribuição
- [`./.github/CODE_OF_CONDUCT.pt-br.md`](./.github/CODE_OF_CONDUCT.pt-br.md): código de conduta
