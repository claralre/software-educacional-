# Relatório de Testes — Segunda Etapa

## 1. Testes do Backend

Ferramenta: Python unittest

Comando:
docker compose run --rm --build backend python -m unittest -v test_app

Resultado:
- Testes executados: 7
- Testes aprovados: 7
- Testes reprovados: 0

Funcionalidades verificadas:
- Rota inicial Hello, World!
- Recebimento de código válido
- Rejeição de código vazio
- Rejeição de entradas com espaços
- Rejeição de campos ausentes
- Rejeição de JSON inválido
- Rejeição de tipos inválidos

## 2. Testes da Interface

Ferramenta: Node.js Test Runner

Comando:
docker run --rm -v "$PWD/frontend:/app" -w /app node:22-alpine node --test test_interface.js

Resultado:
- Testes executados: 8
- Testes aprovados: 8
- Testes reprovados: 0

Funcionalidades verificadas:
- Identificação do software
- Campo de entrada de código
- Botão de análise
- Área de resultados
- Seleção de exemplos
- Presença de três exemplos Python
- Código de comunicação com o backend
- Código de validação de entrada vazia

## 3. Testes Manuais

Ambiente: Docker Compose e navegador Safari.

Verificações realizadas:
- Interface acessível em http://localhost:3000
- Exemplo de operação aritmética carregado corretamente
- Código enviado ao backend
- Mensagem "Código recebido com sucesso."
- Entrada vazia rejeitada com mensagem apropriada

## 4. Limitações

Os testes automatizados da interface verificam
elementos e trechos do código-fonte, mas ainda
não simulam interações reais no navegador.

A análise léxica, sintática e semântica ainda
não foi implementada, conforme o escopo
da segunda etapa.


## Testes automatizados de interação — Playwright

Foi utilizado o Playwright com Python e Chromium para
verificar o funcionamento da interface web.

### Cenários testados

1. Abertura da página do Software Educacional.
2. Verificação do título da aplicação.
3. Seleção de um exemplo de código Python.
4. Preenchimento automático do campo de código.
5. Edição manual do código-fonte.
6. Envio do código para análise.
7. Exibição da mensagem de sucesso retornada pelo backend.
8. Validação da mensagem de erro para código vazio.

### Ambiente de execução

- Sistema operacional: macOS.
- Linguagem dos testes: Python.
- Ferramenta: Playwright com Chromium.
- Aplicação executada com Docker Compose.
- Endereço da interface: http://localhost:3000.

### Comando utilizado

python tests/test_interface.py

### Resultado

Todos os cenários de interação executados foram aprovados.

Mensagem apresentada no terminal:

Testes de interação aprovados!

---

# Relatório de Testes — Terceira Etapa (Análise Léxica)

Data da execução: 25/10/2026.

Ambiente: contêiner Linux com Docker 29 / Docker Compose v5, Python 3.11
(imagem do backend), Node.js 22 (imagem `node:22-alpine`), Playwright
com Chromium (headless).

Todos os testes podem ser executados de uma vez com:

```bash
sh scripts/testar_tudo.sh
```

## 1. Testes unitários do scanner

Ferramenta: Python `unittest` — arquivo `backend/test_scanner.py`.

Comando:

```bash
docker compose run --rm --build backend python -m unittest -v test_scanner
```

Resultado: **50 testes executados, 50 aprovados, 0 reprovados.**

