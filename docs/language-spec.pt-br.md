# Especificação da Linguagem Potion

Este documento descreve a superfície atualmente implementada de Potion neste repositório.

Ele é uma referência prática do compilador como ele existe hoje, não uma proposta futura.

## Visão Geral

Potion é uma linguagem pequena que compila para código Erlang e depois para bytecode BEAM pelo fluxo atual da CLI.

Foco atual da implementação:

- declarações `val` no topo do módulo
- bindings mutáveis locais de função com `var`
- funções e `return` explícito
- aritmética e comparações
- mapas, listas e pattern matching
- criação de processos e troca de mensagens
- anotações e inferência leve de tipos
- análise semântica antes da geração de Erlang
- interop com Erlang por meio de módulos importados

## Palavras-chave Reservadas

O lexer reserva atualmente estas palavras-chave:

- `return`
- `val`
- `var`
- `import`
- `erlang`
- `fn`
- `sp`
- `send`
- `receive`
- `on`
- `when`
- `any`
- `match`
- `none`
- `if`
- `else`
- `true`
- `false`

Builtins especiais que são parseadas como identificadores comuns, mas recebem tratamento especial no compilador:

- `print`
- `self`
- `to_string`

## Tipos Suportados

Nomes de tipos aceitos atualmente pelo compilador:

- `int`
- `str`
- `bool`
- `none`
- `atom`
- `pid`
- `dynamic`

Observações:

- `none` vira `undefined` em Erlang
- `atom` vira átomo Erlang
- `pid` é voltado para process ids, como o retorno de `self()` ou `sp ...`
- `dynamic` é usado internamente para valores cujo tipo estático não é conhecido com precisão

## Literais

Literais suportados:

- inteiros, por exemplo `42`
- strings, por exemplo `"hello"`
- booleanos: `true`, `false`
- `none`
- átomos, por exemplo `:ok`, `:error` e `:not_found`
- mapas, por exemplo `{name: "Bruce", age: 42}`
- listas, por exemplo `[1, 2, 3]`

Limites atuais:

- literais numéricos são tratados como inteiros
- a sintaxe de ponto flutuante é tokenizada pelo lexer, mas não vira um tipo numérico separado no AST
- nomes de átomos precisam começar com letra minúscula ou underscore e conter apenas letras, números e underscores
- chaves de mapa precisam ser identificadores simples

## Declarações

### `val`

Forma de declaração estilo imutável:

```potion
val total = 10
val total: int = 10
```

No topo do módulo, `val` é a única forma de declaração suportada.

### `var`

Forma de binding mutável local de função suportada pelo compilador:

```potion
var current = none
var current: none = none
```

Reatribuição local é suportada:

```potion
fn acumular() {
    var total: int = 1
    total = total + 1
    total = total * 3
    print("Total = " + to_string(total))
}
```

Importante:

- reatribuição é suportada para `var` local dentro de funções
- `var` é voltado para estado mutável local de função
- estado global mutável no nível de módulo não faz parte do modelo da linguagem
- atribuir a um `val` faz o compilador falhar
- a reatribuição preserva o tipo previamente estabelecido da variável

### Bindings globais e locais

Bindings no topo do arquivo são expressos com `val` e emitidos como macros Erlang:

```potion
val taxa = 5
val mensagem = "hello"
```

vira:

```erlang
-define(TAXA, 5).
-define(MENSAGEM, "hello").
```

Bindings locais dentro de funções são emitidos como variáveis Erlang capitalizadas.

```potion
fn calcular(delta: int) {
    val proximo = taxa + delta
    return proximo
}
```

vira:

```erlang
calcular(Delta) ->
    Proximo = (?TAXA + Delta),
    Proximo.
```

Para `var` local mutável, o compilador emite internamente variáveis Erlang versionadas para preservar o modelo de single-assignment do Erlang.

## Funções

Sintaxe de declaração:

```potion
fn sum(a: int, b: int) {
    return a + b
}
```

Regras atuais:

