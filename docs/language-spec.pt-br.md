# Especificação da Linguagem Potion

Este documento descreve a superfície atualmente implementada da linguagem Potion neste repositório.

Ele é uma referência prática do compilador como ele existe hoje, não uma proposta futura.

## Visão Geral

Potion é uma linguagem pequena que compila para código Erlang.

Foco atual da implementação:

- declarações simples com `val` e `var`
- funções e retornos
- aritmética e comparações
- mapas e pattern matching
- troca de mensagens e criação de processos
- anotações e inferência leve de tipos

## Palavras-chave Reservadas

O lexer reserva atualmente estas palavras-chave:

- `return`
- `val`
- `var`
- `fn`
- `sp`
- `send`
- `receive`
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

Forma de declaração também suportada pelo compilador:

```potion
var current = none
var current: none = none
```

Importante:

- `var` atualmente suporta apenas declaração
- sintaxe de reatribuição como `current = other` ainda não existe

### Bindings globais e locais

`val` e `var` no topo do arquivo são emitidos como macros Erlang:

```potion
val base = 10
var maybe_name: none = none
```

vira:

```erlang
-define(BASE, 10).
-define(MAYBE_NAME, undefined).
```

Bindings locais dentro de funções são emitidos como variáveis Erlang capitalizadas.

## Funções

Sintaxe de declaração:

```potion
fn sum(a, b) {
    return a + b
}
```

Regras atuais:

- parâmetros são posicionais
- parâmetros ainda não têm anotação de tipo
- `return` explícito é suportado
- se a última instrução não for `return`, a última expressão Erlang emitida vira o resultado da função

## Expressões

Formas de expressão suportadas:

- identificadores
- chamadas de função
- aritmética
- comparações
- mapas
- blocos `if`
- blocos `match`
- blocos `receive`
- `send(...)`
- `sp ...`

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
- concatenação de string usa `+` em Potion e vira `++` em Erlang quando o compilador reconhece uma expressão de string

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

## Mapas e Pattern Matching

### Literais de mapa

```potion
val person = {name: "Bruce", age: 42}
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

O receptor então pode fazer binding desse pid em um pattern de mapa e responder explicitamente:

```potion
match message {
    {hello: name, reply_to: caller} => {
        send(caller, {ok: "received"})
    }
}
```

Observações:

- `self()` retorna o pid do processo atual
- `reply_to` não é palavra reservada; é apenas uma chave de mapa por convenção
- `caller` não é palavra reservada; é apenas o nome local usado no pattern
- isso é uma convenção de protocolo de mensagens construída sobre `send`, não uma feature especial de resposta da linguagem

### `receive`

```potion
receive message {
    match message {
        {ok: text} => print(text)
    }
}
```

Compila para `receive ... end` em Erlang.

## Regras de Geração de Código

Convenções importantes atuais do codegen:

- declarações no topo do arquivo viram macros Erlang
- identificadores locais viram variáveis Erlang capitalizadas
- `if` vira `case`
- `match` vira `case`
- mapas viram maps Erlang
- padrões de mapa usam `:=`
- concatenação de string usa `++`
- `print(...)` emite `io:format("~p~n", [...])`

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

- `var` ainda não possui sintaxe de reatribuição
- anotações de tipo em parâmetros não existem
- não há sistema de módulos/imports
- ainda não existem listas nem tuplas na sintaxe Potion
- a checagem de tipos é leve e ainda está acoplada à geração de código
- concatenação de strings depende de o compilador reconhecer a expressão como produtora de string
- não há geração direta de BEAM; Potion gera Erlang primeiro
