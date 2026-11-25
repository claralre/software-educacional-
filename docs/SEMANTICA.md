# Análise semântica (Etapa 5)

O scanner reconhece as palavras; o parser verifica se elas formam frases
válidas e monta a AST. A **análise semântica** verifica se o programa **faz
sentido**: se cada nome recebeu valor antes de ser usado, se os tipos combinam
nas operações, se as chamadas passam o número certo de argumentos, e assim por
diante. Ela percorre a AST e monta a **tabela de símbolos**.

Implementação: [`backend/analisador_semantico.py`](../backend/analisador_semantico.py).
Testes: [`backend/test_semantico.py`](../backend/test_semantico.py).

## 1. Adaptação ao Python (decisão de projeto)

O enunciado da etapa usa exemplos de C e Java (`int x = 10;`), linguagens com
**declarações** e **tipos declarados**. O subconjunto deste projeto é Python,
que não tem nenhum dos dois. As regras clássicas foram adaptadas ao que
significam em Python:

| Regra clássica (C/Java) | Equivalente em Python | O que o Python faria ao executar |
|---|---|---|
| Identificador declarado antes do uso | Nome **recebe valor** antes do uso (`total = 0`) | `NameError` |
| Tipo da expressão compatível com o tipo declarado | Não há tipo declarado: o tipo de cada variável é **inferido** dos valores, e o que se verifica é a compatibilidade dos **operandos** (`"a" + 1`) | `TypeError` |
| Redeclaração no mesmo escopo | Dar novo valor é permitido; repetir um **parâmetro** não | `SyntaxError` (parâmetro repetido) |
| Escopo de bloco `{ }` | Blocos de `if`, `while` e `for` **não** criam escopo; só funções criam | — |
| Variável local esconde a global | Igual (sombreamento), mais uma regra própria do Python: um nome que recebe valor em qualquer ponto da função é local na função **inteira** | `UnboundLocalError` |
| Condição do `if`/`while` deve ser booleana | **Não se aplica**: em Python qualquer valor pode ser condição (`if lista:`). Não foi implementada de propósito | — |

Essas diferenças são exibidas ao estudante na interface (seção “O que é
análise semântica?”) e são, por si, conteúdo didático: mostram que as regras
semânticas dependem da linguagem.

## 2. Escopo da análise

### 2.1. Regras implementadas

Erros (o programa falharia ao executar):

| Código | O que verifica | Exemplo inválido | Python |
|---|---|---|---|
| `IDENTIFICADOR_NAO_DEFINIDO` | Nome usado sem ter recebido valor antes (ou nunca) | `print(totl)` | NameError |
| `ATRIBUICAO_COMPOSTA_SEM_VALOR` | `x += 1` sem `x` ter valor | `cont += 1` | NameError |
| `VARIAVEL_LOCAL_SEM_VALOR` | Variável local lida antes de receber valor na função | `x = 1` / `def f():` / `print(x)` / `x = 2` | UnboundLocalError |
| `TIPOS_INCOMPATIVEIS` | Operador aritmético com tipos que ele não aceita | `"idade: " + 21` | TypeError |
| `OPERANDO_INVALIDO` | `-x` / `+x` com valor que não é número | `-"a"` | TypeError |
| `COMPARACAO_INVALIDA` | `<`, `>`, `<=`, `>=` entre tipos diferentes | `"a" < 3` | TypeError |
| `NAO_ITERAVEL` | `for` ou `in` sobre número, `bool` ou `None` | `for i in 10:` | TypeError |
| `NAO_INDEXAVEL` | `[ ]` em valor sem itens | `n = 5` / `n[0]` | TypeError |
| `INDICE_INVALIDO` | Índice que não é inteiro | `v["a"]` | TypeError |
| `ITEM_IMUTAVEL` | Alterar uma letra de um texto | `t[0] = "x"` | TypeError |
| `NAO_CHAMAVEL` | Chamar com `( )` algo que não é função | `x = 3` / `x()` | TypeError |
| `ARGUMENTOS_INCORRETOS` | Número de argumentos diferente do número de parâmetros (funções do programa e embutidas) | `def f(a, b)` / `f(1)` | TypeError |
| `ARGUMENTO_INVALIDO` | `len()` sem coleção, `range()` sem inteiros | `len(5)` | TypeError |
| `PARAMETRO_DUPLICADO` | Dois parâmetros com o mesmo nome | `def g(a, a):` | SyntaxError |
| `RETORNO_FORA_DE_FUNCAO` | `return` fora de função | `return 1` | SyntaxError |
| `FORA_DE_LACO` | `break`/`continue` fora de laço | `break` | SyntaxError |

