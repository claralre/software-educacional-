# Tutorial — Entendendo as Análises Léxica, Sintática e Semântica com o Software Educacional

Este tutorial é destinado a estudantes que estão começando a estudar
compiladores. Ele leva cerca de 15 minutos.

## Antes de começar

Suba a aplicação (veja o README) e abra `http://localhost:3000`. A
interface funciona no computador e no celular.

## Passo 1 — Seu primeiro token

1. No seletor **Exemplos de programas**, escolha **Variável**. O campo de
   código recebe `idade = 21`.
2. Clique em **Analisar código**.
3. Na aba **Tabela de tokens**, observe:

| Tipo              | Lexema  | Linha | Coluna |
|-------------------|---------|-------|--------|
| IDENTIFICADOR     | `idade` | 1     | 1      |
| OPERADOR          | `=`     | 1     | 7      |
| LITERAL_INTEIRO   | `21`    | 1     | 9      |
| NOVA_LINHA        | (fim)   | 1     | 11     |
| FIM               | (vazio) | 1     | 11     |

**Pergunta:** os espaços entre `idade`, `=` e `21` viraram tokens? Por quê?

> O **lexema** é o texto exato (`idade`); o **token** é o par
> `<IDENTIFICADOR, idade>`. Espaços entre tokens são descartados.

## Passo 2 — Veja o scanner trabalhando

1. Escolha o exemplo **Função com comentários** e clique em **Analisar código**.
2. Abra a aba **Passo a passo** e clique em **▶|** (próximo passo) várias vezes.
3. Repare que:
   * o trecho em amarelo é o lexema que acabou de ser reconhecido;
   * o texto em cinza ainda não foi lido;
   * o comentário `# Calcula...` é lido, mas **não** vira token;
   * depois de `def media(a, b):` surge `INDENTA`, porque a linha
     seguinte começa com 4 espaços — é assim que Python marca um bloco.
4. Clique em **▶ Reproduzir** e ajuste a velocidade para ver o processo inteiro.

**Pergunta:** quantos tokens `DEDENTA` aparecem e onde?

## Passo 3 — Palavras reservadas × identificadores

Digite:

```python
if iffy:
    return True
```

Observe no **Código colorido** (toque em cada palavra):

* `if`, `return` e `True` são `PALAVRA_RESERVADA`;
* `iffy` é `IDENTIFICADOR`, embora comece com `if`. O scanner lê a
  palavra inteira (`iffy`) antes de consultar a tabela de palavras
  reservadas.

## Passo 4 — Casamento mais longo

Digite `x **= 2` e veja que `**=` é **um** token, não três.
Agora digite `a===b`: o scanner produz `==` e depois `=`.

> Regra do **casamento mais longo** (*maximal munch*): o scanner sempre
> escolhe o maior lexema possível.

## Passo 5 — Erros léxicos

1. Escolha o exemplo **Erros léxicos** e analise.
2. A seção **Erros léxicos** lista 5 problemas, cada um com linha, coluna
   e uma dica. Clique em um erro para vê-lo destacado no código.
3. Observe que os tokens válidos continuam aparecendo: o scanner **não
   para** no primeiro erro.

**Pergunta:** `1nome = "Ana"` gera erro léxico, mas `= = if` não gera.
Por quê?

> `1nome` não corresponde a nenhum padrão de token. Já `= = if` é formado
> por tokens válidos em uma ordem inválida — isso é um erro **sintático**,
> que será detectado na Etapa 4 pelo parser.

## Passo 6 — Do código à sequência de tokens

Abra a aba **Sequência**. À esquerda está o código como você escreveu; à
direita, o que a próxima fase (o parser) receberá. Repare que comentários
e linhas em branco desaparecem.

Na aba **Resumo**, veja quantos tokens de cada categoria foram encontrados
e a lista de identificadores distintos — que, nas próximas etapas, formará
a **tabela de símbolos**.

## Passo 7 — Da sequência de tokens à árvore (Etapa 4)

1. Escolha o exemplo **Precedência de operadores** e analise.
2. Na seção **Análise sintática**, aba **Árvore (AST)**, observe a primeira
   atribuição: em `10 + 5 * 2`, o nó **Multiplicação** fica **abaixo** do nó
   **Adição**. Quem está mais fundo na árvore é calculado primeiro.
3. Toque no nó **Multiplicação (\*)**: o trecho `5 * 2` é destacado no código e
   o painel mostra a regra da gramática que reconheceu o nó (`termo`).
