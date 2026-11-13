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