As três últimas o Python acusa ao **compilar** (por isso aparecem como
`SyntaxError`), mas não são erros de gramática: a gramática livre de contexto
aceita `return` em qualquer lugar. Elas dependem do **contexto**, por isso são
verificadas aqui. (Na Etapa 4 elas já estavam listadas como “deixadas para a
análise semântica”, em `docs/GRAMATICA.md`.)

Avisos (algo permitido, mas arriscado; não reprovam o programa):

| Código | Situação |
|---|---|
| `POSSIVELMENTE_NAO_DEFINIDA` | O nome só recebe valor dentro de um `if` sem `else`, de um laço, ou mais adiante no mesmo laço |
| `MUDANCA_DE_TIPO` | A variável recebe valores de tipos diferentes (`x = 1`, depois `x = "a"`) |
| `SOMBREIA_EMBUTIDA` | Dar valor a um nome de função embutida (`list = [1]`) |

### 2.2. Regras não implementadas (e por quê)

- **Condição booleana em `if`/`while`**: não se aplica ao Python (qualquer valor
  serve de condição).
- **Tipo de retorno compatível com o tipo declarado da função**: Python não
  declara tipos de retorno (anotações de tipo não fazem parte do subconjunto). O
  tipo de retorno é só **inferido** e exibido.
- **Tipos dos parâmetros**: um parâmetro recebe qualquer valor na chamada, então
  seu tipo fica `desconhecido`, e as operações com ele não são verificadas.
- **Fluxo de controle completo**: a análise de “recebe valor com certeza” trata
  `if/elif/else` e laços de forma simples; não analisa, por exemplo, se toda
  função retorna em todos os caminhos, nem código inalcançável.
- **Métodos e atributos** (`lista.append`, `texto.upper()`): o objeto é
  verificado (precisa ter valor), mas a existência do atributo não.
- **Tipos dos elementos de listas**: `v[0]` tem tipo `desconhecido`.
- **Erros que dependem dos valores** em execução: divisão por zero,
  `int("abc")`, índice fora da lista.
- `global`/`nonlocal`, classes, módulos e outras construções que já estavam fora
  da gramática.

Quando o tipo é `desconhecido`, nenhuma regra de tipo é aplicada: é preferível
deixar de apontar um erro a apontar um erro que talvez não exista.

## 3. Estratégia: percurso da AST em duas fases

Abordagem **tree walk**: um método por tipo de nó da AST, com a tabela de
símbolos como estado. Python, porém, exige uma **pré-coleta**:

1. **Pré-coleta por escopo** (`_coletar`): antes de percorrer um escopo, o
   analisador anota todos os nomes que recebem valor nele e as assinaturas das
   funções. É assim que o próprio Python decide, antes de executar, quais nomes
   são **locais** de uma função, e é o que permite detectar o `UnboundLocalError`.
2. **Percurso em ordem do texto** (`_comando`, `_expressao`): verifica cada uso,
   infere tipos e preenche a tabela.

Detalhes importantes:

- **Atribuição:** o lado direito é analisado **antes** de o nome ser definido,
  como na execução (`x = x + 1` sem `x` anterior é erro).
- **Atribuição com certeza ou “talvez”:** para `if/elif/else`, um nome passa a
  “ter valor com certeza” só se recebe valor em **todos** os ramos (com `else`);
  senão, “talvez”. Em laços, o que recebe valor no corpo vira “talvez” depois do
  laço (o laço pode não repetir nenhuma vez). Usar um nome “talvez” gera o aviso
  `POSSIVELMENTE_NAO_DEFINIDA`, não um erro.
- **Funções:** o corpo é percorrido na definição, num escopo novo. Um nome do
  escopo global usado dentro de uma função é aceito mesmo se receber valor
  **depois** do `def`, porque o corpo só executa na chamada (comportamento
  real do Python). Já no escopo global vale a ordem do texto: chamar `f()` antes
  do `def f` é erro.
