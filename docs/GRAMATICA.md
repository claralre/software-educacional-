# Gramática e Analisador Sintático — Etapa 4

Este documento define a gramática do subconjunto de **Python** aceito pelo
analisador sintático (parser) e explica como o parser foi implementado.

- Implementação: [`backend/analisador_sintatico.py`](../backend/analisador_sintatico.py)
- Testes: [`backend/test_parser.py`](../backend/test_parser.py)
- Formato da árvore produzida: [`docs/AST.md`](AST.md)

A interface mostra esta mesma gramática na aba **Gramática** (carregada do
endpoint `GET /api/gramatica`), destacando a regra do nó ou do erro selecionado.

## 1. Gramática formal (EBNF)

Notação: `=` define a regra; `|` separa alternativas; `{ ... }` repete zero ou
mais vezes; `[ ... ]` é opcional; `( ... )` agrupa; entre aspas, terminais
escritos literalmente; em MAIÚSCULAS, categorias de token do scanner.

```ebnf
programa                = { comando } FIM ;
comando                 = se | enquanto | para | funcao | linha_simples ;
linha_simples           = comando_simples { ";" comando_simples } [ ";" ] NOVA_LINHA ;
comando_simples         = retorno | "pass" | "break" | "continue" | atribuicao_ou_expressao ;
atribuicao_ou_expressao = expressao [ op_atribuicao expressao ] ;
op_atribuicao           = "=" | "+=" | "-=" | "*=" | "/=" | "//=" | "%=" | "**=" ;
retorno                 = "return" [ expressao ] ;
se                      = "if" expressao ":" bloco { "elif" expressao ":" bloco } [ "else" ":" bloco ] ;
enquanto                = "while" expressao ":" bloco ;
para                    = "for" IDENTIFICADOR "in" expressao ":" bloco ;
funcao                  = "def" IDENTIFICADOR "(" [ parametros ] ")" ":" bloco ;
parametros              = IDENTIFICADOR { "," IDENTIFICADOR } [ "," ] ;
bloco                   = linha_simples | NOVA_LINHA INDENTA comando { comando } DEDENTA ;

expressao               = ou ;
ou                      = e { "or" e } ;
e                       = nao { "and" nao } ;
nao                     = "not" nao | comparacao ;
comparacao              = soma [ op_comparacao soma ] ;
op_comparacao           = "==" | "!=" | "<" | ">" | "<=" | ">=" | "in" | "not" "in" | "is" [ "not" ] ;
soma                    = termo { ( "+" | "-" ) termo } ;
termo                   = unario { ( "*" | "/" | "//" | "%" ) unario } ;
unario                  = ( "+" | "-" ) unario | potencia ;
potencia                = primario [ "**" unario ] ;
primario                = atomo { chamada | indexacao | atributo } ;
chamada                 = "(" [ argumentos ] ")" ;
argumentos              = expressao { "," expressao } [ "," ] ;
indexacao               = "[" expressao "]" ;
atributo                = "." IDENTIFICADOR ;
atomo                   = IDENTIFICADOR | LITERAL_INTEIRO | LITERAL_REAL | LITERAL_STRING
                        | "True" | "False" | "None" | "(" expressao ")" | lista ;
lista                   = "[" [ expressao { "," expressao } [ "," ] ] "]" ;
```

**Restrições verificadas pelo parser** (não cabem na EBNF sem duplicar regras):

- Em `atribuicao_ou_expressao`, quando há `op_atribuicao`, o lado esquerdo deve
  ser um **nome** (`x = ...`) ou um **item de lista** (`v[0] = ...`).
- Comparações não podem ser encadeadas (`a < b < c` é recusado com explicação).
- Atribuições não podem ser encadeadas (`a = b = 0` é recusado com explicação).

## 2. Símbolos

**Símbolo inicial:** `programa`.

**Não terminais (30):** `programa`, `comando`, `linha_simples`,
`comando_simples`, `atribuicao_ou_expressao`, `op_atribuicao`, `retorno`, `se`,
`enquanto`, `para`, `funcao`, `parametros`, `bloco`, `expressao`, `ou`, `e`,
`nao`, `comparacao`, `op_comparacao`, `soma`, `termo`, `unario`, `potencia`,
`primario`, `chamada`, `argumentos`, `indexacao`, `atributo`, `atomo`, `lista`.

