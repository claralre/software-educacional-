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


---

# Relatório de Testes — Quarta Etapa (Análise Sintática e AST)

Data da execução: 12/11/2026.

Ambiente: contêiner Linux com Docker 29 / Docker Compose v5, Python 3.11
(imagem do backend), Node.js 22 (`node:22-alpine`), Playwright com Chromium
(headless), Ollama (`ollama/ollama:latest`) para os testes de infraestrutura da IA.

Bateria completa (regressão das Etapas 1 a 4):

```bash
sh scripts/testar_tudo.sh
```

## 1. Testes unitários do parser

Arquivo: `backend/test_parser.py`.

```bash
docker compose run --rm --build backend python -m unittest -v test_parser
```

Resultado: **68 testes executados, 68 aprovados, 0 reprovados.**

| Grupo | O que é verificado |
|-------|--------------------|
| Precedência e associatividade | `10 + 5 * 2`, `2 + 3 * 4`, `2 * 3 + 4`, `20 - 5 - 3`, `10 - 3 - 2`, `8 / 4 / 2`, `(10 + 5) * 2`, `20 - (5 - 3)`, `((7))`, `2 ** 3 ** 2`, `-2 ** 2`, `2 ** -1`, `7 // 2 % 3`, comparação abaixo da aritmética, `not` > `and` > `or`, `in`, `not in`, `is`, `is not` — comparados com árvores de referência |
| Construções válidas | atribuição simples, composta e a item de lista; literais e listas; chamada, indexação e atributo; `if/elif/else` (com papéis dos filhos); `while`; `for`; `def` com e sem parâmetros; `return` com e sem valor; `pass/break/continue`; bloco na mesma linha; `;`; aninhamento em 4 níveis; vários comandos; quebra de linha dentro de parênteses |
| Estrutura dos nós | todos os nós com o mesmo conjunto de campos, tipo e regra válidos; ids únicos; regra correta em cada nó |
| Posições | início e fim de expressões, parênteses incluídos na faixa, várias linhas, string de várias linhas, posição do nó igual à do token |
| Erros sintáticos | formato do erro; operando ausente; operadores consecutivos; falta de `:`; falta de `)` e `]`; `else`/`elif` sem `if`; palavra reservada como nome e como variável; dois valores sem operador; bloco sem indentação; fim inesperado do código; indentação inesperada; atribuição inválida; construções fora do subconjunto; comando composto depois de `;`; aninhamento excessivo |
| Recuperação de erros | vários erros em comandos diferentes; sem cascata após `if` sem `:`; erro dentro de bloco não impede o resto; AST nula quando há erro |
| Casos de borda | código vazio, só comentários, comando único, fim no meio da construção, contagem de nós |
| Integração com o scanner | o parser consome todos os tokens, em ordem; as folhas da derivação são os tokens; cada nó é criado uma vez; entradas e saídas de regra balanceadas; detalhes desligáveis |

## 2. Testes dos endpoints

Arquivo: `backend/test_app.py` — **30 testes, 30 aprovados**:
- 7 de regressão da Etapa 2;
- 11 da Etapa 3;
- 8 novos de análise sintática;
- 4 novos da IA.

Novos cenários: código válido retorna AST; formato do contrato da Etapa 4 (`lexico`
e `sintatico`) com os campos da Etapa 3 preservados; erro sintático retorna
erros e `ast: null` com HTTP 200; erro léxico **não executa** o parser; entrada
vazia continua como na Etapa 2 (HTTP 400); código grande omite derivação e
passos, mas mantém a AST; falha interna do parser não expõe detalhes (HTTP
500); `GET /gramatica`; IA desligada retorna 503 sem afetar `/analisar`;
explicação com Ollama simulado; pedidos inválidos à IA retornam 400.

## 3. Testes da integração com a IA

Arquivo: `backend/test_ia.py` — **18 testes, 18 aprovados** (Ollama simulado):
- montagem do contexto com dados reais (nó, token, erro léxico, erro sintático
  e conceito), código marcado como dado e pergunta padrão;
- extração de `message.content`;
- respostas vazias ou inválidas;
- Ollama fora do ar: nova tentativa e, depois, desistência;
- tempo esgotado;
- modelo não instalado;
- endpoint de status;
- contexto de precedência nos nós de expressão, glossário nas perguntas
  conceituais e conferência dos números citados no glossário (3 testes
  acrescentados após a demonstração).

**Testes manuais de infraestrutura (com o Ollama real):**