- parâmetros são posicionais
- anotações de tipo em parâmetros são opcionais
- `return` explícito é suportado
- se a última instrução não for `return`, a última expressão Erlang emitida vira o resultado da função

Exemplo com parâmetros anotados e não anotados:

```potion
fn greet(name: str, suffix) {
    return name + suffix
}
```

## Módulos E Imports

Potion usa um arquivo-fonte por módulo.

### Importando módulos Potion irmãos

```potion
import module_helpers

fn main() {
    greet("Bruce")
    announce("Bruce", 42)
}
```

Regras atuais:

- `import nome_do_modulo` resolve para `nome_do_modulo.potion`
- módulos importados são buscados no mesmo diretório do arquivo importador
- funções importadas podem ser chamadas diretamente pelo nome no código Potion
- chamadas importadas são emitidas como chamadas remotas Erlang, como `module_helpers:greet(...)`
- funções locais têm precedência sobre funções importadas com o mesmo nome e aridade

Limites atuais:

- módulos `.potion` importados expõem funções, não bindings `val` do topo do módulo
- não há sintaxe de alias nem de import seletivo
- caminhos de módulo em diretórios aninhados ainda não existem

### Importando módulos Erlang

```potion
import erlang math
import erlang lists

fn main() {
    val root = math.sqrt(16)
    val reversed = lists.reverse([1, 2, 3])
    print(root)
    print(reversed)
}
```

Regras atuais:

- `import erlang nome_do_modulo` registra um módulo Erlang externo para o arquivo atual
- chamadas externas Erlang usam o formato `modulo.funcao(...)`
- chamadas externas Erlang são emitidas como `modulo:funcao(...)`
- a análise semântica verifica se o módulo Erlang foi importado antes do uso

Limites atuais:

- o interop Erlang não valida existência de módulo, função nem aridade
- Potion ainda não tem sintaxe de tupla, binário ou fun, então algumas APIs de Erlang são chamáveis, mas ainda não são totalmente ergonômicas

## Expressões

Formas de expressão suportadas:

- identificadores
- chamadas de função
- chamadas de módulo externo no formato `modulo.funcao(...)`
- aritmética
- comparações
- mapas
- listas
- blocos `if`
- blocos `match`
- blocos `receive`
- `send(...)`
- `sp ...`
- instruções de atribuição para `var` local previamente declarado

### Operadores

Operadores aritméticos:

- `+`
- `-`
- `*`
- `/`

Operadores de comparação:

- `==`
- `!=`
- `<`
- `>`
- `<=`
- `>=`

Observações:

- `/` é emitido como divisão inteira `div` em Erlang
- `+` aceita `int + int` e `str + str`
- expressões mistas com `+`, como `str + int` e `int + str`, falham em tempo de compilação
- use `to_string(...)` explicitamente quando precisar de concatenação textual com um valor que não é string
- concatenação de string vira `++` em Erlang depois que a análise semântica confirma que os dois lados são strings

## Builtins

### `print(value)`

Imprime um valor usando `io:format` em Erlang.

```potion
print("hello")
print(total)
```

Regra atual:

- exatamente um argumento

### `self()`

Retorna o pid do processo Erlang atual.

```potion
val me: pid = self()
```

Uso típico:

```potion
send(worker_pid, {hello: "Bruce", reply_to: self()})
```

`reply_to` não é palavra reservada. É apenas a convenção atual de formato de mensagem usada pelo açúcar sintático de `receive`.

### `to_string(value)`

Converte um valor para uma string no formato de lista Erlang.

```potion
val idade: int = 42
print("Age: " + to_string(idade))
```

Comportamento atual da conversão:

- strings e listas: sem mudança
- inteiros: `integer_to_list/1`
- booleanos: convertidos a partir de átomos
- `none` / `undefined`: `"undefined"`
- átomos: `atom_to_list/1`
- binários: `binary_to_list/1`
- fallback: `io_lib:format("~p", ...)` achatado para lista

Potion favorece conversão explícita em vez de coerção implícita.

Isto é inválido:

```potion
val idade: int = 42
val mensagem = "Age: " + idade
```

Isto é válido:

```potion
val idade: int = 42
val mensagem = "Age: " + to_string(idade)
```

## Análise Semântica

Antes da geração de código Erlang, Potion executa uma fase de análise semântica.

Responsabilidades atuais:

- registrar nomes declarados e aridades de funções
- acompanhar bindings mutáveis locais com `var`
- inferir tipos simples quando possível
- validar anotações explícitas de tipo
- rejeitar reatribuições inválidas
- rejeitar operações incompatíveis com `+`, como `str + int`
- garantir que chamadas a módulos Erlang referenciem módulos importados via `import erlang`

A checagem de tipos é intencionalmente leve e está acoplada ao pipeline atual do compilador.

## Controle De Fluxo

### `if / else`

```potion
fn classificar(score) {
    val aprovado: bool = score >= 7

    if aprovado {
        print("approved")
    } else {
        print("rejected")
    }
}
```

Isso é emitido como um `case` de Erlang sobre a condição.

Quando `var` mutáveis são reatribuídas dentro de ramos, o compilador emite um merge após o `case` para que expressões posteriores usem o valor atualizado.

Exemplo:

```potion
fn main() {
    var total: int = 1

    if true {
        total = total + 2
    } else {
        total = total + 10
    }

    print("Total = " + to_string(total))
}
```

## `none`

`none` é a grafia da linguagem para ausência de valor.

```potion
var current: none = none
```

Ele é emitido como `undefined` em Erlang.

Exemplo:

```potion
var current: none = none
val fallback: str = "anonymous"

fn describe(name) {
    if name == none {
        print("Missing name")
    } else {
        print("Name: " + name)
    }
}
```

## Átomos

Átomos são valores simbólicos imutáveis escritos com prefixo `:`.

```potion
val status: atom = :ok
val error = :error
val env = :prod
```

Átomos são emitidos como átomos Erlang:

```potion
print(:not_found)
```

vira:

```erlang
io:format("~p~n", [not_found])
```

Átomos podem ser usados em declarações, argumentos de função, chamadas de função, `return`, `print`, comparações de igualdade, comparações usadas por expressões `if` e valores de mapas.

## Mapas, Listas E Pattern Matching

### Literais de mapa

```potion
val person = {name: "Bruce", age: 42}
```

As chaves de mapa atualmente precisam ser identificadores simples e viram átomos em Erlang.

Mapas aninhados são suportados:

```potion
val request = {
    user: {name: "Bruce"},
    meta: {source: "api"}
}
```

### Literais de lista

```potion
val numbers = [1, 2, 3]
print(numbers)
```

Listas são especialmente úteis no interop com módulos Erlang como `lists`.

### `match`

```potion
match person {
    {name: who, age: years} => {
        print("Name: " + who)
        print("Age: " + to_string(years))
    }
    _ => print("unknown")
}
```

Formas de padrão suportadas:

- binding por identificador
- curinga `_`
- inteiros, strings e booleanos literais
- `none`
- padrões de mapa aninhados

Exemplo com padrões aninhados:

```potion
match request {
    {user: {name: who}, meta: {source: source}} => {
        print("User: " + who)
        print("Source: " + source)
    }
    _ => print("invalid request")
}
```

Observações:

- uma chave de padrão como `age` faz binding do valor no identificador do lado direito, por exemplo `age: years`
- depois disso, a variável disponível é `years`, não `age`
- `match` compila para `case` em Erlang
- se `var` mutáveis forem reatribuídas dentro de ramos de `match`, o compilador faz merge da versão final após a expressão de controle de fluxo

## Concorrência

Potion expõe atualmente uma superfície pequena de concorrência no estilo Erlang.

### `sp`

```potion
val pid: pid = sp worker()
```

Compila para `spawn(fun () -> worker() end)` em Erlang.

### `send(target, message)`

```potion
send(pid, {ok: "done"})
```

Compila para `!` em Erlang.

`send` apenas envia um valor para um processo alvo. Ele não cria um canal de resposta automático.

