# Árvore Sintática Abstrata (AST) — Etapa 4

Este documento descreve a estrutura que o parser devolve ao frontend: a AST, a
árvore de derivação, os passos da construção e os erros sintáticos.

## 1. Tokens, árvore de derivação e AST

São três representações diferentes do mesmo código. Para `x = 5 + 3`:

**Sequência de tokens (Etapa 3):**
`<IDENTIFICADOR, x> <OPERADOR, => <LITERAL_INTEIRO, 5> <OPERADOR, +> <LITERAL_INTEIRO, 3> <NOVA_LINHA> <FIM>`

**Árvore de derivação (concreta):** mostra cada regra aplicada e cada token
consumido. Para chegar ao `5`, o parser passa por todas as regras de
precedência:

```text
‹programa›
├── ‹comando›
│   └── ‹linha_simples›
│       ├── ‹atribuicao›
│       │   ├── ‹expressao› › ‹ou› › ‹e› › ‹nao› › ‹comparacao› › ‹soma› › ‹termo› › ‹unario› › ‹potencia› › ‹primario› › ‹atomo›
│       │   │                                                                                                  └── IDENTIFICADOR x
│       │   ├── OPERADOR =
│       │   └── ‹expressao› › ... › ‹soma›
│       │                            ├── ‹termo› › ... › ‹atomo› └── LITERAL_INTEIRO 5
│       │                            ├── OPERADOR +
│       │                            └── ‹termo› › ... › ‹atomo› └── LITERAL_INTEIRO 3
│       └── NOVA_LINHA
└── FIM
```

**AST:** guarda só o que importa para o significado. As regras intermediárias,
os parênteses, o `:` e os fins de linha desaparecem.

```text
Programa
└── Atribuição (=)
    ├── [alvo]  Identificador: x
    └── [valor] Adição (+)
        ├── [esquerda] Número inteiro: 5
        └── [direita]  Número inteiro: 3
```

Na interface, a aba **Árvore de derivação** mostra a primeira árvore e informa
quantos nós cada uma tem. Para esse exemplo, a árvore de derivação tem 38 nós
e a AST, 6.

## 2. Formato de um nó

Todos os nós têm exatamente os mesmos campos:

| Campo         | Tipo           | Descrição |
|---------------|----------------|-----------|
| `id`          | inteiro        | Identificador único do nó. Segue a **ordem de criação**: os filhos são criados antes do pai. |
| `tipo`        | texto          | Tipo do nó (tabela da seção 3). |
| `rotulo`      | texto          | Nome legível do tipo (ex.: `"Adição"`). |
| `categoria`   | texto          | `estrutura`, `comando`, `expressao` ou `literal`. Define a forma e a cor na interface. |
| `regra`       | texto          | Regra da gramática que criou o nó (ex.: `"soma"`). Ver `docs/GRAMATICA.md`. |
| `papel`       | texto ou `null`| Função do nó dentro do pai (ex.: `"condicao"`, `"esquerda"`, `"corpo"`). `null` na raiz. |
| `atributos`   | objeto         | Dados próprios do tipo (operador, nome, valor...). |
| `linha`, `coluna` | inteiros   | Início do trecho no código (contagem a partir de 1). |
| `linha_fim`, `coluna_fim` | inteiros | Último caractere do trecho (inclusive). |
| `filhos`      | lista de nós   | Subárvores, na ordem em que aparecem no código. |

Quando uma expressão está entre parênteses, o nó recebe o atributo
`"entre_parenteses": true`, e a posição dele passa a incluir os parênteses. Os
parênteses não viram nó: eles só mudam a forma da árvore.

### Exemplo completo (`x = 5 + 3`)