- **Laços:** `break`/`continue` são verificados com a profundidade de laços; uma
  função começa com profundidade zero.
- **Sem erros em cascata:** cada nome indefinido é apontado **uma vez por
  escopo**, e um valor de tipo `desconhecido` não gera erros de tipo adicionais.
  Assim `a = b + 1` / `c = b * "x"` gera um único erro.

### Inferência de tipos

| Expressão | Tipo |
|---|---|
| `21`, `3.14`, `"Ana"`, `True`, `None`, `[1, 2]` | `int`, `float`, `str`, `bool`, `None`, `list` |
| `int ± int`, `int * int`, `int // int`, `int ** int` | `int` (com `float` no meio: `float`) |
| `a / b` (números) | `float` |
| `str + str`, `list + list` | `str`, `list` |
| `str * int`, `list * int` | `str`, `list` |
| comparações, `not` | `bool` |
| `len()`, `input()`, `int()`, `str()`, `range()`… | `int`, `str`, `int`, `str`, `range`… |
| chamada de função do programa | o tipo de retorno inferido (`return 1` → `int`), se único |
| parâmetro, item de lista, atributo | `desconhecido` |

## 4. Tabela de símbolos

### 4.1. Organização

Lista de símbolos, cada um ligado a um **escopo**. Os escopos formam uma
cadeia: **função → funções que a envolvem → global → embutido**. A busca de um
nome começa no escopo mais interno e sobe pela cadeia. Escopos:

- **global**: nomes definidos fora de qualquer função;
- **um por função** (`def`), com seus parâmetros e variáveis locais;
- **embutido**: funções do Python usadas pelo programa (`print`, `len`,
  `range`…); só aparecem na tabela se forem usadas.

### 4.2. Atributos de cada símbolo

| Campo | Descrição |
|---|---|
| `nome` | O nome no código |
| `categoria` | `variavel`, `funcao`, `parametro` ou `embutida` |
| `tipo` | Tipo inferido mais recente (`int`, `str`, `função`, `desconhecido`…) |
| `tipos` | Todos os tipos conhecidos que o nome recebeu, em ordem |
| `escopo`, `escopo_rotulo` | Nome do escopo (`global`, nome da função, `embutido`) e rótulo legível |
| `linha`, `coluna`, `linha_fim`, `coluna_fim` | Posição da **primeira** definição (para funções, a posição do nome depois do `def`) |
| `no_id` | Id do nó da AST que definiu o símbolo |
| `inicializado` | Sempre `true` para nomes do programa: em Python, definir é dar valor |
| `usado`, `usos` | Se é usado e onde (posição e id do nó de cada uso) |
| `atribuicoes` | Quantas vezes recebe valor |
| `parametros`, `retorno` | Para funções: nomes dos parâmetros e tipo de retorno inferido |
| `argumentos` | Para embutidas: quantos argumentos aceitam |
| `sombreia` | Quando um nome local esconde um nome de fora (ex.: `total do escopo global`) |

### 4.3. Exemplo

```python
limite = 3
total = 0

def dobro(x):
    total = x * 2  # variável local: sombreia o total global
    return total

for i in range(limite):
    total += dobro(i)
print("Total:", total)
```

| Escopo | Nome | Categoria | Tipo | Definido em | Observação |
|---|---|---|---|---|---|
| global | `limite` | variável | `int` | linha 1, coluna 1 | |
| global | `total` | variável | `int → desconhecido` | linha 2, coluna 1 | depois de `+= dobro(i)`, o tipo não é mais conhecido |
| global | `dobro` | função | `função(x) → desconhecido` | linha 4, coluna 5 | |
| global | `i` | variável | `int` | linha 8, coluna 5 | variável do `for` sobre `range` |
| função dobro | `x` | parâmetro | `desconhecido` | linha 4, coluna 11 | |
| função dobro | `total` | variável | `desconhecido` | linha 5, coluna 5 | **sombreia** o `total` global |
| embutido | `range`, `print` | função embutida | | | |

Repare que `i` está no escopo **global**: o `for` não cria escopo em Python.

### 4.4. Apresentação na interface

A tabela aparece **agrupada por escopo** (um cartão por escopo, com o escopo de
função recuado e outra cor de borda). Colunas: Nome, Categoria, Tipo (inferido),
Definido em, Usos. Ao selecionar um símbolo:

- a **definição** é destacada em verde e cada **uso** em azul tracejado, no
  próprio código (não depende só de cor: estilos de borda diferentes);
- o painel de detalhe explica o tipo (inferido, ou por que é desconhecido), o
  escopo e o sombreamento;
- o botão **🌳 Ver o nó na AST** abre a AST com o nó correspondente selecionado;
- o botão **✨ Explicar este símbolo com IA** pede uma explicação ao assistente.

## 5. Erros léxicos e sintáticos: a análise semântica não é executada

Se há erros léxicos ou sintáticos, a análise semântica **não roda**: não há AST,
ou ela estaria incompleta, e os diagnósticos seriam enganosos. A resposta traz
`semantico.executado = false` e uma mensagem dizendo o motivo, e a interface
avisa o estudante. Os erros léxicos e sintáticos continuam aparecendo
normalmente. Testado em `test_app.py` (`TestAnaliseSemantica`) e
`tests/test_interface.py` (`testar_tres_tipos_de_erro_e_semantica_nao_executada`).

## 6. Formato do diagnóstico

```json
{
  "tipo": "ERRO_SEMANTICO",
  "regra": "IDENTIFICADOR_NAO_DEFINIDO",
  "titulo": "Nome usado sem ter recebido valor",
  "linha": 3, "coluna": 7, "linha_fim": 3, "coluna_fim": 10,
  "mensagem": "Erro semântico na linha 3, coluna 7: 'totl' foi usado, mas não recebe valor em nenhum ponto do programa.",
  "explicacao": "Em Python, uma variável só passa a existir quando recebe um valor (por exemplo, total = 0). Usar um nome antes disso, ou que nunca recebeu valor, é um erro: o programa não sabe a que o nome se refere.",
  "sugestao": "Você quis dizer 'total'?",
  "erro_python": "NameError",
  "no_id": 9
}
```

Avisos têm o mesmo formato, com `"tipo": "AVISO_SEMANTICO"` e mensagem
começando com “Aviso”. A sugestão de nome parecido (“Você quis dizer…?”) usa a
semelhança entre o nome errado e os nomes visíveis naquele ponto.

## 7. Contrato da API

`POST /api/analisar` mantém todos os campos das Etapas 3 e 4 e acrescenta o
bloco `semantico`:

```json
"semantico": {
  "executado": true,
  "sucesso": false,
  "mensagem": "Análise semântica concluída com 1 erro(s) semântico(s).",
  "tabela_simbolos": [ { "nome": "x", "categoria": "variavel", "tipo": "int", "escopo": "global", "linha": 1, "coluna": 1, "...": "..." } ],
  "escopos": [ { "nome": "global", "rotulo": "Escopo global", "tipo": "global", "pai": null, "total_simbolos": 2 } ],
  "erros": [ { "tipo": "ERRO_SEMANTICO", "regra": "IDENTIFICADOR_NAO_DEFINIDO", "...": "..." } ],
  "avisos": [],
  "resumo": { "total_simbolos": 3, "total_erros": 1, "total_avisos": 0,
              "por_categoria": { "variavel": 2, "funcao": 0, "parametro": 0, "embutida": 1 } }
}
```

- `sucesso` é `true` quando não há **erros** (avisos não reprovam).
- O campo se chama `tabela_simbolos` (e não `tabelaSimbolos`, como no exemplo do
  enunciado) para seguir o padrão em português com `_` já usado no contrato.
- Erros no código do estudante continuam com HTTP 200; entradas inválidas, 400 ou
  413; falha interna, 500 sem detalhes.

`GET /api/semantica` devolve as regras (código, título, gravidade, explicação,
erro do Python) e as funções embutidas reconhecidas; a interface usa essa lista
na aba **Regras semânticas**.

## 8. Interface

- **Fases da análise:** abaixo do resultado, uma faixa mostra
  `✔ Léxica → ✔ Sintática → ✖ Semântica: 2 erro(s)`, com símbolo, texto e estilo
  de borda diferentes para “ok”, “aviso”, “erro” e “não executada”.
- **Distinção entre os três tipos de erro:** rótulos com texto próprio
  (`ERRO LÉXICO`, `ERRO SINTÁTICO`, `ERRO SEMÂNTICO`, `AVISO SEMÂNTICO`), cores
  diferentes e, nos avisos, borda tracejada: a diferença não depende só de cor.
