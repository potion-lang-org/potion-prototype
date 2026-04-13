# Demo Feature Server

POC pequena de feature server usando Potion compilando para Erlang/BEAM.

## Estrutura

- `main.potion`: entry point da demo
- `http_server.potion`: accept loop e workers por conexão
- `http_router.potion`: roteamento HTTP e validação mínima
- `feature_manager.potion`: processo concorrente com regra principal
- `demo_support.erl`: bridge mínimo para HTTP raw, JSON e Mnesia

## Como rodar

Modo direto a partir de `demo/`:

```bash
potionc --run main.potion
```

O `main.potion` compila e carrega `demo_support.erl` no boot.

Modo explícito:

```bash
python -m cli.potionc demo/main.potion --outdir demo/_build --no-beam
erlc -o demo/_build demo/demo_support.erl
erlc -o demo/_build demo/_build/main.erl demo/_build/http_server.erl demo/_build/http_router.erl demo/_build/feature_manager.erl
erl -noshell -pa demo/_build -eval 'main:main().'
```

Servidor padrão: `http://localhost:4040`

## Curl

Criar ou atualizar:

```bash
curl -i -X POST http://localhost:4040/features \
  -H 'content-type: application/json' \
  -d '{
    "name": "new_checkout",
    "environment": "prod",
    "enabled": true,
    "description": "novo checkout"
  }'
```

Consultar uma feature:

```bash
curl -i "http://localhost:4040/features/new_checkout?environment=prod"
```

Listar todas:

```bash
curl -i http://localhost:4040/features
```

## Fluxo

1. O `http_server` aceita a conexão e lê a requisição.
2. O `http_router` decide o endpoint e envia uma mensagem para o `feature_manager`.
3. O `feature_manager` executa a operação no Mnesia via `demo_support.erl`.
4. A resposta volta por mensagem para o router e o servidor devolve JSON ao cliente.