**Terminais** — todos são tokens produzidos pelo scanner da Etapa 3:

| Terminal na gramática                                         | Categoria do token (Etapa 3) |
|---------------------------------------------------------------|------------------------------|
| `IDENTIFICADOR`                                               | `IDENTIFICADOR`              |
| `LITERAL_INTEIRO`, `LITERAL_REAL`, `LITERAL_STRING`           | mesmas categorias            |
| `"if"`, `"elif"`, `"else"`, `"while"`, `"for"`, `"in"`, `"def"`, `"return"`, `"pass"`, `"break"`, `"continue"`, `"and"`, `"or"`, `"not"`, `"is"`, `"True"`, `"False"`, `"None"` | `PALAVRA_RESERVADA` |
| `"+"` `"-"` `"*"` `"/"` `"//"` `"%"` `"**"` `"=="` `"!="` `"<"` `">"` `"<="` `">="` `"="` `"+="` `"-="` `"*="` `"/="` `"//="` `"%="` `"**="` | `OPERADOR` |
| `"("` `")"` `"["` `"]"` `","` `":"` `"."` `";"`               | `DELIMITADOR`                |
| `NOVA_LINHA`, `INDENTA`, `DEDENTA`, `FIM`                     | tokens estruturais de mesmo nome |

**Coerência com o scanner:** o parser não precisou de nenhum token novo. Os
tokens estruturais criados na Etapa 3 (`NOVA_LINHA`, `INDENTA`, `DEDENTA`,
`FIM`) são exatamente o que a gramática usa para reconhecer o fim de cada
comando e os blocos indentados. O scanner, portanto, **não foi alterado**, e
os testes léxicos da Etapa 3 continuam os mesmos.

## 3. Precedência e associatividade

A precedência não é uma tabela à parte: ela é codificada na própria gramática.
Cada nível de precedência é uma regra que chama a regra do nível seguinte
(mais forte). Por isso, quanto mais forte o operador, mais fundo ele fica na
árvore.

| Nível (do mais fraco ao mais forte) | Regra        | Operadores                         | Associatividade |
|-------------------------------------|--------------|------------------------------------|-----------------|
| 1                                   | `ou`         | `or`                               | esquerda        |
| 2                                   | `e`          | `and`                              | esquerda        |
| 3                                   | `nao`        | `not` (unário)                     | —               |
| 4                                   | `comparacao` | `== != < > <= >= in not in is is not` | não associativo (sem encadeamento) |
| 5                                   | `soma`       | `+ -`                              | esquerda        |
| 6                                   | `termo`      | `* / // %`                         | esquerda        |
| 7                                   | `unario`     | `+ -` (unários)                    | —               |
| 8                                   | `potencia`   | `**`                               | **direita**     |
| 9                                   | `primario`   | chamada `f()`, índice `v[i]`, atributo `a.b` | esquerda |

A ordem é a mesma do Python. Exemplos verificados nos testes
(`TestPrecedenciaEAssociatividade`):

| Código              | Árvore produzida                    | Por quê                                  |
|---------------------|-------------------------------------|------------------------------------------|
| `10 + 5 * 2`        | `ADICAO(10, MULTIPLICACAO(5, 2))`   | `termo` está abaixo de `soma`            |
| `20 - 5 - 3`        | `SUBTRACAO(SUBTRACAO(20, 5), 3)`    | o laço `{ ... }` de `soma` agrupa à esquerda |
| `(10 + 5) * 2`      | `MULTIPLICACAO(ADICAO(10, 5), 2)`   | parênteses reiniciam em `expressao`      |
| `2 ** 3 ** 2`       | `POTENCIA(2, POTENCIA(3, 2))`       | `potencia` chama `unario` à direita      |
| `-2 ** 2`           | `UNARIO(-, POTENCIA(2, 2))`         | como no Python: `-(2 ** 2)`              |
| `a or b and not c`  | `or(a, and(b, not c))`              | `not` > `and` > `or`                     |