- **Cada erro semântico mostra:** mensagem com linha e coluna, a **regra**
  (título e código), **por quê** (explicação em linguagem acessível), **como
  corrigir** (sugestão), **o erro que o Python mostraria** ao executar e os
  botões **Ver o nó na AST** e **Entender erro com IA**. Clicar no erro destaca o
  trecho no código e a regra na aba **Regras semânticas**.
- **Exemplos novos:** “Escopos e tabela de símbolos” e “Erros semânticos”.

## 9. Novidade desta etapa

Considerando os dez estudos analisados no artigo:

1. **Cada erro semântico é ligado ao erro real do Python** (`NameError`,
   `UnboundLocalError`, `TypeError`, `SyntaxError`) e essa ligação é **conferida
   automaticamente executando o próprio Python** (`TestOraculoPython`): o
   estudante vê que a regra não é arbitrária, é o que aconteceria ao rodar o
   programa.
2. **Explicação da regra violada + sugestão de correção** em cada diagnóstico,
   incluindo “Você quis dizer…?” para nomes digitados errado.
3. **Tabela de símbolos interativa ligada ao código e à AST**: definição e usos
   destacados no código; botão que abre o nó na AST.
4. **Regras semânticas próprias do Python explicadas**: escopo só por função,
   variável local que esconde a global (`UnboundLocalError`), tipos inferidos.
5. **IA** que explica erros semânticos e símbolos com os dados reais do analisador
   (diferencial opcional).

Tabela de símbolos e análise semântica já existem em ferramentas analisadas
(Borela et al., 2025; Koitz-Hristov et al., 2025; Alaküla et al., 2025). Os
pontos acima **não foram identificados** nos dez estudos analisados; não se
afirma que sejam inéditos.

**Pergunta de avaliação ligada à novidade** (formulário da avaliação por pares,
escala de 1 a 5):

- **D6.** A explicação da regra semântica violada, com a sugestão de correção e o
  erro que o Python mostraria, ajudou você a entender o erro.
- **D7.** Destacar no código onde cada símbolo é definido e usado ajudou você a
  entender o que é escopo.

## 10. Testes

| Arquivo | Testes | O que cobre |
|---|---|---|
| `backend/test_semantico.py` | 65 | tabela de símbolos (tipos, escopos, usos, sombreamento, blocos sem escopo), cada regra com caso válido e inválido, avisos, formato e coerência dos campos, ligação com a AST e com os tokens, bordas, programa grande e o **oráculo Python** |
| `backend/test_app.py` (`TestAnaliseSemantica`) | 10 | contrato, erro semântico com tabela parcial, aviso, semântica não executada com erro léxico ou sintático, entrada vazia, falha interna sem detalhes, `/semantica` |
| `backend/test_ia.py` | 4 novos | contexto da IA para erro semântico, aviso e símbolo |
| `frontend/test_interface.js` | 11 novos | agrupamento por escopo, destaque de definição e usos, escape de HTML, fases, rótulos dos três tipos de erro |
| `tests/test_interface.py` | 5 novos | tabela de símbolos, erros semânticos, três tipos de erro, consistência com tokens, celular |

```bash
docker compose run --rm --build backend python -m unittest -v test_semantico
```

Resultados em `docs/RELATORIO_TESTES.md`.

## 11. Limitações conhecidas

- Tipos de parâmetros, itens de lista e atributos são `desconhecido`, então erros
  de tipo envolvendo esses valores não são detectados.
- A análise de “recebe valor com certeza” é simples (seção 3); casos com
  `break`, `return` no meio de ramos ou laços infinitos podem gerar avisos a
  mais ou a menos.
- Um nome global usado dentro de uma função é aceito se receber valor em
  qualquer ponto do programa, mesmo que a função seja chamada antes disso.
- As funções embutidas reconhecidas são as listadas em `GET /api/semantica`.

## 12. Relação com a Etapa 6

A Etapa 6 (representação semântica e experiência didática) pode partir de:
`no_id` em cada símbolo e diagnóstico (para anotar a AST com tipos e símbolos),
a cadeia de escopos em `escopos` (para desenhar a árvore de escopos) e os tipos
inferidos (para uma AST anotada com o tipo de cada expressão).
