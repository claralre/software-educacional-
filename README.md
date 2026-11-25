# Software Educacional para Análise de Código Python

## 1. Descrição do projeto

Este projeto tem como objetivo desenvolver uma aplicação web educacional para auxiliar estudantes na compreensão dos processos de análise léxica, sintática e semântica de códigos escritos em Python.

O desenvolvimento é incremental:

- **Etapa 1** — configuração do ambiente, estrutura da aplicação e comunicação entre frontend e backend;
- **Etapa 2** — interface web para entrada de código, seleção de exemplos, envio ao backend e mensagens de retorno;
- **Etapa 3** — **análise léxica (scanner)**: o código é transformado em uma sequência de tokens, exibidos de forma didática, com erros léxicos explicados;
- **Etapa 4** — **análise sintática (parser)**: os tokens são verificados contra uma gramática formal (EBNF), o programa é representado como uma **Árvore Sintática Abstrata (AST)** e os erros sintáticos são explicados com a regra gramatical violada. Como diferencial opcional, um **assistente de IA** (Ollama + Llama 3.2) explica tokens, nós e erros;
- **Etapa 5 (atual)** — **análise semântica**: a AST é percorrida para montar a **tabela de símbolos** (nomes, tipos inferidos, escopos, definição e usos) e verificar se o programa **faz sentido** — por exemplo, se cada nome recebeu valor antes de ser usado e se os tipos combinam nas operações. Cada erro semântico explica a regra violada, sugere uma correção e informa o erro que o Python mostraria ao executar.

As três análises aparecem lado a lado na interface, e os erros léxicos, sintáticos e semânticos são claramente diferenciados.

## 2. Linguagem escolhida

A linguagem selecionada é **Python**, devido à sua legibilidade, sintaxe relativamente simples e ampla utilização no ensino de programação.

Um aspecto pouco explorado por ferramentas didáticas de compiladores (que costumam usar subconjuntos de C ou Pascal) é que, em Python, **a indentação faz parte da linguagem**. Por isso o scanner deste projeto gera os tokens `INDENTA` e `DEDENTA`, mostrando ao estudante como os blocos são reconhecidos já na análise léxica.

## 3. Escopo léxico (subconjunto suportado)