| Grupo                     | O que é verificado                                                        |
|---------------------------|---------------------------------------------------------------------------|
| Palavras reservadas       | cada uma das 35 palavras; maiúsculas (`If`, `true`) viram identificadores; `iffy` não é `if`; `and/or/not` como operadores lógicos |
| Identificadores           | `x`, `_x1`, `__init__`, `média`...; `1abc` gera erro; `valor$` gera erro no `$` |
| Literais                  | inteiros, reais (`.5`, `2.`, `1e10`, `1.5e-3`), strings simples/duplas/triplas/f-strings, `True/False/None`; erros em `007`, `3.14.15`, `1__0`, `10_`, strings não fechadas |
| Operadores                | cada operador do subconjunto; compostos sem espaço (`a==b!=c<=d>=e`); casamento mais longo (`**=`, `===`); `!` isolado gera erro com dica |
| Delimitadores             | cada delimitador; parêntese não fechado gera erro com posição             |
| Comentários e espaços     | comentário ignorado e registrado à parte; espaços e tabulações não geram tokens |
| Estrutura de linhas       | `NOVA_LINHA`, `INDENTA`, `DEDENTA`, `FIM`; linhas em branco; indentação inconsistente; tabs+espaços; junção implícita `( )` e explícita `\` |
| Posição                   | linha/coluna em uma e várias linhas, após string de várias linhas, com `\r\n` |
| Erros léxicos             | `@ $ ? ` & \| ^ ~` com linha e coluna; formato do erro; acúmulo de vários erros; ordenação; erro sintático **não** é erro léxico |
| Casos de borda            | código vazio, só espaços, só comentários, token no fim sem `\n`, resumo por tipo, formato do token |

## 2. Testes dos endpoints do backend

Ferramenta: Python `unittest` com o cliente de testes do Flask — arquivo `backend/test_app.py`.

Comando:

```bash
docker compose run --rm --build backend python -m unittest -v test_app
```

Resultado: **18 testes executados, 18 aprovados, 0 reprovados**
(7 de regressão da Etapa 2 + 11 novos).

Novos cenários:

- Código válido retorna `200`, `sucesso: true` e a lista de tokens;
- Formato da resposta conforme o contrato (`sucesso`, `recebido`, `mensagem`, `tokens`, `erros`, `comentarios`, `resumo`);
- Mensagem de sucesso com o total de tokens;
- Erro léxico retorna `200`, `sucesso: false` e o erro com tipo, lexema, linha, coluna e mensagem;
- Tokens válidos continuam sendo retornados quando há erro léxico;
- Código com erro apenas sintático é tokenizado com sucesso;
- Respostas `400` têm o mesmo formato (`sucesso: false`, `tokens: []`, `erros: []`);
- Código acima de 20 000 caracteres retorna `413`;
- Falha interna retorna `500` sem expor stack trace nem detalhes;
- `GET /analisar` retorna `405`;
- `GET /escopo` retorna o escopo léxico.

## 3. Testes do frontend (estrutura e funções)

Ferramenta: Node.js Test Runner — arquivo `frontend/test_interface.js`.

Comando:

```bash
docker run --rm -v "$PWD/frontend:/app" -w /app node:22-alpine node --test test_interface.js
```

Resultado: **22 testes executados, 22 aprovados, 0 reprovados**
(8 de regressão da Etapa 2 + 14 novos).

Novos cenários: presença da tabela de tokens com as colunas Tipo/Lexema/Linha/Coluna,
das seções de erros, destaque, passo a passo, sequência e resumo; explicação de
token/lexema; adaptação a celular; todos os exemplos do seletor existem; e testes
das funções puras do `app.js` — escape de HTML (proteção contra injeção),
exibição de caracteres invisíveis, conversão linha/coluna → posição, prioridade de
erros sobre tokens no destaque, renderização do código colorido preservando o texto
original, marcação de passos, intercalação de erros no passo a passo e contagem por categoria.

## 4. Testes de interação (Playwright)

Arquivo: `tests/test_interface.py`. Com a aplicação em execução:

```bash
python tests/test_interface.py
```

Resultado: **8 cenários executados, 8 aprovados.**

