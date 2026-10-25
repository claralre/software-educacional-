# Escopo Léxico e Funcionamento do Scanner — Etapa 3

Este documento descreve o subconjunto léxico de **Python** reconhecido pelo
analisador léxico (scanner) do projeto e explica como ele foi implementado.

Implementação: [`backend/scanner.py`](../backend/scanner.py).

## 1. Tabela do subconjunto léxico

| Categoria (`tipo`)   | Regra de formação                                                                 | Exemplos                                    |
|----------------------|-----------------------------------------------------------------------------------|---------------------------------------------|
| `PALAVRA_RESERVADA`  | Uma das 35 palavras reservadas do Python 3 (diferencia maiúsculas de minúsculas)  | `if`, `elif`, `else`, `while`, `for`, `def`, `return`, `and`, `or`, `not`, `True`, `False`, `None` |
| `IDENTIFICADOR`      | Letra ou `_`, seguida de letras, dígitos ou `_`, que não seja palavra reservada    | `numero`, `resultado`, `_x1`, `média`       |
| `LITERAL_INTEIRO`    | Sequência de dígitos; `_` pode separar dígitos; sem zeros à esquerda              | `0`, `10`, `42`, `1_000`                    |
| `LITERAL_REAL`       | Dígitos com ponto decimal e/ou expoente `e`/`E`                                   | `3.14`, `.5`, `2.`, `1e10`, `1.5e-3`        |
| `LITERAL_STRING`     | Texto entre `'...'`, `"..."`, `'''...'''` ou `"""..."""`, com escapes `\`; prefixos `r`, `f`, `b`, `u` | `"olá"`, `'A'`, `"""várias linhas"""`, `f"x={x}"` |
| `OPERADOR`           | Aritméticos, relacionais e de atribuição (abaixo)                                 | `+`, `**`, `==`, `>=`, `=`, `+=`            |
| `DELIMITADOR`        | Parênteses, colchetes, chaves e pontuação                                         | `(`, `)`, `[`, `]`, `{`, `}`, `,`, `:`, `.`, `;` |
| `NOVA_LINHA`         | Quebra de linha que encerra uma instrução                                         | `\n`                                        |
| `INDENTA`            | Aumento da indentação no início de uma linha (abre bloco)                         | 4 espaços após `if x:`                      |
| `DEDENTA`            | Redução da indentação (fecha bloco)                                               | volta à coluna 1 após um bloco              |
| `FIM`                | Fim do código-fonte                                                               | —                                           |

> **Observação sobre caracteres:** Python não possui um tipo "caractere"
> separado; `'A'` é uma string de tamanho 1 e é classificado como
> `LITERAL_STRING`.

### 1.1. Palavras reservadas

```
False  None   True   and    as     assert async  await  break  class
continue def  del    elif   else   except finally for   from   global
if     import in     is     lambda nonlocal not  or     pass   raise
return try    while  with   yield
```

`and`, `or` e `not` são os **operadores lógicos** do Python. Como são
palavras, o scanner os classifica como `PALAVRA_RESERVADA` com a descrição
"palavra reservada (operador lógico)". `True`, `False` e `None` recebem a
descrição "palavra reservada (valor constante)".

Nomes de funções embutidas, como `print`, `len` e `int`, **não** são
palavras reservadas em Python: são identificadores.

### 1.2. Operadores

| Grupo                 | Operadores                                    |
|-----------------------|-----------------------------------------------|
| Aritméticos           | `+` `-` `*` `/` `//` `%` `**`                 |
| Relacionais           | `==` `!=` `<` `>` `<=` `>=`                   |
| Lógicos               | `and` `or` `not` (palavras reservadas)        |
| Atribuição            | `=`                                           |
| Atribuição composta   | `+=` `-=` `*=` `/=` `//=` `%=` `**=`          |

### 1.3. Delimitadores

`(` `)` `[` `]` `{` `}` `,` `:` `.` `;`

### 1.4. Comentários

Apenas comentários de linha: de `#` até o fim da linha. São **ignorados**
(não geram tokens), mas o scanner devolve sua posição na lista
`comentarios` para que a interface possa destacá-los. Python não possui
comentário de bloco; strings com aspas triplas são literais.

### 1.5. Espaços em branco

* Espaços, tabulações e `\f` **entre** tokens são ignorados.
* Espaços **no início** de uma linha formam a indentação, que em Python
  define blocos. O scanner mantém uma pilha de níveis de indentação e gera
  `INDENTA` / `DEDENTA`, como o tokenizador oficial da linguagem.
* Linhas em branco ou só com comentários não geram `NOVA_LINHA` nem
  alteram a indentação.