| Categoria            | Exemplos                                                        |
|----------------------|-----------------------------------------------------------------|
| Palavras reservadas  | `if`, `elif`, `else`, `while`, `for`, `in`, `def`, `return`, `and`, `or`, `not`, `True`, `False`, `None` (todas as 35 do Python 3) |
| Identificadores      | `numero`, `resultado`, `_x1`, `média` — letra ou `_`, seguida de letras, dígitos ou `_` |
| Literais inteiros    | `0`, `10`, `42`, `1_000`                                         |
| Literais reais       | `3.14`, `.5`, `1e10`, `1.5e-3`                                   |
| Literais string      | `"texto"`, `'A'`, `"""várias linhas"""`, `f"x={x}"`               |
| Operadores           | aritméticos `+ - * / // % **`; relacionais `== != < > <= >=`; atribuição `= += -= *= /= //= %= **=`; lógicos `and or not` (palavras reservadas) |
| Delimitadores        | `(` `)` `[` `]` `{` `}` `,` `:` `.` `;`                          |
| Comentários          | `# até o fim da linha` — ignorados (não geram tokens)            |
| Espaços em branco    | ignorados entre tokens; no início da linha geram `INDENTA`/`DEDENTA` |
| Estrutura            | `NOVA_LINHA` (fim de instrução), `INDENTA`, `DEDENTA`, `FIM`     |
| Não reconhecidos     | `@`, `$`, `?`, `!` isolado, `&`, `\|`, `^`, `~`, `` ` `` → erro léxico com linha, coluna e dica; o scanner continua a análise |

A especificação completa (regras de formação, todos os erros tratados e o algoritmo) está em [`docs/ESCOPO_LEXICO.md`](docs/ESCOPO_LEXICO.md). A interface também mostra esse escopo na seção **Escopo léxico suportado**, carregada do próprio backend.

## 4. Gramática e analisador sintático

A gramática completa (EBNF), com símbolo inicial, terminais, não terminais, precedência, construções suportadas e fora do escopo, exemplos válidos e inválidos, está em **[`docs/GRAMATICA.md`](docs/GRAMATICA.md)**. Resumo:

```ebnf
programa   = { comando } FIM ;
comando    = se | enquanto | para | funcao | linha_simples ;
se         = "if" expressao ":" bloco { "elif" expressao ":" bloco } [ "else" ":" bloco ] ;
bloco      = linha_simples | NOVA_LINHA INDENTA comando { comando } DEDENTA ;
soma       = termo { ( "+" | "-" ) termo } ;
termo      = unario { ( "*" | "/" | "//" | "%" ) unario } ;
...        (30 regras no total)
```

- **Construções suportadas:** atribuição (simples e composta), expressões aritméticas, relacionais e lógicas, literais e listas, chamadas, indexação, atributos, `if/elif/else`, `while`, `for`, `def` com parâmetros, `return`, `pass`, `break`, `continue`.
- **Fora do escopo:** `class`, `import`, `try`, `lambda`, `with`, dicionários, fatiamento, parâmetros com valor padrão, comparações e atribuições encadeadas, entre outras. O parser recusa essas construções explicando que elas não fazem parte do subconjunto.
- **Precedência** igual à do Python, codificada na própria gramática (uma regra por nível). Por exemplo, `10 + 5 * 2` vira `ADICAO(10, MULTIPLICACAO(5, 2))`, `20 - 5 - 3` vira `SUBTRACAO(SUBTRACAO(20, 5), 3)` e `2 ** 3 ** 2` vira `POTENCIA(2, POTENCIA(3, 2))`.

**Estratégia:** parser **descendente recursivo escrito à mão** ([`backend/analisador_sintatico.py`](backend/analisador_sintatico.py)). Cada regra da gramática é um método com o mesmo nome, então o estudante consegue ler a regra e o código lado a lado. Não há ferramenta geradora nem dependência nova. A justificativa e as alternativas consideradas estão em `docs/GRAMATICA.md`, seção 5.

**Fluxo:** código → validação → scanner (Etapa 3, sem alterações) → tokens → parser → AST → resposta ao frontend.

**Decisão sobre erros léxicos:** se o scanner encontra erros, **o parser não é executado**. Com um caractere inválido falta um token na sequência, e o parser apontaria erros que não existem. Os erros léxicos continuam aparecendo, e a interface avisa que a análise sintática não foi feita.

**Erros sintáticos:** cada erro informa a linha e a coluna, o que foi encontrado, o que era esperado, a regra da gramática violada (com a produção EBNF) e uma dica. A recuperação é em **modo pânico**: o parser pula até o fim da linha (e o bloco indentado seguinte) e continua. Assim, vários erros aparecem de uma vez, sem erros em cascata.

**AST:** formato JSON uniforme. Cada nó tem `tipo`, `categoria`, `regra`, `papel`, `atributos`, posição inicial e final e `filhos`. Os tipos de nó e exemplos estão em **[`docs/AST.md`](docs/AST.md)**, que também explica a diferença entre sequência de tokens, árvore de derivação e AST.

## 4.1. Análise semântica (Etapa 5)

Documentação completa: **[`docs/SEMANTICA.md`](docs/SEMANTICA.md)** (escopo, regras implementadas e não implementadas, estratégia, tabela de símbolos, contrato, novidade e limitações). Resumo:

- **Adaptação ao Python.** Python não tem declarações nem tipos declarados. A regra “declarar antes de usar” vira “**dar valor antes de usar**” (`NameError`), e o tipo de cada variável é **inferido** dos valores (`21` é `int`, `"Ana"` é `str`). Blocos de `if`, `while` e `for` **não** criam escopo; só funções criam.
- **Estratégia:** percurso da AST (*tree walk*) em duas fases por escopo: (1) pré-coleta dos nomes que recebem valor e das assinaturas das funções, como o Python faz para decidir o que é variável local; (2) percurso em ordem do texto, verificando cada uso, inferindo tipos e preenchendo a tabela.
- **Regras (erros):** nome sem valor, atribuição composta sem valor (`x += 1`), variável local lida antes de receber valor (`UnboundLocalError`), tipos incompatíveis (`"a" + 1`), sinal em não número, comparação de ordem entre tipos diferentes, `for`/`in` sobre não coleção, indexação inválida, alterar letra de texto, chamar algo que não é função, número de argumentos, argumento inválido de `len`/`range`, parâmetro repetido, `return` fora de função e `break`/`continue` fora de laço.
- **Avisos** (permitidos, mas arriscados): variável que talvez não tenha valor (só recebe dentro de um `if` ou laço), mudança de tipo e reaproveitamento do nome de uma função embutida.
- **Tabela de símbolos:** organizada por escopo (global, um por função, embutido), com nome, categoria, tipo, escopo, linha e coluna da definição, usos, parâmetros, tipo de retorno e sombreamento.
- **Erros léxicos ou sintáticos:** a análise semântica **não é executada** (não há AST válida), e a interface avisa o motivo.
- **Sem erros em cascata:** cada nome indefinido é apontado uma vez, e valores de tipo desconhecido não geram erros de tipo adicionais.

## 5. O scanner

O scanner ([`backend/scanner.py`](backend/scanner.py)) foi **escrito à mão em Python**, sem geradores de analisadores e sem o módulo `tokenize` da biblioteca padrão. Ele percorre o código caractere a caractere; o caractere atual decide qual reconhecedor é usado (identificador, número, string, operador, delimitador, comentário), aplicando a regra do **casamento mais longo** (`**=` é um único token).

Justificativa da escolha:

- cada regra fica em uma função curta, que pode ser lida pelo estudante;
- permite mensagens de erro em português com dicas e **continua após erros**, acumulando todos;
- cada token recebe uma `explicacao` de por que foi classificado assim, usada no modo passo a passo;
- não adiciona dependências e roda no mesmo backend Flask.

## 6. Tecnologias utilizadas

- **Frontend:** HTML, CSS e JavaScript (sem frameworks);
- **Backend:** Python com Flask;
- **Scanner, parser e analisador semântico:** Python (biblioteca padrão), escritos à mão;
- **Assistente de IA (opcional):** Ollama com o modelo Llama 3.2;
- **Servidor web:** Nginx;
- **Conteinerização:** Docker;
- **Orquestração:** Docker Compose;
- **Testes do backend e do scanner:** Python e unittest;
- **Testes do frontend:** Node.js Test Runner;
- **Testes de interação:** Playwright com Chromium;
- **Versionamento:** Git e GitHub.

## 7. Estrutura do projeto

```text
software-educacional/
├── frontend/
│   ├── index.html          # estrutura da interface
│   ├── style.css           # estilos (inclui layout para celular)
│   ├── app.js              # interface e visualizações da análise léxica
│   ├── arvore.js           # visualizações da análise sintática (AST, derivação...)
│   ├── semantica.js        # tabela de símbolos e diagnósticos semânticos
│   ├── ia.js               # botões "Explicar com IA" e professor virtual
│   ├── nginx.conf
│   ├── Dockerfile
│   └── test_interface.js   # testes Node.js
├── backend/
│   ├── app.py              # API Flask
│   ├── scanner.py          # analisador léxico
│   ├── analisador_sintatico.py  # parser descendente recursivo e AST
│   ├── analisador_semantico.py  # análise semântica e tabela de símbolos
│   ├── ia.py               # integração opcional com o Ollama
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── test_app.py         # testes dos endpoints
│   ├── test_scanner.py     # testes unitários do scanner
│   ├── test_parser.py      # testes unitários do parser
│   ├── test_semantico.py   # testes do analisador semântico
│   └── test_ia.py          # testes da integração com a IA (Ollama simulado)
├── tests/
│   └── test_interface.py   # testes de interação (Playwright)
├── scripts/
│   └── testar_tudo.sh      # executa toda a bateria de testes
├── docs/
│   ├── ESCOPO_LEXICO.md    # especificação léxica e funcionamento do scanner
│   ├── GRAMATICA.md        # gramática EBNF e funcionamento do parser
│   ├── AST.md              # formato da AST, derivação e erros sintáticos
│   ├── SEMANTICA.md        # análise semântica e tabela de símbolos
│   ├── IA_OLLAMA.md        # assistente de IA (Ollama + Llama 3.2)
│   ├── ARTIGO_MATERIAIS_E_METODOS.md  # fluxograma e registros para o artigo
│   ├── TUTORIAL.md         # tutorial para estudantes
│   └── RELATORIO_TESTES.md # registro dos testes (Etapas 2 a 5)
├── compose.yaml
└── README.md
```

## 8. Funcionalidades implementadas

### Etapa 2 (mantidas)

- Campo editável para código-fonte e seleção de exemplos;
- Botão de análise e área de resultado;
- Comunicação frontend–backend por HTTP e JSON;
- Validação de código vazio, campo ausente, tipo inválido e JSON malformado;
- Tratamento de falhas de comunicação.

### Etapa 3

- **Scanner** para o subconjunto de Python, integrado ao endpoint `/analisar`;
- **Código colorido** por categoria de token, com legenda; tocar em um trecho mostra tipo, lexema, linha, coluna e a explicação da classificação;
- **Passo a passo animado**: o scanner percorre o código token a token (avançar, voltar, reproduzir, pausar, velocidade), destacando o lexema atual, o que já foi lido e o que ainda falta, com a tabela sendo preenchida progressivamente;
- **Tabela de tokens** (tipo, lexema, linha, coluna, descrição), com filtro por categoria e opção de ocultar tokens de estrutura;
- **Sequência de tokens**: comparação, linha a linha, entre o código original e a sequência `<TIPO, lexema>` que o parser receberá;
- **Resumo**: contagem por categoria (gráfico de barras) e lista de identificadores distintos (prévia da tabela de símbolos);
- **Erros léxicos** com mensagem, localização e dica; clicar em um erro o destaca no código;
- Explicação de **token, lexema e padrão**, **tutorial** inicial e tabela do **escopo léxico**;
- **Nove exemplos**: os três da Etapa 2 e mais condicional, laço, função com comentários, literais, operadores compostos e erros léxicos;
- **Layout responsivo** para celular (abas roláveis, botões grandes para toque, sem rolagem horizontal).

### Etapa 4 (novas)

- **Parser** para o subconjunto de Python, integrado ao endpoint `/analisar`;
- **AST em diagrama** (árvore desenhada de cima para baixo) ou em **lista navegável** com botões *Expandir tudo* e *Recolher tudo*. Os nós têm cor **e forma** por categoria (▣ estrutura, ■ comando, ● expressão, ◆ valor ou nome), para não depender só de cor;
- **Selecionar um nó** destaca o trecho do código e mostra tipo, atributos, posição, papel no nó pai, a regra gramatical que o reconheceu e os tokens que o formam (comparação entre sequência de tokens e árvore);
- **Filtro por tipo de nó**;
- **Construção da árvore passo a passo** (animada): o parser consome os tokens, a pilha de regras ativas é exibida e as subárvores aparecem de baixo para cima conforme os nós são criados;
- **Árvore de derivação** ao lado da AST, com explicação e contagem de nós de cada uma;
- **Gramática** exibida na interface, com a regra do nó ou do erro selecionado destacada;
- **Exportação da AST** em JSON (baixar ou copiar);
- **Erros sintáticos** com rótulo próprio (distinto dos erros léxicos), mensagem, encontrado, esperado, regra gramatical e dica; clicar no erro o destaca no código;
- **Três exemplos novos**: precedência de operadores, programa completo e erros sintáticos;
- **Assistente de IA (opcional)**: *Explicar token com IA*, *Explicar este nó com IA*, *Entender erro com IA* e **professor virtual** para perguntas livres. Veja a seção 11.1.

### Etapa 5 (novas)

- **Analisador semântico** integrado ao endpoint `/analisar`, executado depois do parser;
- **Faixa das três fases** (`✔ Léxica → ✔ Sintática → ✖ Semântica`), mostrando onde a análise parou;
- **Tabela de símbolos agrupada por escopo**; selecionar um símbolo destaca a **definição** (verde) e os **usos** (azul tracejado) no código, explica o tipo e o escopo e permite **abrir o nó na AST**;
- **Erros semânticos** com rótulo próprio (`ERRO SEMÂNTICO`), linha e coluna, **regra violada**, **por quê**, **como corrigir** (inclusive “Você quis dizer…?”) e **o erro que o Python mostraria** ao executar; **avisos** separados (`AVISO SEMÂNTICO`, borda tracejada);
- Aba **Regras semânticas**, com a regra do diagnóstico selecionado destacada;
- **IA**: *Entender erro com IA* em erros e avisos semânticos e *Explicar este símbolo com IA*;
- **Dois exemplos novos**: escopos e tabela de símbolos; erros semânticos.

## 9. Comunicação entre frontend e backend (contrato)

A interface envia `POST /api/analisar`, encaminhado pelo Nginx ao Flask em `/analisar`.

### Requisição

```json
{
  "codigo": "idade = 21"
}
```

### Resposta — análise concluída sem erros (HTTP 200)

```json
{
  "sucesso": true,
  "recebido": true,
  "mensagem": "Análise léxica concluída: 5 token(s) reconhecido(s).",
  "tokens": [
    { "tipo": "IDENTIFICADOR", "lexema": "idade", "linha": 1, "coluna": 1,
      "descricao": "nome definido pelo programador",
      "explicacao": "'idade' começa com letra ou '_' e continua com letras, dígitos ou '_', e não é palavra reservada." },
    { "tipo": "OPERADOR", "lexema": "=", "linha": 1, "coluna": 7, "descricao": "atribuição", "explicacao": "..." },
    { "tipo": "LITERAL_INTEIRO", "lexema": "21", "linha": 1, "coluna": 9, "descricao": "número inteiro", "explicacao": "..." },
    { "tipo": "NOVA_LINHA", "lexema": "", "linha": 1, "coluna": 11, "descricao": "fim de linha lógica", "explicacao": "..." },
    { "tipo": "FIM", "lexema": "", "linha": 1, "coluna": 11, "descricao": "fim do código-fonte", "explicacao": "..." }
  ],
  "erros": [],
  "comentarios": [],
  "resumo": {
    "total_tokens": 5,
    "total_erros": 0,
    "por_tipo": { "IDENTIFICADOR": 1, "OPERADOR": 1, "LITERAL_INTEIRO": 1, "NOVA_LINHA": 1, "FIM": 1 }
  }
}
```

| Campo         | Descrição |
|---------------|-----------|
| `sucesso`     | `true` se não houve erro léxico; `false` caso contrário |
| `recebido`    | mantido da Etapa 2: o código foi recebido e analisado |
| `mensagem`    | resumo legível do resultado |
| `tokens`      | lista de tokens: `tipo`, `lexema`, `linha`, `coluna` (a partir de 1), `descricao` e `explicacao` |
| `erros`       | lista de erros léxicos, ordenada por posição |
| `comentarios` | comentários descartados (`lexema`, `linha`, `coluna`), usados para o destaque |
| `resumo`      | totais e contagem de tokens por tipo |

### Resposta — código com erro léxico (HTTP 200, `sucesso: false`)

Requisição `{"codigo": "x = 1\nresultado = @"}`:

```json
{
  "sucesso": false,
  "recebido": true,
  "mensagem": "Análise léxica concluída com 1 erro(s) léxico(s).",
  "tokens": [ "... tokens válidos continuam sendo retornados ..." ],
  "erros": [
    {
      "tipo": "ERRO_LEXICO",
      "lexema": "@",
      "linha": 2,
      "coluna": 13,
      "mensagem": "Erro léxico na linha 2, coluna 13: caractere não reconhecido '@'.",
      "dica": "Decoradores e o operador '@' não fazem parte do subconjunto suportado."
    }
  ],
  "comentarios": [],
  "resumo": {
    "total_tokens": 8,
    "total_erros": 1,
    "por_tipo": { "IDENTIFICADOR": 2, "OPERADOR": 2, "LITERAL_INTEIRO": 1, "NOVA_LINHA": 2, "FIM": 1 }
  }
}
```

Um erro léxico **não** é um erro da requisição: o código foi recebido e analisado com sucesso, e o resultado da análise indica problemas no código do estudante. Por isso a resposta usa HTTP 200 com `sucesso: false`.

### Respostas de erro da requisição

| Situação                                   | HTTP | `mensagem` |
|--------------------------------------------|------|------------|
| JSON malformado ou corpo que não é objeto  | 400  | Requisição inválida. |
| Campo `codigo` ausente ou não-texto        | 400  | Informe um código-fonte válido. |
| Código vazio ou só com espaços             | 400  | Informe um código-fonte antes de solicitar a análise. |
| Código com mais de 20 000 caracteres       | 413  | O código é muito grande para ser analisado (...). |
| Falha interna inesperada                   | 500  | Ocorreu um erro interno ao analisar o código. Tente novamente. |

Essas respostas têm o formato `{"sucesso": false, "mensagem": "...", "tokens": [], "erros": []}`. Detalhes internos (stack traces) nunca são enviados ao usuário.

### Etapa 4: blocos `lexico` e `sintatico`

Os campos acima (Etapa 3) foram **mantidos com o mesmo significado** para não quebrar a compatibilidade: `sucesso` e `mensagem` de nível superior continuam se referindo à análise léxica. A Etapa 4 acrescenta dois blocos.

Programa válido (`{"codigo": "resultado = 10 + 5 * 2"}`):

```json
{
  "sucesso": true, "recebido": true, "mensagem": "...", "tokens": [ "..." ], "erros": [], "comentarios": [], "resumo": { "...": "..." },
  "lexico": { "sucesso": true, "mensagem": "Análise léxica concluída: 9 token(s) reconhecido(s).", "tokens": [ "..." ], "erros": [] },
  "sintatico": {
    "executado": true,
    "sucesso": true,
    "mensagem": "Análise sintática concluída: o programa segue a gramática. AST com 8 nó(s).",
    "ast": { "id": 7, "tipo": "PROGRAMA", "regra": "programa", "linha": 1, "coluna": 1, "filhos": [ "..." ] },
    "erros": [],
    "derivacao": { "regra": "programa", "filhos": [ "..." ] },
    "passos": [ { "acao": "entrar", "regra": "programa" }, "..." ],
    "resumo": { "total_nos": 8, "por_tipo": { "NUMERO_INTEIRO": 3, "...": 1 } },
    "detalhes_omitidos": false
  }
}
```

Erro sintático (`{"codigo": "if x > 1\n    y = 2"}`), ainda HTTP 200:

```json
"sintatico": {
  "executado": true,
  "sucesso": false,
  "mensagem": "Análise sintática concluída com 1 erro(s) sintático(s).",
  "ast": null,
  "erros": [
    {
      "tipo": "ERRO_SINTATICO",
      "linha": 1,
      "coluna": 9,
      "encontrado": "NOVA_LINHA",
      "encontrado_descricao": "o fim da linha",
      "esperado": ["':'"],
      "mensagem": "Erro sintático na linha 1, coluna 9: a linha terminou, mas era esperado ':' ao final da condição do 'if'.",
      "regra": "se",
      "producao": "se = \"if\" expressao \":\" bloco { \"elif\" expressao \":\" bloco } [ \"else\" \":\" bloco ] ;",
      "dica": "Em Python, o cabeçalho de if, elif, else, while, for e def termina com ':'."
    }
  ],
  "derivacao": null, "passos": null, "resumo": null, "detalhes_omitidos": false
}
```

Erro léxico (`{"codigo": "x = 5 @ 2"}`): `lexico.sucesso` é `false` e o parser não é executado (`sintatico.executado` é `false`, `ast` é `null`, `erros` é vazio e `mensagem` explica o motivo).

| Campo de `sintatico` | Descrição |
|----------------------|-----------|
| `executado`          | `false` quando há erros léxicos (o parser não roda) |
| `sucesso`            | `true` se o programa segue a gramática |
| `ast`                | a AST (formato em `docs/AST.md`) ou `null` se houver erro |
| `erros`              | erros sintáticos, ordenados por posição |
| `derivacao`, `passos`| árvore de derivação e eventos da construção (omitidos acima de 3000 tokens; então `detalhes_omitidos` é `true`) |
| `resumo`             | total de nós e contagem por tipo |

Os códigos HTTP continuam os da Etapa 3: um erro léxico ou sintático **não** é erro da requisição (HTTP 200); entradas inválidas recebem 400 ou 413; falhas internas, 500, sem detalhes.

### Etapa 5: bloco `semantico`

Os campos das Etapas 3 e 4 continuam iguais. A Etapa 5 acrescenta o bloco `semantico`. Exemplo para `x = 10`, `total = x + 5`, `print(totl)`:

```json
"semantico": {
  "executado": true,
  "sucesso": false,
  "mensagem": "Análise semântica concluída com 1 erro(s) semântico(s).",
  "tabela_simbolos": [
    { "nome": "x", "categoria": "variavel", "tipo": "int", "tipos": ["int"], "escopo": "global",
      "escopo_rotulo": "Escopo global", "linha": 1, "coluna": 1, "linha_fim": 1, "coluna_fim": 1,
      "no_id": 0, "inicializado": true, "usado": true,
      "usos": [{ "linha": 2, "coluna": 9, "linha_fim": 2, "coluna_fim": 9, "no_id": 4 }], "atribuicoes": 1 },
    "..."
  ],
  "escopos": [{ "nome": "global", "rotulo": "Escopo global", "tipo": "global", "pai": null, "...": "..." }, "..."],
  "erros": [
    {
      "tipo": "ERRO_SEMANTICO",
      "regra": "IDENTIFICADOR_NAO_DEFINIDO",
      "titulo": "Nome usado sem ter recebido valor",
      "linha": 3, "coluna": 7, "linha_fim": 3, "coluna_fim": 10,
      "mensagem": "Erro semântico na linha 3, coluna 7: 'totl' foi usado, mas não recebe valor em nenhum ponto do programa.",
      "explicacao": "Em Python, uma variável só passa a existir quando recebe um valor (...)",
      "sugestao": "Você quis dizer 'total'?",
      "erro_python": "NameError",
      "no_id": 9
    }
  ],
  "avisos": [],
  "resumo": { "total_simbolos": 3, "total_erros": 1, "total_avisos": 0,
              "por_categoria": { "variavel": 2, "funcao": 0, "parametro": 0, "embutida": 1 } }
}
```

| Campo de `semantico` | Descrição |
|----------------------|-----------|
| `executado` | `false` quando há erros léxicos ou sintáticos (sem AST válida, a análise semântica não roda) |
| `sucesso` | `true` se não há erros semânticos (avisos não reprovam) |
| `tabela_simbolos` | símbolos com nome, categoria, tipo inferido, escopo, posição da definição, usos e, para funções, parâmetros e retorno |
| `escopos` | escopos na ordem: global, um por função, embutido |
| `erros`, `avisos` | diagnósticos com regra, explicação, sugestão, erro do Python e id do nó da AST |
| `resumo` | totais e contagem por categoria |

### Outros endpoints

| Rota | Descrição |
|------|-----------|
| `GET /api/gramatica` | regras da gramática (EBNF), símbolo inicial e tipos de nó da AST |
| `GET /api/semantica` | regras semânticas (código, título, gravidade, explicação, erro do Python) e funções embutidas reconhecidas |
| `GET /api/ia/status` | situação do assistente de IA |
| `POST /api/ia/explicar` | explicação por IA de um token, nó, erro (léxico, sintático ou semântico), símbolo ou pergunta (veja `docs/IA_OLLAMA.md`) |

### Endpoint do escopo léxico

`GET /api/escopo` (Flask: `/escopo`) retorna as palavras reservadas, operadores, delimitadores e tipos de token suportados, usados pela interface.

## 10. Pré-requisitos

Para executar a aplicação:

- Docker Desktop;
- Docker Compose;
- Navegador web (computador ou celular).

Para executar os testes automatizados adicionais:

- Node.js, para os testes do frontend (ou a imagem `node:22-alpine`);
- Python e Playwright, para os testes de interação;
- Chromium instalado pelo Playwright.

A Etapa 4 acrescenta ao backend as variáveis `OLLAMA_BASE_URL`, `OLLAMA_MODELO` e `OLLAMA_TEMPO_LIMITE`, usadas apenas pelo assistente de IA opcional (já definidas no `compose.yaml`). Nenhuma porta nova é publicada e nenhuma credencial é necessária.

## 11. Como executar a aplicação

Clone o repositório ou baixe o arquivo ZIP no GitHub e descompacte-o.

Abra o Terminal na pasta principal do projeto, onde está localizado o arquivo `compose.yaml`, e execute:

```bash
docker compose up -d --build
```

Abra a interface no navegador:

http://localhost:3000

O backend também pode ser acessado diretamente em:

http://localhost:5001

Para testar o scanner pela linha de comando:

```bash
curl -X POST http://localhost:3000/api/analisar \
  -H "Content-Type: application/json" \
  -d '{"codigo": "if x >= 10:\n    y = x * 2"}'