```json
{
  "id": 5, "tipo": "PROGRAMA", "rotulo": "Programa", "categoria": "estrutura",
  "regra": "programa", "papel": null, "atributos": {},
  "linha": 1, "coluna": 1, "linha_fim": 1, "coluna_fim": 9,
  "filhos": [
    {
      "id": 4, "tipo": "ATRIBUICAO", "rotulo": "Atribuição", "categoria": "comando",
      "regra": "atribuicao_ou_expressao", "papel": "comando",
      "atributos": { "operador": "=", "alvo": "x" },
      "linha": 1, "coluna": 1, "linha_fim": 1, "coluna_fim": 9,
      "filhos": [
        {
          "id": 0, "tipo": "IDENTIFICADOR", "rotulo": "Identificador", "categoria": "literal",
          "regra": "atomo", "papel": "alvo", "atributos": { "nome": "x" },
          "linha": 1, "coluna": 1, "linha_fim": 1, "coluna_fim": 1, "filhos": []
        },
        {
          "id": 3, "tipo": "ADICAO", "rotulo": "Adição", "categoria": "expressao",
          "regra": "soma", "papel": "valor", "atributos": { "operador": "+" },
          "linha": 1, "coluna": 5, "linha_fim": 1, "coluna_fim": 9,
          "filhos": [
            { "id": 1, "tipo": "NUMERO_INTEIRO", "rotulo": "Número inteiro", "categoria": "literal",
              "regra": "atomo", "papel": "esquerda", "atributos": { "valor": "5" },
              "linha": 1, "coluna": 5, "linha_fim": 1, "coluna_fim": 5, "filhos": [] },
            { "id": 2, "tipo": "NUMERO_INTEIRO", "rotulo": "Número inteiro", "categoria": "literal",
              "regra": "atomo", "papel": "direita", "atributos": { "valor": "3" },
              "linha": 1, "coluna": 9, "linha_fim": 1, "coluna_fim": 9, "filhos": [] }
          ]
        }
      ]
    }
  ]
}
```

## 3. Tipos de nó

| Tipo               | Categoria | Atributos                          | Filhos (papel)                                     | Exemplo de código |
|--------------------|-----------|------------------------------------|----------------------------------------------------|-------------------|
| `PROGRAMA`         | estrutura | —                                  | comandos (`comando`)                               | (raiz)            |
| `BLOCO`            | estrutura | —                                  | comandos (`comando`)                               | corpo de um `if`  |
| `ATRIBUICAO`       | comando   | `operador`, `alvo` (nome ou `null`) | `alvo`, `valor`                                   | `x += 1`          |
| `COMANDO_EXPRESSAO`| comando   | —                                  | `expressao`                                        | `print(x)`        |
| `SE`               | comando   | —                                  | `condicao`, `entao`, `senao_se`*, `senao` (opcional) | `if ... elif ... else` |
| `SENAO_SE`         | comando   | —                                  | `condicao`, `entao`                                | `elif x:`         |
| `ENQUANTO`         | comando   | —                                  | `condicao`, `corpo`                                | `while x:`        |
| `PARA`             | comando   | `variavel`                         | `variavel`, `iteravel`, `corpo`                    | `for i in v:`     |
| `FUNCAO`           | comando   | `nome`, `parametros`               | `parametro`*, `corpo`                              | `def f(a, b):`    |
| `PARAMETRO`        | comando   | `nome`                             | —                                                  | `a`               |
| `RETORNO`          | comando   | —                                  | `valor` (opcional)                                 | `return x`        |
| `PASSE`, `INTERROMPE`, `CONTINUA` | comando | —                    | —                                                  | `pass`, `break`, `continue` |
| `ADICAO`, `SUBTRACAO`, `MULTIPLICACAO`, `DIVISAO`, `DIVISAO_INTEIRA`, `RESTO`, `POTENCIA` | expressao | `operador` | `esquerda`, `direita` | `a + b` |
| `UNARIO`           | expressao | `operador` (`+` ou `-`)            | `operando`                                         | `-x`              |
| `COMPARACAO`       | expressao | `operador` (`==`, `<`, `in`, `is not`...) | `esquerda`, `direita`                       | `a >= b`          |
| `OPERACAO_LOGICA`  | expressao | `operador` (`and` ou `or`)         | `esquerda`, `direita`                              | `a and b`         |
| `NEGACAO`          | expressao | `operador` (`not`)                 | `operando`                                         | `not a`           |
| `CHAMADA`          | expressao | `nome` (ou `null`), `total_argumentos` | `funcao`, `argumento`*                         | `f(1, 2)`         |
| `INDEXACAO`        | expressao | —                                  | `objeto`, `indice`                                 | `v[0]`            |
| `ACESSO_ATRIBUTO`  | expressao | `atributo`                         | `objeto`                                           | `lista.append`    |
| `IDENTIFICADOR`    | literal   | `nome`                             | —                                                  | `x`               |
| `NUMERO_INTEIRO`, `NUMERO_REAL` | literal | `valor` (lexema)        | —                                                  | `10`, `3.14`      |
| `TEXTO`            | literal   | `valor` (lexema com aspas)         | —                                                  | `"oi"`            |
| `LOGICO`, `NULO`   | literal   | `valor`                            | —                                                  | `True`, `None`    |
| `LISTA`            | literal   | `total_elementos`                  | `elemento`*                                        | `[1, 2]`          |

