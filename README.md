# Software Educacional para Análise de Código Python

## 1. Descrição do projeto

Este projeto tem como objetivo desenvolver uma aplicação web educacional para auxiliar estudantes na compreensão dos processos de análise léxica, sintática e semântica de códigos escritos em Python.

O desenvolvimento é incremental:

- **Etapa 1** — configuração do ambiente, estrutura da aplicação e comunicação entre frontend e backend;
- **Etapa 2** — interface web para entrada de código, seleção de exemplos, envio ao backend e mensagens de retorno;
- **Etapa 3 (atual)** — **análise léxica (scanner)**: o código é transformado em uma sequência de tokens, exibidos de forma didática, com erros léxicos explicados.

**A análise sintática (Etapa 4) e a análise semântica (Etapa 5) ainda não foram implementadas.** Nesta etapa, o sistema reconhece os tokens, mas não verifica se estão na ordem correta: `= = if 10 )` é tokenizado sem erros.

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

## 4. O scanner

O scanner ([`backend/scanner.py`](backend/scanner.py)) foi **escrito à mão em Python**, sem geradores de analisadores e sem o módulo `tokenize` da biblioteca padrão. Ele percorre o código caractere a caractere; o caractere atual decide qual reconhecedor é usado (identificador, número, string, operador, delimitador, comentário), aplicando a regra do **casamento mais longo** (`**=` é um único token).

Justificativa da escolha:

- cada regra fica em uma função curta, que pode ser lida pelo estudante;
- permite mensagens de erro em português com dicas e **continua após erros**, acumulando todos;
- cada token recebe uma `explicacao` de por que foi classificado assim, usada no modo passo a passo;
- não adiciona dependências e roda no mesmo backend Flask.

## 5. Tecnologias utilizadas

- **Frontend:** HTML, CSS e JavaScript (sem frameworks);
- **Backend:** Python com Flask;
- **Scanner:** Python (biblioteca padrão);
- **Servidor web:** Nginx;
- **Conteinerização:** Docker;
- **Orquestração:** Docker Compose;
- **Testes do backend e do scanner:** Python e unittest;
- **Testes do frontend:** Node.js Test Runner;
- **Testes de interação:** Playwright com Chromium;
- **Versionamento:** Git e GitHub.

## 6. Estrutura do projeto

```text
software-educacional/
├── frontend/
│   ├── index.html          # estrutura da interface
│   ├── style.css           # estilos (inclui layout para celular)
│   ├── app.js              # lógica da interface e visualizações
│   ├── nginx.conf
│   ├── Dockerfile
│   └── test_interface.js   # testes Node.js
├── backend/
│   ├── app.py              # API Flask
│   ├── scanner.py          # analisador léxico
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── test_app.py         # testes dos endpoints
│   └── test_scanner.py     # testes unitários do scanner
├── tests/
│   └── test_interface.py   # testes de interação (Playwright)
├── scripts/
│   └── testar_tudo.sh      # executa toda a bateria de testes
├── docs/
│   ├── ESCOPO_LEXICO.md    # especificação léxica e funcionamento do scanner
│   ├── TUTORIAL.md         # tutorial para estudantes
│   └── RELATORIO_TESTES.md # registro dos testes (Etapas 2 e 3)
├── compose.yaml
└── README.md
```

## 7. Funcionalidades implementadas

### Etapa 2 (mantidas)

- Campo editável para código-fonte e seleção de exemplos;
- Botão de análise e área de resultado;
- Comunicação frontend–backend por HTTP e JSON;
- Validação de código vazio, campo ausente, tipo inválido e JSON malformado;
- Tratamento de falhas de comunicação.

### Etapa 3 (novas)

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

## 8. Comunicação entre frontend e backend (contrato)

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

### Endpoint do escopo léxico

`GET /api/escopo` (Flask: `/escopo`) retorna as palavras reservadas, operadores, delimitadores e tipos de token suportados, usados pela interface.

## 9. Pré-requisitos

Para executar a aplicação:

- Docker Desktop;
- Docker Compose;
- Navegador web (computador ou celular).

Para executar os testes automatizados adicionais:

- Node.js, para os testes do frontend (ou a imagem `node:22-alpine`);
- Python e Playwright, para os testes de interação;
- Chromium instalado pelo Playwright.

Nenhuma variável de ambiente, porta ou credencial nova foi adicionada nesta etapa.

## 10. Como executar a aplicação

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

## 11. Testes

Toda a bateria (backend, frontend, comunicação e interação) pode ser executada com:

```bash
sh scripts/testar_tudo.sh
```

### 11.1. Testes unitários do scanner — 50 testes

Palavras reservadas, identificadores, literais, operadores (inclusive compostos), delimitadores, comentários, espaços, indentação, posição (linha/coluna), erros léxicos e casos de borda.

```bash
docker compose run --rm --build backend python -m unittest -v test_scanner
```

**Resultado obtido: 50 testes aprovados.**

### 11.2. Testes dos endpoints — 18 testes

7 testes da Etapa 2 (regressão) e 11 novos: tokens na resposta, formato do contrato, erro léxico com `sucesso: false`, códigos HTTP (200, 400, 405, 413, 500) e endpoint `/escopo`.

```bash
docker compose run --rm --build backend python -m unittest -v test_app
```

**Resultado obtido: 18 testes aprovados.**

### 11.3. Testes do frontend — 22 testes

8 testes da Etapa 2 (regressão) e 14 novos (estrutura da interface e funções de destaque, passo a passo, escape de HTML e contagem).

```bash
docker run --rm -v "$PWD/frontend:/app" -w /app node:22-alpine node --test test_interface.js
```

**Resultado obtido: 22 testes aprovados.**

### 11.4. Testes de interação (Playwright) — 8 cenários

Regressão do fluxo da Etapa 2, tabela de tokens, código colorido, passo a passo, erros léxicos, entradas hostis (HTML/emoji/só espaços), escopo e uso em tela de celular.

```bash
python -m pip install playwright
python -m playwright install chromium
python tests/test_interface.py
```

Variáveis opcionais: `URL_APLICACAO` (padrão `http://localhost:3000`) e `CAMINHO_CHROMIUM` (para usar um Chromium já instalado).

**Resultado obtido: 8 cenários aprovados.**

O registro detalhado (comandos, resultados, falhas encontradas e correções) está em [`docs/RELATORIO_TESTES.md`](docs/RELATORIO_TESTES.md).

## 12. Limitações conhecidas

- O scanner **não verifica a estrutura** do programa (ordem dos tokens, parênteses sobrando): isso será feito pelo analisador sintático na Etapa 4.
- Não há análise semântica (variáveis não definidas, tipos) — Etapa 5.
- Não fazem parte do subconjunto: inteiros em outras bases (`0x1F`, `0b101`), números imaginários (`3j`), operadores bit a bit (`& | ^ ~ << >>`), `@`, `->` e `:=`.
- O conteúdo de f-strings não é analisado: `f"{x}"` é um único `LITERAL_STRING`.
- Colunas são contadas em caracteres; uma tabulação conta como 1 coluna.
- A versão para celular foi validada por emulação no Playwright, não em um aparelho físico.

## 13. Estado atual do projeto

**Primeira etapa — Concluída**

- Estrutura inicial, Docker e Docker Compose, comunicação básica frontend–backend.

**Segunda etapa — Concluída**

- Interface para entrada de código, exemplos, envio ao backend, validações, testes e documentação.

**Terceira etapa — Concluída**

- Scanner para o subconjunto de Python, integrado ao backend;
- Contrato de comunicação com tokens e erros léxicos;
- Visualizações didáticas (código colorido, passo a passo, tabela, sequência, resumo);
- Erros léxicos com mensagens, localização e dicas;
- 90 testes automatizados (68 no backend e 22 no frontend) + 8 cenários de interação;
- Documentação do escopo léxico, tutorial e relatório de testes.

## 14. Próximas etapas

- **Etapa 4 — Análise sintática:** o parser consumirá a sequência de tokens produzida pelo scanner (incluindo `NOVA_LINHA`, `INDENTA`, `DEDENTA` e `FIM`) para verificar a estrutura do programa e construir a árvore sintática.
- **Etapa 5 — Análise semântica:** verificação de significado, tabela de símbolos e tipos.