**Associatividade à esquerda sem recursão à esquerda.** Uma regra como
`soma = soma "+" termo` faria um parser descendente recursivo chamar `soma`
infinitamente. A gramática usa repetição (`soma = termo { "+" termo }`), e o
parser monta a árvore à esquerda dentro do laço: cada novo operador vira pai do
resultado acumulado. Para `**`, que é associativo à direita, a regra chama
`unario` (e portanto `potencia` de novo) do lado direito.

## 4. Construções suportadas e fora do escopo

**Suportadas:**

- atribuição simples e composta (`=`, `+=`, `-=`, `*=`, `/=`, `//=`, `%=`, `**=`), inclusive a itens de lista (`v[0] = 1`);
- expressões aritméticas, relacionais e lógicas com precedência do Python;
- literais inteiros, reais, strings (inclusive f-strings, sem analisar o interior), `True`, `False`, `None` e listas;
- chamada de função `f(a, b)`, indexação `v[i]` e acesso a atributo `obj.metodo()`;
- `if` / `elif` / `else`, `while`, `for ... in ...`;
- `def` com parâmetros simples e `return`;
- `pass`, `break`, `continue`;
- blocos indentados ou na mesma linha (`if x: y = 1`) e vários comandos separados por `;`;
- comentários e linhas em branco em qualquer lugar (descartados pelo scanner).

**Fora do escopo** (o parser recusa com uma mensagem explicando que a
construção não faz parte do subconjunto):

- `class`, `import`/`from`, `try`/`except`/`finally`, `with`, `lambda`, `global`, `nonlocal`, `del`, `assert`, `yield`, `raise`, `async`/`await`;
- dicionários e conjuntos (`{}`), tuplas sem parênteses, fatiamento (`v[1:3]`);
- parâmetros com valor padrão, `*args`, `**kwargs` e argumentos nomeados (`f(x=1)`);
- comparações encadeadas (`a < b < c`) e atribuições encadeadas (`a = b = 0`);
- expressão condicional (`x if c else y`) e operador morsa (`:=`).

**Verificações deixadas para a análise semântica (Etapa 5):** `return` fora de
função, `break`/`continue` fora de laço, uso de variável não definida, número
de argumentos de uma chamada e tipos. Elas dependem do significado do
programa, não da sua forma.

## 5. Estratégia: parser descendente recursivo escrito à mão

Cada não terminal da gramática é um **método** com o mesmo nome em
`analisador_sintatico.py` (`programa()`, `se()`, `soma()`, `atomo()` ...). Um
método decide o que fazer olhando o token atual e, em dois casos, o seguinte
(`not in` e `is not`). Não há retrocesso.

**Justificativa da escolha:**

- É a abordagem mais didática: a gramática e o código têm a mesma forma, então o
  estudante consegue ler a regra `soma = termo { ("+"|"-") termo }` e, logo
  abaixo, o método `soma()` que a implementa.
- Permite mensagens de erro específicas para cada regra (o método sabe o que
  estava reconhecendo e o que esperava), em português e com dicas.
- Permite registrar a **pilha de regras** e a **ordem de criação dos nós**, usadas
  na animação “Construção da árvore”.
- Não acrescenta dependências: só a biblioteca padrão do Python, no mesmo
  backend Flask da Etapa 3.

**Alternativas consideradas:** geradores (ANTLR, Lark, PLY) produzem parsers
corretos com menos código, mas esconderiam justamente o que queremos ensinar e
gerariam mensagens de erro genéricas. O módulo `ast` do próprio Python foi
descartado porque reconhece a linguagem inteira (não o subconjunto), produz
mensagens em inglês e não expõe a derivação.

**O que é manual e o que é gerado:** tudo foi escrito à mão; nenhum código é
gerado por ferramenta.

**Por que a gramática é LL(1) na prática:** não há recursão à esquerda (veja a
seção 3) e as alternativas de cada regra começam por tokens diferentes. O único
prefixo comum, entre atribuição e expressão (`x = 1` e `print(x)` começam
ambos por uma expressão), foi resolvido por **fatoração à esquerda**: a regra
`atribuicao_ou_expressao` reconhece a expressão primeiro e só depois decide,
pelo token seguinte, se é uma atribuição.

