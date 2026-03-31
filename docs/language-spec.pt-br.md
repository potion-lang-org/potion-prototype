# Especificação da Linguagem Potion

Este documento descreve a superfície atualmente implementada da linguagem Potion neste repositório.

Ele é uma referência prática do compilador como ele existe hoje, não uma proposta futura.

## Visão Geral

Potion é uma linguagem pequena que compila para código Erlang.

Foco atual da implementação:

- declarações simples com `val` e bindings mutáveis locais com `var`
- funções e retornos
- aritmética e comparações
- mapas e pattern matching
- troca de mensagens e criação de processos
- anotações e inferência leve de tipos
- análise semântica antes da geração de Erlang

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
- `pid`
- `dynamic`

Observações:

- `none` vira `undefined` em Erlang
- `pid` é voltado para process ids, como o retorno de `self()` ou `sp ...`
- `dynamic` é usado internamente para valores cujo tipo estático não é conhecido com precisão

## Literais

Literais suportados:

- inteiros, por exemplo `42`
- strings, por exemplo `"hello"`
- booleanos: `true`, `false`
- `none`
- mapas, por exemplo `{name: "Bruce", age: 42}`
- listas, por exemplo `[1, 2, 3]`

Limites atuais:

- literais numéricos são tratados como inteiros
- a sintaxe de ponto flutuante é tokenizada pelo lexer, mas não vira um tipo numérico separado no AST
- chaves de mapa precisam ser identificadores simples

## Declarações

### `val`

Forma de declaração estilo imutável:

```potion
val total = 10
val total: int = 10
```

### `var`

Forma de binding mutável local de função suportada pelo compilador:

```potion
var current = none
var current: none = none
```

Reatribuição local é suportada:

```potion
var total: int = 1
total = total + 1
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
val base = 10
```

vira:

```erlang
-define(BASE, 10).
```

Bindings locais dentro de funções são emitidos como variáveis Erlang capitalizadas.
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

## Módulos e Imports

Potion usa um arquivo-fonte por módulo.

Sintaxe de import:

```potion
import module_helpers
```

Sintaxe de import de módulo Erlang externo:

```potion
import erlang httpc
```

Regras atuais:

- `import nome_do_modulo` resolve para `nome_do_modulo.potion`
- módulos importados são buscados no mesmo diretório do arquivo importador
- funções importadas podem ser chamadas diretamente pelo nome no código Potion
- chamadas importadas são emitidas como chamadas remotas Erlang, como `module_helpers:greet(...)`
- funções locais têm precedência sobre funções importadas com o mesmo nome e aridade
- `import erlang nome_do_modulo` registra um módulo Erlang externo para o arquivo atual
- chamadas externas Erlang usam o formato `modulo.funcao(...)`
- chamadas externas Erlang são emitidas como `modulo:funcao(...)`
- a análise semântica só verifica se o módulo Erlang foi importado antes do uso

Limites atuais:

- apenas funções importadas são expostas ao módulo importador
- bindings `val` no topo do módulo importado não são expostos
- não há sintaxe de alias nem de import seletivo
- caminhos de módulo em diretórios aninhados ainda não existem
- o interop Erlang externo não valida existência de função nem aridade

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

### `to_string(value)`

Converte um valor para uma string no formato de lista Erlang.

```potion
print("Age: " + to_string(age))
```

Comportamento atual da conversão:

- strings/listas: sem mudança
- inteiros: `integer_to_list/1`
- booleanos: convertidos a partir de átomos
- `none` / `undefined`: `"undefined"`
- átomos: `atom_to_list/1`
- binários: `binary_to_list/1`
- fallback: `io_lib:format("~p", ...)` achatado para lista

## Análise Semântica

Antes da geração de código Erlang, Potion executa uma fase de análise semântica.

Responsabilidades atuais:

- registrar nomes declarados e aridades de funções
- acompanhar bindings mutáveis locais com `var`
- inferir tipos simples quando possível
- validar anotações explícitas de tipo
- rejeitar reatribuições inválidas
- rejeitar operações incompatíveis com `+`, como `str + int`

Potion favorece conversão explícita em vez de coerção implícita.

Por exemplo, isto é inválido:

```potion
val idade: int = 42
val mensagem = "Age: " + idade
```

Isto é válido:

```potion
val idade: int = 42
val mensagem = "Age: " + to_string(idade)
```

## Controle de Fluxo

### `if / else`

```potion
if score > 0 {
    print("positivo")
} else {
    print("zero ou negativo")
}
```