4. Compare `20 - 5 - 3` (a primeira subtração fica embaixo, à esquerda) com
   `2 ** 3 ** 2` (a segunda potência fica embaixo, à direita).

**Pergunta:** por que `(10 + 5) * 2` produz uma árvore diferente de `10 + 5 * 2`,
se os tokens são quase os mesmos?

## Passo 8 — Veja o parser montando a árvore

1. Abra a aba **Construção da árvore** e clique em **▶|** algumas vezes.
2. Acompanhe a **pilha de regras**: para ler um simples número, o parser
   atravessa `expressao › ou › e › nao › comparacao › soma › termo › unario ›
   potencia › primario › atomo`. É assim que a gramática define a precedência.
3. Marque **Parar só quando um nó é criado** e veja que a árvore cresce **de
   baixo para cima**: primeiro as folhas, depois os nós que as ligam.
4. Abra a aba **Árvore de derivação** e compare a quantidade de nós com a da AST.

## Passo 9 — Erros sintáticos

1. Escolha o exemplo **Erros sintáticos** e analise.
2. Leia cada erro: ele diz o que foi **encontrado**, o que era **esperado** e
   qual **regra da gramática** foi violada.
3. Repare que o `if` sem `:` gera **um** erro só, e não um erro para cada linha
   do seu bloco: o parser se recupera e continua.
4. Se o assistente de IA estiver ligado, clique em **✨ Entender erro com IA**.

**Pergunta:** por que `x = 10 @ 2` mostra um erro léxico, mas nenhum erro
sintático?

## Passo 10 — A tabela de símbolos (Etapa 5)

1. Escolha o exemplo **Escopos e tabela de símbolos** e analise.
2. Abaixo do resultado, veja a faixa **Léxica → Sintática → Semântica**: as três
   fases passaram.
3. Na seção **Análise semântica**, a tabela aparece dividida em **escopos**: o global,
   o da função `dobro` e o das funções embutidas (`range`, `print`).
4. Clique na linha do `total` do **escopo global**: a definição fica verde e os usos,
   azuis, no código. Repare que a variável `i` do `for` está no escopo global, porque
   em Python o `for` **não** cria escopo.
5. Agora veja o `total` dentro da função: ele tem a marca **sombreia**. É outra
   variável, local da função, que esconde o `total` global.
6. Clique em **🌳 Ver o nó na AST** e veja de qual nó da árvore o símbolo veio.

**Pergunta:** por que o tipo do `total` global aparece como `int → desconhecido`?

## Passo 11 — Erros semânticos

1. Escolha o exemplo **Erros semânticos** e analise. Não há erro léxico nem
   sintático: todas as frases estão “bem escritas”, mas algumas não fazem sentido.
2. Leia cada erro: a **regra** violada, o **porquê**, **como corrigir** e o erro que o
   **Python mostraria** ao executar (`NameError`, `TypeError`…).
3. Clique no erro de `idad`: o trecho é destacado e o sistema pergunta “Você quis
   dizer 'idade'?”.
4. Abra a aba **Regras semânticas** e encontre a regra do erro selecionado.
5. Digite `x = 1` e, na linha de baixo, `x = "a"`: aparece um **aviso**, não um erro.
   Python permite mudar o tipo de uma variável, mas isso costuma confundir.

**Pergunta:** `x = 5 +` mostra erro sintático e nenhum erro semântico. Por quê?

## Exercícios

1. Escreva um programa que gere ao menos um token de cada categoria.
2. Escreva uma linha que produza exatamente 3 erros léxicos diferentes.
3. Por que `3.14.15` é um erro, mas `3.14 . 15` não é (lexicamente)?
4. Crie um bloco `if` dentro de um `while` e conte os tokens `INDENTA` e `DEDENTA`.
5. Consulte o **Escopo léxico suportado** no fim da página e encontre um
   operador do Python que **não** faz parte do subconjunto.
6. Escreva uma expressão cuja AST tenha uma **Potência** acima de uma **Adição**.
7. Escreva um programa com três erros sintáticos diferentes e confira se o parser
   aponta os três.
8. Na aba **Gramática**, encontre a regra que impede `a < b < c`.
9. Escreva um programa sem erros em que um mesmo nome apareça em dois escopos
   diferentes da tabela de símbolos.
10. Escreva uma linha com erro semântico de tipo e corrija-a de duas formas
    diferentes, seguindo a sugestão do sistema.
11. Em `x = 1`, `def f():`, `print(x)`, `x = 2`, `f()`, o Python dá erro mesmo
    existindo um `x` global. Use o sistema para descobrir por quê.
