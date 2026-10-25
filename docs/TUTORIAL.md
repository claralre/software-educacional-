# Tutorial — Entendendo a Análise Léxica com o Software Educacional

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

## Exercícios

1. Escreva um programa que gere ao menos um token de cada categoria.
2. Escreva uma linha que produza exatamente 3 erros léxicos diferentes.
3. Por que `3.14.15` é um erro, mas `3.14 . 15` não é (lexicamente)?
4. Crie um bloco `if` dentro de um `while` e conte os tokens `INDENTA` e `DEDENTA`.
5. Consulte o **Escopo léxico suportado** no fim da página e encontre um
   operador do Python que **não** faz parte do subconjunto.
