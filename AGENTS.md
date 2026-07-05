# Potion Language - Codex Development Guide

Este arquivo define as diretrizes obrigatórias para qualquer implementação realizada no projeto Potion.

O objetivo é garantir consistência arquitetural, evolução incremental da linguagem e conformidade com o processo SDD (Spec Driven Development).

---

## 1. Sempre consulte as especificações

Antes de iniciar qualquer implementação:

- Leia obrigatoriamente `specs/000-git-flow-process/spec.md`.
- Leia a spec da feature que será implementada.
- Leia também as specs relacionadas ou dependentes quando necessário.
- Caso a feature ainda não possua uma spec, crie-a antes de iniciar qualquer implementação.

Nenhuma feature deve ser implementada sem uma spec correspondente.

---

## 2. A Spec é a fonte de verdade

As specs representam o comportamento oficial da linguagem.

Sempre implemente seguindo a especificação.

Caso encontre divergências entre:

- código
- README
- docs
- specs

considere a spec como a principal referência e documente qualquer inconsistência encontrada.

---

## 3. Diferencie linguagem de implementação

Sempre mantenha claramente separados:

- o design da linguagem Potion;
- a implementação atual do compilador;
- limitações temporárias;
- workarounds utilizados pela POC.

Nunca documente uma limitação temporária como se fosse uma decisão permanente da linguagem.

---

## 4. Preserve a arquitetura existente

Antes de criar novos componentes:

- reutilize a arquitetura existente;
- reutilize visitors;
- reutilize passes;
- reutilize estruturas do parser;
- reutilize o semantic analyzer;
- reutilize o code generator.

Evite criar novas camadas quando a funcionalidade puder ser integrada naturalmente ao compilador existente.

Prefira evolução incremental à duplicação.

---

## 5. Faça mudanças pequenas e focadas

Cada implementação deve resolver apenas a feature proposta.

Evite incluir:

- refatorações amplas;
- melhorias não relacionadas;
- mudanças arquiteturais desnecessárias;
- otimizações prematuras.

Cada Pull Request deve possuir um objetivo claro e bem definido.

---

## 6. Mantenha compatibilidade

Novas funcionalidades não devem quebrar:

- código existente;
- exemplos existentes;
- testes existentes;
- comportamento documentado.

Quando uma quebra for inevitável, ela deve ser documentada explicitamente na spec.

---

## 7. Atualize a documentação da feature

Sempre que uma feature for implementada:

- atualize sua spec;
- documente limitações conhecidas;
- documente decisões arquiteturais relevantes;
- registre possíveis evoluções futuras quando apropriado.

---

## 8. Atualize testes

Sempre adicionar ou atualizar:

- testes unitários;
- fixtures;
- exemplos de codegen;
- casos negativos quando aplicável.

Uma implementação sem testes é considerada incompleta.

---

## 9. Utilize Git Flow

Toda implementação deve seguir o fluxo definido em:

`specs/000-git-flow-process/spec.md`

Respeite a estratégia de branches, Pull Requests e releases definida pelo projeto.

---

## 10. Sempre adicionar exemplos da linguagem

Toda nova feature deve adicionar ou atualizar pelo menos um arquivo `.potion` demonstrando seu uso.

Os exemplos devem ser:

- pequenos;
- didáticos;
- executáveis;
- representar o uso recomendado da feature.

Sempre que fizer sentido, os exemplos devem servir também como testes de regressão do compilador.

---

## 11. Priorize a simplicidade

Evite adicionar abstrações desnecessárias.

Prefira soluções:

- simples;
- legíveis;
- previsíveis;
- fáceis de manter.

Complexidade só deve ser introduzida quando realmente necessária.

---

## 12. Preserve a identidade da Potion

Ao implementar novas funcionalidades, priorize sempre:

- consistência com a sintaxe existente;
- interoperabilidade natural com Erlang;
- simplicidade de aprendizado;
- previsibilidade;
- baixo nível de "mágica";
- geração de código Erlang idiomático.

Não copie funcionalidades de outras linguagens apenas por existirem.

Sempre avalie se a solução faz sentido para a filosofia da Potion.

---

## 13. Considere o backend atual como uma implementação

O backend Erlang representa a implementação atual da linguagem.

Ele não deve limitar decisões de design da Potion.

Evite incorporar limitações do backend como parte da semântica da linguagem.

---

## 14. Ao concluir uma implementação

Antes de considerar uma feature concluída, verifique:

- Spec criada ou atualizada.
- Código implementado.
- Testes adicionados.
- Exemplos adicionados.
- Codegen validado.
- Documentação atualizada quando necessário.
- Nenhuma regressão introduzida.

Somente após essa validação a feature pode ser considerada pronta para revisão.