Isso é emitido como um `case` de Erlang sobre a condição.
Quando `var` mutáveis são reatribuídas dentro de ramos, o compilador emite um merge após o `case` para que expressões posteriores usem o valor atualizado.

## Mapas e Pattern Matching

### Literais de mapa

```potion
val person = {name: "Bruce", age: 42}
```

### Literais de lista

```potion
val numbers = [1, 2, 3]
```

### `match`

```potion
match person {
    {name: who, age: years} => print(who)
    _ => print("unknown")
}
```

Formas de padrão suportadas:

- binding por identificador
- curinga `_`
- inteiros, strings e booleanos literais
- `none`
- padrões de mapa aninhados

Observações:

- uma chave de padrão como `age` faz binding do valor no identificador do lado direito, por exemplo `age: years`
- depois disso, a variável disponível é `years`, não `age`

## Concorrência

Potion expõe atualmente uma pequena superfície de concorrência inspirada em Erlang.

### `sp`

```potion
val pid: pid = sp worker()
```

Compila para `spawn(fun () -> worker() end)` em Erlang.

### `send(target, message)`

```potion
send(pid, {ok: "done"})
```

Compila para o operador `!` de Erlang.

`send` apenas envia um valor para um processo de destino. Ele não cria um canal automático de resposta.

Se o emissor espera uma resposta, o padrão comum é incluir o próprio pid dentro da mensagem:

```potion
send(worker_pid, {hello: "Bruce", reply_to: self()})
```

Dentro de `receive`, o receptor pode fazer binding posicional desse pid com `on <tag>(...)` e responder explicitamente:

```potion
receive {
    on hello(name, caller) {
        send(caller, {ok: "received"})
    }
}
```

Observações:

- `self()` retorna o pid do processo atual
- `reply_to` não é palavra reservada; é apenas uma chave de mapa por convenção
- `caller` não é palavra reservada; é apenas o nome local usado na cláusula de receive
- isso é uma convenção de protocolo de mensagens construída sobre `send`, não uma feature especial de resposta da linguagem

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
Dentro de `receive`, `on <tag>(arg1, arg2, ...)` é açúcar sintático para pattern matching sobre mapas.
O primeiro binding corresponde ao payload principal em `<tag>`, e os bindings seguintes correspondem aos campos extras por convenção fixa.
Hoje, o primeiro campo extra é `reply_to`.
`on any` compila para a cláusula coringa `_`.
Expressões opcionais com `when` viram guards Erlang.
Se `var` mutáveis forem reatribuídas dentro do corpo de `receive` ou de `match` aninhados, o compilador faz merge da versão final após a expressão de controle de fluxo.

Exemplo:

```potion
receive {
    on data(value, caller) when value > 10 {
        print(value)
    }

    on any {
        print("ignored")
    }
}
```

## Regras de Geração de Código

Convenções importantes atuais do codegen:

- declarações no topo do arquivo viram macros Erlang
- identificadores locais viram variáveis Erlang capitalizadas
- `var` locais mutáveis viram variáveis Erlang versionadas
- `if` vira `case`
- `match` vira `case`
- mapas viram maps Erlang
- listas viram listas Erlang
- padrões de mapa usam `:=`
- concatenação de string usa `++`
- `print(...)` emite `io:format("~p~n", [...])`
- chamadas de módulo externo viram `modulo:funcao(...)`

## Regras de Nomeação da CLI

A CLI deriva o nome do módulo Erlang a partir do nome do arquivo-fonte.

Se o nome do arquivo não for válido como módulo Erlang, ele é sanitizado:

- caracteres inválidos viram `_`
- o nome é convertido para minúsculas
- se não começar com letra, recebe o prefixo `potion_`

Exemplo:

- `01_values_and_functions.potion`
- vira módulo Erlang `potion_01_values_and_functions`

## Limites Atuais

- estado mutável no nível de módulo não faz parte da linguagem
- anotações de tipo em parâmetros são opcionais, mas anotações de tipo de retorno ainda não existem
- imports entre arquivos `.potion` são limitados a módulos irmãos e funções importadas
- o interop Erlang é limitado a `import erlang <modulo>` e `<modulo>.<funcao>(...)`
- o interop Erlang não valida existência do módulo, da função nem da aridade
- ainda não existe sintaxe de tupla
- ainda não existe sintaxe de átomo
- a checagem de tipos é leve e ainda está acoplada à geração de código
- concatenação de strings depende de o compilador reconhecer a expressão como produtora de string
- não há geração direta de BEAM; Potion gera Erlang primeiro