| Cenário                               | Verificações                                                                 |
|---------------------------------------|------------------------------------------------------------------------------|
| `testar_regressao_etapa2`             | título, seleção de exemplo, edição, envio, validação de código vazio          |
| `testar_tabela_de_tokens`             | 5 tokens para `idade = 21`, tipo/lexema/linha/coluna corretos, filtros         |
| `testar_codigo_colorido_e_detalhes`   | cores por categoria, comentário destacado, detalhes ao clicar, sequência, resumo |
| `testar_passo_a_passo`                | avançar, voltar, reproduzir até o fim, voltar ao início, tabela progressiva   |
| `testar_erros_lexicos`                | 5 erros com mensagem e posição, destaque no código, tokens válidos mantidos   |
| `testar_entradas_hostis_nao_quebram`  | HTML/JS no código não é executado (sem XSS), emoji, só espaços, só comentário |
| `testar_escopo_e_conceitos`           | explicação de token/lexema e escopo léxico carregado do backend              |
| `testar_celular`                      | tela de 375 px com toque, sem rolagem horizontal, passo a passo funcionando  |

Todos os cenários também verificam que nenhum erro de JavaScript ocorreu na página.

## 5. Testes de regressão

| Verificação                                        | Resultado |
|----------------------------------------------------|-----------|
| Testes do backend da Etapa 2 (7)                    | Aprovados |
| Testes de estrutura do frontend da Etapa 2 (8)      | Aprovados |
| Fluxo de interação da Etapa 2 (Playwright)          | Aprovado  |
| `docker compose up -d --build` sobe os dois serviços | Aprovado  |
| `POST http://localhost:3000/api/analisar` via Nginx  | `200`     |
| `GET http://localhost:3000/api/escopo` via Nginx     | `200`     |

## 6. Falhas encontradas e correções

| # | Falha                                                                                       | Correção |
|---|---------------------------------------------------------------------------------------------|----------|
| 1 | Os testes da Etapa 2 esperavam a mensagem "Código recebido com sucesso." e liam o JavaScript dentro do `index.html`. | Mudança intencional do contrato: a mensagem passou a ser o resultado da análise léxica e o JavaScript foi movido para `app.js`. Os testes foram atualizados (o campo `recebido: true` foi mantido por compatibilidade). |
| 2 | A visão "Sequência" não mostrava os erros léxicos, dando a impressão de que trechos do código haviam sumido (encontrado na revisão visual). | Erros passaram a aparecer como `<ERRO_LEXICO, @>` na posição em que ocorrem; teste de interação adicionado. |
| 3 | O JSON da resposta saía com acentos escapados (`\u00e1`) e chaves em ordem alfabética, dificultando a leitura nos exemplos. | `app.json.ensure_ascii = False` e `app.json.sort_keys = False` no Flask. |
| 4 | No ambiente de nuvem usado para os testes, o `pip install` dentro do `docker build` falhou por causa do certificado do proxy de rede do ambiente (problema do ambiente, não do projeto). | Para a execução, foi usada uma imagem base local que confia no certificado do proxy. Os Dockerfiles do projeto não foram alterados por isso. |
| 5 | A versão do Playwright instalada via `pip` procurava uma versão de Chromium diferente da disponível. | O teste aceita a variável opcional `CAMINHO_CHROMIUM` para usar um Chromium já instalado. Sem a variável, o comportamento é o mesmo da Etapa 2. |
| 6 | Durante o envio manual dos arquivos ao GitHub, foi criado por engano um arquivo vazio `scripts` (impedindo a criação da pasta `scripts/`) e o `tests/test_interface.py` recebeu o conteúdo JavaScript de `frontend/test_interface.js`. | O arquivo vazio foi removido, a pasta `scripts/` foi criada e o `tests/test_interface.py` voltou a conter os testes Playwright em Python. |

## 7. Validação do fluxo completo

1. `docker compose up -d --build` — serviços `frontend` (3000) e `backend` (5001) em execução.
2. Acesso a `http://localhost:3000`.
3. Seleção do exemplo "Função com comentários", edição do código e análise — tokens exibidos.
4. Exemplo "Erros léxicos" — 5 erros exibidos com mensagens, dicas e posições.
5. Todos os testes automatizados executados com sucesso.

**Pendente:** a validação manual no navegador físico de um celular não foi
realizada; a versão móvel foi verificada com emulação de tela (375 px) e
toque no Playwright.