* Dentro de `()`, `[]` ou `{}`, as quebras de linha são ignoradas (junção
  implícita de linhas). Uma `\` no fim da linha também continua a
  instrução na linha seguinte.
* Uma tabulação na indentação avança até o próximo múltiplo de 8
  (regra do Python); para linha/coluna, conta como 1 caractere.

### 1.6. Caracteres e sequências não reconhecidos

O scanner **não para** ao encontrar um erro: registra o problema e
continua a partir do próximo caractere, para que o estudante veja todos os
erros de uma vez.

| Situação                                 | Exemplo             | Mensagem                                                        |
|------------------------------------------|---------------------|-----------------------------------------------------------------|
| Caractere fora do subconjunto            | `@`, `$`, `?`, `!`, `&`, `\|`, `^`, `~`, `` ` `` | "caractere não reconhecido '@'" + dica específica |
| Número colado a letras / dois pontos     | `1nome`, `3.14.15`  | "literal numérico malformado"                                    |
| Inteiro com zero à esquerda              | `007`               | "o inteiro '007' começa com zero"                               |
| `_` mal posicionado em número            | `1__0`, `10_`       | "uso inválido de '_' no número"                                  |
| String não fechada                       | `"texto`            | "string iniciada com \" não foi fechada nesta linha"            |
| String tripla não fechada                | `"""texto`          | "string iniciada com \"\"\" não foi fechada"                     |
| Parêntese/colchete/chave nunca fechado   | `print(1`           | "'(' foi aberto e nunca fechado"                                 |
| Indentação inconsistente                 | volta para um nível que nunca existiu | "a indentação não corresponde a nenhum bloco aberto"  |
| Indentação misturando tabs e espaços     | `" \tx = 1"`        | "indentação mistura espaços e tabulações"                       |

Dentro de strings e comentários qualquer caractere é aceito.

## 2. Como o scanner funciona

O scanner foi **escrito à mão em Python**, sem geradores de analisadores
(como Lex/PLY) e **sem** usar o módulo `tokenize` da biblioteca padrão.

**Justificativa:**

* O objetivo é educacional: cada regra está visível em uma função curta
  (`_ler_identificador`, `_ler_numero`, `_ler_string`, ...), que pode ser
  lida junto com o estudante.
* Permite produzir mensagens de erro em português, com dicas, e continuar
  a análise após um erro (o `tokenize` padrão interrompe no primeiro erro).
* Permite anexar a cada token uma **explicação** de por que ele foi
  classificado assim, usada no modo passo a passo da interface.
* Não acrescenta dependências ao contêiner (só a biblioteca padrão).
* Está na mesma linguagem do backend (Flask), simplificando a integração.

### 2.1. Algoritmo

O laço principal (`Scanner.analisar`) olha o caractere atual e decide qual
reconhecedor chamar — é um autômato finito em que o primeiro caractere
determina o estado inicial:

| Caractere atual                    | Ação                                                     |
|------------------------------------|----------------------------------------------------------|
| início de linha                    | mede a indentação → `INDENTA` / `DEDENTA`                 |
| `\n`                               | `NOVA_LINHA` (se a linha teve tokens e não há `(` aberto) |
| espaço / tab                       | ignora                                                   |
| `#`                                | lê o comentário até o fim da linha e o descarta          |
| letra ou `_`                       | lê identificador; consulta a tabela de palavras reservadas |
| dígito, ou `.` seguido de dígito   | lê número (inteiro ou real)                              |
| `'` ou `"`                         | lê string (simples ou tripla)                            |
| início de operador                 | aplica o **casamento mais longo**: tenta `**=` antes de `**` antes de `*` |
| delimitador                        | `DELIMITADOR` (controla a pilha de agrupamento)          |
| qualquer outro                     | registra `ERRO_LEXICO` e avança um caractere             |

No fim, o scanner fecha os blocos abertos (emitindo `DEDENTA`) e emite `FIM`.

Linhas e colunas começam em **1**. A coluna é contada em caracteres.

## 3. O que o scanner não faz (limites desta etapa)

* **Não valida a estrutura** do programa: `= = if 10 )` é tokenizado sem
  erros. A ordem dos tokens será verificada pelo analisador sintático
  (Etapa 4).
* Não verifica significado (variável não declarada, tipos): análise
  semântica, Etapa 5.
* Literais inteiros em outras bases (`0x1F`, `0b101`, `0o17`) e números
  imaginários (`3j`) não fazem parte do subconjunto.
* Operadores bit a bit (`&`, `|`, `^`, `~`, `<<`, `>>`), `@`, `->` e `:=`
  não fazem parte do subconjunto (`->` e `:=` são lidos como dois tokens).
* O conteúdo de f-strings (`f"{x}"`) não é analisado: a f-string inteira
  é um `LITERAL_STRING`.
* Fechamentos sem abertura correspondente (ex.: `)` sobrando) são
  tokenizados normalmente; quem os aponta é o parser.