```

Para usar no celular, acesse `http://<IP-do-computador>:3000` estando na mesma rede.

Para encerrar os serviços:

```bash
docker compose down
```

Um roteiro guiado para estudantes está em [`docs/TUTORIAL.md`](docs/TUTORIAL.md).

### 11.1. Assistente de IA (opcional)

O assistente usa o [Ollama](https://ollama.com) com o modelo **Llama 3.2** para **explicar** os resultados. Tokens, AST e erros continuam sendo produzidos só pelo scanner e pelo parser, e a aplicação funciona normalmente sem a IA.

O serviço `ollama` fica no perfil `ia` do Compose, porque a imagem e o modelo ocupam vários gigabytes. Para ligá-lo:

```bash
docker compose --profile ia up -d --build
docker compose exec ollama ollama pull llama3.2
docker compose exec ollama ollama list
```

Depois, na interface, use os botões **✨ Explicar com IA** (em tokens, nós da AST e erros) ou o **Professor virtual**. O backend acessa o Ollama pela rede interna (`http://ollama:11434`, variável `OLLAMA_BASE_URL`) e o navegador nunca o acessa diretamente. Para desligar: `docker compose --profile ia down`.

Detalhes, como instrução de sistema, endpoint, tratamento de falhas, testes, limitações e roteiro da demonstração, estão em **[`docs/IA_OLLAMA.md`](docs/IA_OLLAMA.md)**.

## 12. Testes

Toda a bateria (backend, frontend, comunicação e interação) pode ser executada com:

```bash
sh scripts/testar_tudo.sh
```

### 12.1. Testes unitários do scanner — 50 testes

Palavras reservadas, identificadores, literais, operadores (inclusive compostos), delimitadores, comentários, espaços, indentação, posição (linha/coluna), erros léxicos e casos de borda.

```bash
docker compose run --rm --build backend python -m unittest -v test_scanner
```

**Resultado obtido: 50 testes aprovados.**

### 12.2. Testes unitários do parser — 68 testes

Precedência e associatividade (comparando com árvores de referência), cada construção da gramática, construções aninhadas, estrutura e posições dos nós, erros (construções incompletas, combinações inválidas, fim inesperado), recuperação de erros, casos de borda e integração com o scanner (todos os tokens consumidos em ordem; folhas da derivação = tokens).

```bash
docker compose run --rm --build backend python -m unittest -v test_parser
```

**Resultado obtido: 68 testes aprovados.**

### 12.3. Testes do analisador semântico — 65 testes

Tabela de símbolos (tipos inferidos, escopos, usos, sombreamento, blocos sem escopo), **cada regra com casos válidos e inválidos**, avisos, formato e coerência dos campos, ligação com os nós da AST e com as posições dos tokens, casos de borda, programa grande e um **oráculo**: os programas de teste são executados no próprio Python, e o erro que ele lança (`NameError`, `TypeError`...) tem de ser o que o analisador previu.

```bash
docker compose run --rm --build backend python -m unittest -v test_semantico
```

**Resultado obtido: 65 testes aprovados.**

### 12.4. Testes dos endpoints — 40 testes

7 testes da Etapa 2, 11 da Etapa 3, 8 da análise sintática, 4 da IA e 10 da análise semântica. Os da Etapa 5 cobrem: tabela de símbolos na resposta, contrato com os campos das Etapas 3 e 4 preservados, erro semântico com tabela parcial, aviso sem reprovar, semântica não executada com erro léxico ou sintático, entrada vazia, falha interna sem detalhes, código grande e `/semantica`.

```bash
docker compose run --rm --build backend python -m unittest -v test_app
```

**Resultado obtido: 40 testes aprovados.**

### 12.5. Testes da integração com a IA — 22 testes

Montagem do contexto com os dados reais do compilador (inclusive erros semânticos, avisos e símbolos) e comunicação com um Ollama **simulado**: resposta válida, vazia ou inválida, serviço fora do ar com nova tentativa, tempo esgotado, modelo não instalado e status.

```bash
docker compose run --rm --build backend python -m unittest -v test_ia
```

**Resultado obtido: 22 testes aprovados.**

### 12.6. Testes do frontend — 51 testes

22 testes das Etapas 2 e 3, 18 da Etapa 4 e 11 da Etapa 5: seções da análise semântica, agrupamento da tabela por escopo, destaque da definição e dos usos, escape de HTML, faixa das três fases, rótulos dos três tipos de erro e pedido à IA para avisos.

```bash
docker run --rm -v "$PWD/frontend:/app" -w /app node:22-alpine node --test test_interface.js
```

**Resultado obtido: 51 testes aprovados.**

### 12.7. Testes de interação (Playwright) — 21 cenários

Os 16 cenários das Etapas 2 a 4 (sem alteração) e 5 novos: tabela de símbolos (escopos, sombreamento, destaque e ligação com a AST), erros e avisos semânticos, distinção dos três tipos de erro com a semântica não executada, consistência entre símbolos e tokens, e a análise semântica no celular.

```bash
python -m pip install playwright
python -m playwright install chromium
python tests/test_interface.py
```

Variáveis opcionais: `URL_APLICACAO` (padrão `http://localhost:3000`) e `CAMINHO_CHROMIUM` (para usar um Chromium já instalado).

**Resultado obtido: 21 cenários aprovados.**

O registro detalhado (comandos, resultados, falhas encontradas e correções) está em [`docs/RELATORIO_TESTES.md`](docs/RELATORIO_TESTES.md).

## 13. Limitações conhecidas

- A análise semântica infere tipos só de valores conhecidos: parâmetros, itens de lista e atributos têm tipo **desconhecido**, e erros de tipo com eles não são detectados. A existência de métodos e atributos (`lista.append`) não é verificada. Detalhes em `docs/SEMANTICA.md`, seção 11.
- A verificação “a variável recebeu valor com certeza” é simples (trata `if/elif/else` e laços); em fluxos com `break` ou `return` no meio pode gerar avisos a mais ou a menos.
- Construções fora do subconjunto (`class`, `import`, `try`, `lambda`, dicionários, fatiamento, parâmetros com valor padrão, comparações e atribuições encadeadas...) são recusadas pelo parser com mensagem explicativa.
- Mais de cerca de 50 níveis de parênteses aninhados são recusados, para proteger a pilha de recursão do parser.
- Acima de 3000 tokens, a construção passo a passo e a árvore de derivação não são exibidas (a AST, sim).
- O assistente de IA é opcional, depende de baixar o modelo (cerca de 2 GB) e pode ser lento na CPU. Na demonstração real, o modelo cometeu algumas imprecisões conceituais (registradas em `docs/IA_OLLAMA.md`, seção 10); por isso as respostas são marcadas como geradas por IA.
- Não fazem parte do subconjunto: inteiros em outras bases (`0x1F`, `0b101`), números imaginários (`3j`), operadores bit a bit (`& | ^ ~ << >>`), `@`, `->` e `:=`.
- O conteúdo de f-strings não é analisado: `f"{x}"` é um único `LITERAL_STRING`.
- Colunas são contadas em caracteres; uma tabulação conta como 1 coluna.
- A versão para celular foi validada por emulação no Playwright, não em um aparelho físico.

## 14. Estado atual do projeto

**Primeira etapa — Concluída**

- Estrutura inicial, Docker e Docker Compose, comunicação básica frontend–backend.

**Segunda etapa — Concluída**

- Interface para entrada de código, exemplos, envio ao backend, validações, testes e documentação.

**Terceira etapa — Concluída**

- Scanner para o subconjunto de Python, integrado ao backend;
- Contrato de comunicação com tokens e erros léxicos;
- Visualizações didáticas (código colorido, passo a passo, tabela, sequência, resumo);
- Erros léxicos com mensagens, localização e dicas;
- 90 testes automatizados (68 no backend e 22 no frontend) + 8 cenários de interação (números da Etapa 3);
- Documentação do escopo léxico, tutorial e relatório de testes.

**Quarta etapa — Concluída**

- Gramática formal em EBNF, coerente com o scanner (que não precisou de alterações);
- Parser descendente recursivo integrado ao backend, com recuperação de erros;
- AST em JSON, exibida em diagrama e em lista navegável, com construção passo a passo, árvore de derivação, gramática e exportação;
- Erros sintáticos com regra gramatical, encontrado, esperado e dica;
- Assistente de IA opcional (Ollama + Llama 3.2) com explicações contextuais e professor virtual;
- 166 testes no backend, 40 no frontend e 16 cenários de interface;
- Documentação: `GRAMATICA.md`, `AST.md`, `IA_OLLAMA.md`, `ARTIGO_MATERIAIS_E_METODOS.md` e relatório de testes.

**Quinta etapa — Concluída**

- Escopo da análise semântica definido e adaptado ao Python (sem declarações; tipos inferidos; escopo por função);
- Analisador semântico por percurso da AST, integrado ao backend, com 16 regras de erro e 3 de aviso;
- Tabela de símbolos por escopo, interativa, ligada ao código e à AST;
- Diagnósticos com regra violada, explicação, sugestão de correção e o erro que o Python mostraria;
- Distinção visual entre erro léxico, sintático e semântico, e faixa das três fases;
- 245 testes no backend (65 da semântica, com oráculo Python), 51 no frontend e 21 cenários de interface;
- Documentação: `SEMANTICA.md`, README, relatório de testes, registros para o artigo e tutorial.

## 15. Próximas etapas

- **Etapa 6 — Representação semântica e experiência didática:** usar o `no_id` de cada símbolo e diagnóstico para anotar a AST com tipos e símbolos, desenhar a árvore de escopos e ampliar a experiência didática (por exemplo, um modo guiado pela análise semântica).
- **Avaliação por pares** com o formulário (itens U1–U7 e D1–D7), incluindo as perguntas sobre a novidade da análise semântica (D6 e D7, em `docs/SEMANTICA.md`).