| Verificação | Resultado |
|-------------|-----------|
| `docker compose --profile ia up -d` sobe o contêiner `ollama` | Aprovado |
| `docker compose config --services` (sem perfil) não inclui o `ollama`; com `--profile ia`, inclui | Aprovado |
| Backend acessa `http://ollama:11434` e detecta o modelo ausente (`/api/ia/status`) | Aprovado: "O Ollama está em execução, mas o modelo 'llama3.2' não foi baixado..." |
| `POST /api/ia/explicar` com o Ollama real, sem modelo | Aprovado: HTTP 503 com o comando `ollama pull llama3.2` |
| `POST /api/ia/explicar` com o Ollama parado | Aprovado: HTTP 503 "não está acessível" |
| `/api/analisar` com o Ollama parado | Aprovado: HTTP 200 |
| `docker compose exec ollama ollama pull llama3.2` | Aprovado (após liberar `registry.ollama.ai` na rede do ambiente de testes): modelo de 2,0 GB |
| `/api/ia/status` com o modelo baixado | Aprovado: "Assistente de IA disponível (modelo llama3.2)" |
| Explicação real de nó, erro sintático e pergunta conceitual (API e interface) | Aprovado, com imprecisões do modelo registradas em `docs/IA_OLLAMA.md`, seção 10 |

## 4. Testes do frontend

Arquivo: `frontend/test_interface.js` — **40 testes, 40 aprovados** (22 das Etapas
2 e 3 + 18 novos).

Novos cenários:
- scripts e seções da análise sintática presentes; Dockerfile copia os novos
  arquivos;
- explicações de AST e derivação; professor virtual e diálogo da IA; tempo de
  espera do nginx;
- rótulos dos nós; índice de pais;
- lista e diagrama com todos os nós, papéis e formas; escape de HTML na árvore;
- destaque exato do trecho do nó; erro no fim da linha sem apagar a quebra;
  tokens de cada nó;
- pilha de regras nos passos; floresta da construção de baixo para cima;
- árvore de derivação; contagem por tipo;
- resposta da IA sem executar HTML; formato do pedido à IA.

## 5. Testes de interação (Playwright)

Arquivo: `tests/test_interface.py` — **16 cenários, 16 aprovados** (8 das Etapas
2 e 3, sem alteração, + 8 novos):

| Cenário novo | Verificações |
|--------------|--------------|
| `testar_ast_para_codigo_valido` | AST com 8 nós; multiplicação abaixo da adição; selecionar nó destaca `5 * 2` no código, mostra posição e regra `termo` |
| `testar_lista_expandir_recolher_e_filtro` | programa com 45 nós; modo lista; recolher e expandir tudo; filtro por tipo (4 chamadas); volta ao diagrama |
| `testar_construcao_passo_a_passo_e_derivacao` | passo a passo com pilha de regras; "parar só quando um nó é criado"; árvore completa no fim; derivação; gramática; JSON e download `ast.json` |
| `testar_erros_sintaticos` | 4 erros com rótulo ERRO SINTÁTICO, linha, coluna, regra; sem aba da AST; erro destacado no código; distinção do erro léxico |
| `testar_erro_lexico_nao_executa_parser` | aviso de análise sintática não executada; volta a executar após correção |
| `testar_consistencia_tokens_e_arvore` | linha e coluna do nó iguais às da tabela de tokens; tokens do nó |
| `testar_entrada_grande_nao_trava` | 1100 linhas analisadas; aviso de detalhes omitidos; limite de 20 000 caracteres |
| `testar_ia_contextual` | botão da IA abre o diálogo e mostra a resposta ou o motivo da indisponibilidade; análise continua funcionando |

O cenário `testar_celular` (Etapa 3) foi ampliado: a AST abre em modo lista em
tela de 375 px, sem rolagem horizontal.

## 6. Regressão

| Verificação | Resultado |
|-------------|-----------|
| Testes do scanner (Etapa 3), sem alteração | 50 de 50 aprovados |
| `backend/scanner.py` | sem alteração (o parser usa os tokens existentes) |
| Testes de endpoint das Etapas 2 e 3 | 18 de 18 aprovados (um teste ajustado, ver falha 1) |
| Testes de frontend das Etapas 2 e 3 | 22 de 22 aprovados |
| Cenários Playwright das Etapas 2 e 3 | 8 de 8 aprovados, sem alteração |
| `POST /api/analisar` via Nginx retorna `lexico` e `sintatico` | Aprovado |
| Docker Compose sobe `frontend` e `backend` | Aprovado |

## 7. Falhas encontradas e correções