Se o emissor espera uma resposta, o padrão comum é incluir o próprio pid na mensagem:

```potion
send(worker_pid, {hello: "Bruce", reply_to: self()})
```

### `receive`

```potion
receive {
    on ok(text) {
        print(text)
    }

    on any {
        print("unexpected")
    }
}
```

Compila para `receive ... end` em Erlang.

Dentro de `receive`, `on <tag>(arg1, arg2, ...)` é açúcar sintático para pattern matching de mapa.

Convenção atual de bindings:

- o primeiro binding aponta para o payload sob a tag da mensagem
- o próximo binding aponta para `reply_to`
- `on any` compila para a cláusula de fallback `_`
- expressões opcionais com `when` compilam para guards de Erlang

Exemplo:

```potion
fn worker() {
    receive {
        on hello(name, caller) {
            print("Hello, " + name)
            send(caller, {ok: "received"})
        }

        on any {
            print("unexpected message")
        }
    }
}

fn main() {
    val proc_id: pid = sp worker()
    send(proc_id, {hello: "Bruce", reply_to: self()})

    receive {
        on ok(text) {
            print(text)
        }

        on any {
            print("no response")
        }
    }
}
```

Exemplo com guard:

```potion
receive {
    on data(value, caller) when value > 10 {
        send(caller, {ok: value})
    }

    on any {
        print("ignored")
    }
}
```

Se `var` mutáveis forem reatribuídas dentro de corpos de `receive`, o compilador faz merge da versão final após a expressão de controle de fluxo.

## Interop HTTP Com Erlang

Potion pode chamar módulos Erlang diretamente após um import explícito.

```potion
import erlang ssl
import erlang inets
import erlang httpc

fn main() {
    ssl.start()
    inets.start()

    val response = httpc.request("https://datatrail.com.br")
    print(response)
}
```

Isso compila para chamadas remotas Erlang como `ssl:start()`, `inets:start()` e `httpc:request(...)`.

Para requisições HTTPS, `ssl.start()` precisa rodar antes de `httpc.request(...)`.

A demo de feature server em [`../demo/`](../demo/) usa essa mesma abordagem de interop junto com código bridge em Erlang para operações de HTTP e Mnesia.

## Regras De Geração De Código

Convenções importantes de codegen hoje:

- declarações no topo do módulo viram macros Erlang
- identificadores locais viram variáveis Erlang capitalizadas
- bindings mutáveis `var` viram variáveis Erlang versionadas
- `if` vira `case`
- `match` vira `case`
- mapas viram maps Erlang
- listas viram listas Erlang
- átomos viram átomos Erlang
- padrões de mapa usam `:=`
- concatenação de string usa `++`
- `print(...)` emite `io:format("~p~n", [...])`
- chamadas de módulo externo viram `modulo:funcao(...)`

## Regras De Nome Da CLI

A CLI deriva o nome do módulo Erlang a partir do nome do arquivo-fonte.

Se o nome do arquivo não for um átomo Erlang válido, ele é sanitizado:

- caracteres inválidos viram `_`
- o nome é convertido para minúsculas
- se não começar com letra, recebe o prefixo `potion_`

Exemplo:

- `01_values_and_functions.potion`
- vira o módulo Erlang `potion_01_values_and_functions`

## Limitações Atuais

- estado mutável no nível de módulo não faz parte da linguagem
- anotações de tipo em parâmetros são opcionais, mas anotações de tipo de retorno ainda não existem
- imports entre arquivos `.potion` estão limitados a módulos irmãos e funções importadas
- módulos `.potion` importados não expõem bindings globais `val`
- o interop Erlang está limitado a `import erlang <modulo>` e `<modulo>.<funcao>(...)`
- o interop Erlang não valida existência de módulo, função nem aridade
- ainda não existe sintaxe de tupla
- a checagem de tipos é leve e continua acoplada à geração de código
- concatenação de string depende de o compilador reconhecer a expressão como produtora de string
- não há geração direta de BEAM; Potion gera Erlang primeiro