**Limitações:** cada nível de parênteses atravessa cerca de 12 regras. Para não
estourar a pilha de recursão, o parser recusa (com mensagem) estruturas com mais
de 600 regras aninhadas, o que corresponde a cerca de 50 níveis de parênteses.

## 6. Decisão sobre erros léxicos

**O parser não é executado quando há erros léxicos.** Os erros léxicos
continuam sendo exibidos normalmente, e a resposta traz
`sintatico.executado = false` com a mensagem “Análise sintática não executada:
corrija primeiro os N erro(s) léxico(s)...”. A interface mostra esse aviso no
lugar da árvore.

Justificativa: com um caractere inválido (por exemplo `@`), falta um token na
sequência, e o parser apontaria erros que não existem (por exemplo, “dois
valores sem operador” em `x = 10 @ 2`). Mostrar só o erro real é mais claro para
quem está aprendendo. Testes: `test_erro_lexico_nao_executa_o_parser`
(backend) e `testar_erro_lexico_nao_executa_parser` (interface).

## 7. Tratamento e recuperação de erros

Cada erro sintático informa: linha e coluna, o que foi **encontrado**, o que era
**esperado**, a **regra** da gramática em que o erro ocorreu (com a produção
completa), a mensagem e uma dica. Formato em [`docs/AST.md`](AST.md#erros-sintáticos).

**Recuperação em modo pânico:** quando um comando tem erro, o parser registra o
erro, descarta os tokens até o fim da linha (e o bloco indentado que vier logo
depois, se houver) e continua no próximo comando. Assim:

- vários erros em comandos diferentes aparecem de uma só vez;
- um `if` sem `:` gera **um** erro, e não um erro para cada linha do seu bloco
  (seria um erro em cascata);
- erros dentro de um bloco são tratados no próprio bloco, sem perder o resto do
  programa.

Quando há qualquer erro sintático, a AST não é devolvida (`ast = null`), porque
uma árvore parcial poderia ser confundida com uma árvore válida.

## 8. Exemplos

### Programas válidos

```python
resultado = 10 + 5 * 2
```

```python
def fatorial(n):
    resultado = 1
    while n > 1:
        resultado *= n
        n -= 1
    return resultado

for i in range(5):
    if i % 2 == 0:
        print(i, fatorial(i))
    else:
        print("ímpar")
```

### Programas inválidos (erros sintáticos intencionais)

| Código                   | Mensagem do parser (resumida)                                                     | Regra |
|--------------------------|-----------------------------------------------------------------------------------|-------|
| `x = 5 +`                | linha 1, coluna 8: a expressão terminou logo depois de '+', sem o valor do lado direito | `atomo` |
| `x = 5 + * 3`            | operadores consecutivos: depois de '+' veio '*', mas era esperado um valor          | `atomo` |
| `if x > 1` (sem `:`)     | a linha terminou, mas era esperado ':' ao final da condição do 'if'                | `se` |
| `print(1 2)`             | era esperado ')' para fechar o '(' da chamada de função aberto na linha 1, coluna 6, mas foi encontrado '2' | `chamada` |
| `else:` sem `if`         | 'else' sem um 'if' correspondente                                                 | `se` |
| `def if(x):`             | era esperado um nome para a função depois de 'def', mas foi encontrada a palavra reservada 'if' | `funcao` |
| `x = 5 6`                | era esperado o fim da linha depois do comando que termina em '5', mas foi encontrado '6' | `linha_simples` |
| `if x:` + linha sem recuo | era esperado um bloco indentado do 'if' da linha 1                               | `bloco` |
| `if x:` no fim do código | o código terminou antes de o bloco do 'if' da linha 1 receber algum comando        | `bloco` |
| `    y = 2` sem bloco    | indentação inesperada: ... nenhum bloco foi aberto com ':' na linha anterior       | `bloco` |
| `5 = x`                  | o lado esquerdo de uma atribuição não pode ser um valor literal                   | `atribuicao_ou_expressao` |
| `import math`            | a construção 'import' não faz parte do subconjunto de Python desta etapa           | `comando` |

O exemplo **Erros sintáticos** da interface reúne quatro desses erros em um
mesmo programa, para mostrar a recuperação de erros.