| # | Falha | Correção |
|---|-------|----------|
| 1 | O teste da Etapa 3 `test_formato_da_resposta` exigia que a resposta tivesse **exatamente** os campos da Etapa 3; com os novos blocos `lexico` e `sintatico`, falhou. | O contrato da Etapa 4 pede que os campos da Etapa 3 sejam **preservados**, não que sejam os únicos. O teste passou a verificar que todos os campos da Etapa 3 continuam presentes, com o mesmo significado. |
| 2 | A nova aba se chamava "Construção passo a passo", e os testes da Etapa 3 que procuram a aba "Passo a passo" passaram a encontrar duas abas (regressão de interface). | A aba nova foi renomeada para "Construção da árvore". Os testes da Etapa 3 não foram alterados. |
| 3 | Clicar em uma aba da análise léxica (ex.: "Tabela de tokens") escondia o painel da AST, porque o código das abas da Etapa 3 selecionava todos os botões `.abas` da página. Encontrado pelo teste `testar_consistencia_tokens_e_arvore`. | O código das abas léxicas passou a atuar só dentro do painel léxico (`#painel .abas button`). |
| 4 | Um erro sintático no fim da linha (ex.: `total = 10 +`) era destacado no lugar da quebra de linha, juntando duas linhas no código exibido (revisão visual). | O marcador do erro passou a ser inserido sem apagar a quebra de linha; teste unitário adicionado. |
| 5 | O destaque de um erro sintático marcava só o primeiro caractere do token (`i` em vez de `if`). | O destaque passou a cobrir o token encontrado inteiro. |
| 6 | Programas maiores abriam no modo diagrama, largo demais, com a raiz fora da área visível. | O diagrama passou a ser o padrão só até 30 nós (e fora do celular), com a raiz centralizada; acima disso, abre o modo lista. |
| 7 | `COPY *.py .` no Dockerfile do backend falhava no construtor clássico do Docker (`DOCKER_BUILDKIT=0`): com vários arquivos, o destino precisa terminar em `/`. | Alterado para `COPY *.py ./`, que funciona nos dois construtores. |
| 8 | Três expectativas erradas nos próprios testes novos: número de nós de `x = 1 + 2` (6, não 5); `def f(a,` é erro **léxico** (parêntese não fechado), não sintático; ids dos nós seguem a ordem de criação. | Os testes foram corrigidos para refletir o comportamento definido na gramática e na documentação (o parser estava correto). |
| 9 | No ambiente de testes, o Docker Hub limitou as requisições (HTTP 429) ao reconstruir a imagem do frontend, e o download do modelo do Ollama foi bloqueado pela rede. | Problemas do ambiente de testes, não do projeto. Os arquivos do frontend foram copiados para o contêiner em execução para os testes de interface; o download do modelo foi feito depois que a rede do ambiente liberou `registry.ollama.ai`. |
| 10 | Na demonstração real, o Llama 3.2 cometeu erros conceituais: chamou a multiplicação de "termo unário", inventou um "nó UNÁRIO", redesenhou a árvore com nós repetidos e, na pergunta sobre AST, disse que ela guarda tipos. | Contexto enviado ao modelo melhorado: resumo da precedência (`PRECEDENCIA`), glossário do projeto (`GLOSSARIO`), regra 12 (não citar nós ou regras fora dos dados) e `temperature: 0`. Os erros diminuíram, mas não desapareceram; os restantes estão registrados em `docs/IA_OLLAMA.md`, seção 10. |

## 8. Validação do fluxo completo

1. `docker compose up -d --build`: serviços `frontend` (3000) e `backend` (5001) em execução.
2. Exemplo "Precedência de operadores": tokens exibidos e AST com a multiplicação
   abaixo da adição, a subtração agrupada à esquerda e a potência à direita.
3. Exemplo "Programa completo": AST com 45 nós, navegável em lista e diagrama.
4. Exemplo "Erros sintáticos": 4 erros com mensagem, posição, regra e dica.
5. Exemplo "Erros léxicos": análise sintática não executada, com aviso.
6. Construção passo a passo, árvore de derivação, gramática e JSON funcionando.
7. Com `--profile ia` e o modelo baixado: explicação real do Llama 3.2 para o nó
   `MULTIPLICACAO`, para o erro de `total = 10 +` e para uma pergunta conceitual
   (`docs/IA_OLLAMA.md`, seção 10).
8. Todos os testes automatizados aprovados (166 no backend, 40 no frontend,
   16 cenários de interface).

**Pendentes:**
- validação em um celular físico (a versão móvel foi testada por emulação).