`*` = pode aparecer várias vezes.

A lista completa (tipo, rótulo e categoria) também é devolvida por
`GET /api/gramatica`, no campo `tipos_no`.

## 4. Passos da construção

Para a animação “Construção da árvore”, o parser devolve em `sintatico.passos`
a sequência de eventos do reconhecimento:

```json
[
  { "acao": "entrar", "regra": "programa" },
  { "acao": "entrar", "regra": "comando" },
  ...
  { "acao": "consumir", "token": 0 },
  { "acao": "criar", "no": 0 },
  { "acao": "sair", "regra": "atomo" },
  ...
]
```

- `entrar` e `sair`: o parser começou ou terminou uma regra (o frontend
  reconstrói a pilha de regras ativas a partir desses eventos);
- `consumir`: o token de índice `token` (na lista de tokens) foi consumido;
- `criar`: o nó de `id` igual a `no` foi criado.

Os testes garantem que todos os tokens são consumidos uma vez, em ordem, que
cada nó é criado uma vez e que entradas e saídas de regra são balanceadas
(`TestIntegracaoComScanner`).

## 5. Árvore de derivação

Em `sintatico.derivacao`. Os não terminais têm a forma `{ "regra": "soma",
"filhos": [...] }`; os terminais (folhas) têm a forma
`{ "terminal": "OPERADOR", "lexema": "+", "linha": 1, "coluna": 7, "token": 3 }`.
Lidas da esquerda para a direita, as folhas são exatamente a sequência de
tokens do scanner.

Para não deixar a página lenta, `passos` e `derivacao` são omitidos quando o
código tem mais de 3000 tokens. Nesse caso, `detalhes_omitidos` é `true`, e a
AST continua sendo enviada.

## 6. Erros sintáticos

```json
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
```

| Campo                  | Descrição |
|------------------------|-----------|
| `encontrado`           | Lexema do token encontrado, ou o tipo para tokens sem texto (`NOVA_LINHA`, `FIM`, `INDENTA`, `DEDENTA`). |
| `encontrado_descricao` | O mesmo, em linguagem natural (ex.: “o fim do código”). |
| `esperado`             | Lista do que a regra aceitaria naquele ponto. |
| `regra`, `producao`    | A regra da gramática violada e sua definição em EBNF. |
| `dica`                 | Sugestão de correção (pode ser vazia). |

## 7. Relação com a Etapa 5

A AST foi projetada para a análise semântica:

- os nós `IDENTIFICADOR`, `ATRIBUICAO`, `FUNCAO` e `PARAMETRO` guardam os
  nomes necessários para a **tabela de símbolos**;
- os literais guardam o lexema original, a partir do qual será possível inferir
  **tipos**;
- todos os nós têm posição de início e fim, para que os erros semânticos possam
  apontar o trecho exato do código;
- o campo `papel` diferencia, por exemplo, o alvo de uma atribuição (definição de
  variável) do seu valor (uso de variáveis).
