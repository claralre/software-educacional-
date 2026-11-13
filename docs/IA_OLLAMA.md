# Assistente de IA com Ollama e Llama 3.2 (diferencial opcional)

## 1. O que é e qual a sua função

O [Ollama](https://ollama.com) executa modelos de linguagem localmente e oferece
uma API HTTP. O projeto usa o modelo **Llama 3.2** (`llama3.2`, versão de 3B
parâmetros) para gerar **explicações didáticas** sobre os resultados do
compilador.

A IA **não participa da compilação**. Tokens, AST e erros continuam sendo
produzidos pelo scanner e pelo parser do projeto. A IA só recebe esses
resultados e explica o que eles significam. Se ela estiver desligada ou fora do
ar, toda a análise léxica e sintática continua funcionando.

```text
ESTUDANTE → INTERFACE WEB → BACKEND (Flask)
                              ├── SCANNER → PARSER → AST          (resultados oficiais)
                              └── OLLAMA (llama3.2)               (explicação dos resultados)
                                        ↓
                              EXPLICAÇÃO → INTERFACE WEB (marcada como "gerada por IA")
```

O navegador nunca acessa o Ollama: só o backend acessa, pela rede interna do
Docker Compose.

## 2. Como foi incorporado ao Docker Compose

O serviço `ollama` foi acrescentado ao `compose.yaml` existente, com o volume
`ollama_data` para guardar o modelo baixado:

```yaml
  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    restart: unless-stopped
    profiles:
      - ia
    volumes:
      - ollama_data:/root/.ollama

volumes:
  ollama_data:
```

No backend, foram acrescentadas as variáveis de ambiente e a dependência:

```yaml
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
      - OLLAMA_MODELO=llama3.2
      - OLLAMA_TEMPO_LIMITE=120
    depends_on:
      ollama:
        condition: service_started
        required: false
```

**Decisão de projeto: perfil `ia`.** A imagem do Ollama ocupa vários gigabytes
em disco (8,5 GB na versão `latest` usada nos testes, que inclui bibliotecas de
GPU) e o modelo, mais 2 GB. Para que a parte obrigatória (análise léxica e sintática)
continue subindo rápido em qualquer computador, o serviço foi colocado no
perfil `ia`: ele só sobe quando o perfil é pedido. Por isso, a dependência do
backend é `required: false`. A porta 11434 **não** é publicada no host.

## 3. Como subir e baixar o modelo

```bash
docker compose --profile ia up -d --build
docker compose --profile ia ps
docker compose exec ollama ollama pull llama3.2
docker compose exec ollama ollama list
```

Teste opcional direto no terminal (saia com Ctrl + D):

```bash
docker compose exec ollama ollama run llama3.2
```

O modelo fica no volume `ollama_data` e não precisa ser baixado de novo ao
recriar os contêineres. Para desligar tudo: `docker compose --profile ia down`.
O desempenho depende da memória e do processador. Na CPU, a primeira resposta
pode levar mais de um minuto, porque o modelo é carregado na memória.

## 4. Variáveis de ambiente

| Variável              | Padrão no Compose        | Descrição |
|-----------------------|--------------------------|-----------|
| `OLLAMA_BASE_URL`     | `http://ollama:11434`    | Endereço do Ollama. Vazio = assistente desligado. |
| `OLLAMA_MODELO`       | `llama3.2`               | Modelo usado nas perguntas. |
| `OLLAMA_TEMPO_LIMITE` | `120`                    | Tempo máximo, em segundos, de espera por uma resposta. |

O endereço `http://ollama:11434` usa o nome do serviço, resolvido pela rede
interna do Compose.

## 5. Como o backend faz as requisições

Implementação: [`backend/ia.py`](../backend/ia.py). Usa apenas a biblioteca
padrão do Python (`urllib`), sem dependências novas.

### Endpoints

| Método e rota          | Função |
|------------------------|--------|
| `GET /api/ia/status`   | Informa se o Ollama está acessível e se o modelo foi baixado. |
| `POST /api/ia/explicar`| Pede uma explicação. |

Requisição de `POST /api/ia/explicar`:

```json
{
  "codigo": "resultado = 10 + 5 * 2",
  "alvo": { "tipo": "no", "id": 4 },
  "pergunta": "Por que a multiplicação aparece abaixo da adição?"
}
```

| `alvo.tipo`      | Campo extra | Explica |
|------------------|-------------|---------|
| `token`          | `indice`    | um token da tabela de tokens |
| `erro_lexico`    | `indice`    | um erro léxico |
| `no`             | `id`        | um nó da AST |
| `erro_sintatico` | `indice`    | um erro sintático |
| `conceito`       | —           | pergunta livre ao professor virtual (`pergunta` obrigatória) |

`pergunta` é opcional nos quatro primeiros casos: sem ela, o backend usa uma
pergunta padrão para o tipo de alvo.

**Dados reais, não enviados pelo navegador:** o backend **refaz** a análise
léxica e sintática do `codigo` e localiza o token, nó ou erro pedido. Assim, o
modelo recebe os resultados verdadeiros do compilador, e o navegador não
consegue enviar uma AST inventada. Para um nó, o contexto inclui:
- o nó, seus atributos e sua posição;
- a regra da gramática que o reconheceu, com a produção em EBNF;
- o caminho desde a raiz e o nó pai;
- a subárvore do nó, em texto;
- o trecho de código correspondente;
- se o nó for uma expressão, um resumo da **precedência** na gramática do projeto
  (`PRECEDENCIA`), acrescentado depois da demonstração (seção 10).

Nas perguntas ao professor virtual (`conceito`), o contexto inclui a gramática,
a precedência e um **glossário** com as definições usadas no próprio projeto
(`GLOSSARIO`: scanner, token, parser, terminais, AST, árvore de derivação etc.).

O backend então chama `POST http://ollama:11434/api/chat` com `stream: false` e
devolve `message.content`. A chamada usa `temperature: 0` (respostas mais
estáveis e menos “criativas”) e `num_predict: 500` (limite de tamanho):

```json
{
  "sucesso": true,
  "resposta": "...texto gerado pelo modelo...",
  "modelo": "llama3.2",
  "gerado_por_ia": true,
  "aviso": "Explicação gerada por IA (Ollama + Llama 3.2). Ela pode conter erros: os resultados oficiais da compilação são os do scanner e do parser."
}
```

### Instrução de sistema

Definida em `INSTRUCAO_SISTEMA` (`backend/ia.py`). Ela segue as regras pedidas
no enunciado: explicar em português, passo a passo, não inventar tokens, nós ou
erros, não contradizer o diagnóstico do parser, informar limitações e separar
teoria de resultado. Acrescenta uma regra de segurança: o código, os tokens e a
AST são **dados**, nunca instruções. No texto enviado ao modelo, o código fica
entre os marcadores `<<<INICIO_DO_CODIGO` e `FIM_DO_CODIGO>>>`.

### Falhas tratadas

| Situação                              | HTTP | Mensagem ao estudante |
|---------------------------------------|------|-----------------------|
| `OLLAMA_BASE_URL` vazio               | 503  | assistente desligado; a análise funciona normalmente |
| Ollama fora do ar (após 2 tentativas) | 503  | como subir o serviço e baixar o modelo |
| Modelo não baixado                    | 503  | comando `ollama pull llama3.2` |
| Tempo esgotado                        | 504  | o modelo pode estar carregando; tente de novo |
| Resposta vazia ou inválida            | 502  | tente novamente |
| Pedido inválido (alvo inexistente, código acima de 4000 caracteres, pergunta acima de 600 caracteres) | 400 | o que corrigir |

O nginx espera até 180 s pelas respostas (`proxy_read_timeout`), e o navegador
desiste após 150 s.

## 6. Funcionalidades didáticas na interface

- **Explicar token com IA**: no detalhe de um token (aba *Código colorido*).
- **Entender erro com IA**: em cada erro léxico e em cada erro sintático.
- **Explicar este nó com IA**: no detalhe de um nó selecionado na AST.
- **Professor virtual**: área de perguntas livres, com sugestões (scanner ×
  parser, terminais e não terminais, AST × árvore de derivação, precedência,
  recursão à esquerda). As perguntas incluem a gramática do projeto e, se houver,
  um resumo da análise do código atual.

Todas as respostas aparecem com o aviso “Explicação gerada por IA (...) pode
conter erros” e um indicador de carregamento enquanto a resposta não chega. A
situação do assistente (disponível ou não, e por quê) aparece no topo do
professor virtual.

## 7. Testes da integração

| Tipo | Como | Situação |
|------|------|----------|
| Montagem do contexto com dados reais (nó, token, erros, conceito) | `backend/test_ia.py` | automatizado |
| Extração de `message.content`, resposta vazia/inválida, Ollama fora do ar com nova tentativa, tempo esgotado, modelo não instalado, status | `backend/test_ia.py` (Ollama simulado) | automatizado |
| Endpoints `/ia/status` e `/ia/explicar` (sucesso, 503 e pedidos inválidos) | `backend/test_app.py` (`TestEndpointsIA`) | automatizado |
| Formatação segura da resposta (sem executar HTML) | `frontend/test_interface.js` | automatizado |
| Botão da IA no nó da AST abre o diálogo e mostra resposta ou motivo da indisponibilidade; a análise continua funcionando | `tests/test_interface.py` (`testar_ia_contextual`) | automatizado |
| Contêiner `ollama` sobe com `--profile ia`; o backend o acessa em `http://ollama:11434` e detecta que o modelo não foi baixado | manual (registrado em `RELATORIO_TESTES.md`) | executado |
| `ollama pull llama3.2` e `ollama list` | manual | executado (modelo de 2,0 GB) |
| Resposta real do Llama 3.2 pela API e pela interface (nó, erro sintático, pergunta conceitual) | manual (seção 10) | executado |

```bash
docker compose run --rm --build backend python -m unittest -v test_ia
```

## 8. Limitações conhecidas

- **O modelo comete erros conceituais**, e isso foi observado na demonstração
  (seção 10): confundiu níveis da gramática, inventou nós que não existem na AST
  e misturou exemplos. As melhorias no contexto reduziram, mas não eliminaram,
  esses erros. Por isso as respostas são marcadas como geradas por IA e nunca
  substituem os resultados do compilador.
- A qualidade varia com a pergunta: perguntas específicas (“Por que a
  multiplicação aparece abaixo da adição?”) tiveram respostas melhores que a
  pergunta padrão genérica do botão.
- Na CPU (sem GPU), cada resposta levou de 40 s a 1 min na demonstração.
- O modelo de 3B parâmetros às vezes responde de forma genérica. O contexto
  enviado (regra da gramática, nó pai, subárvore) existe para reduzir isso.

## 9. Demonstração (roteiro)

1. `docker compose --profile ia up -d --build` e
   `docker compose exec ollama ollama pull llama3.2`.
2. Abrir http://localhost:3000 e conferir, no *Professor virtual*, a mensagem
   “Assistente de IA disponível (modelo llama3.2)”.
3. Digitar `resultado = 10 + 5 * 2` e clicar em **Analisar código**.
4. Ver os tokens (análise léxica) e a AST (análise sintática).
5. Clicar no nó **Multiplicação (\*)** e depois em **✨ Explicar este nó com IA**.
6. Digitar `total = 10 +` e analisar; no erro sintático, clicar em
   **✨ Entender erro com IA**.

## 10. Registro da demonstração

Executada com o Llama 3.2 real (`llama3.2:latest`, 3B parâmetros, 2,0 GB),
Ollama no Docker Compose (`--profile ia`), em CPU, sem GPU. As respostas abaixo
foram copiadas sem edição.

![Explicação de um nó da AST gerada pelo Llama 3.2 na interface](img/demo-ia-no.png)

### 10.1. Primeira tentativa e ajustes feitos

Com a instrução de sistema original, a explicação do nó `MULTIPLICACAO` de
`resultado = 10 + 5 * 2` acertava a ideia geral, mas afirmava que “a
multiplicação é considerada um termo unário” — errado: `unario` é a regra do
sinal de **um** operando (`-x`). Em outras tentativas, o modelo redesenhou a
árvore com nós repetidos e inventou um “nó UNÁRIO”. Ajustes feitos em
`backend/ia.py`:

1. **Contexto de precedência** (`PRECEDENCIA`): enviado junto com nós de
   expressão; explica a ordem dos níveis da gramática e por que o operador mais
   forte fica mais abaixo na AST.
2. **Regra 12 na instrução de sistema**: não redesenhar a árvore nem citar nós,
   regras ou níveis que não estejam nos dados; limite de 180 palavras.
3. **`temperature: 0`** (antes 0,2), para respostas mais estáveis.
4. **Glossário do projeto** (`GLOSSARIO`) nas perguntas conceituais (ver 10.4).

Os ajustes 1 e 4 têm testes em `backend/test_ia.py`.

### 10.2. Nó da AST (após os ajustes)

- **Código:** `resultado = 10 + 5 * 2`
- **Alvo:** nó `MULTIPLICACAO` (`{"tipo": "no", "id": 4}`)
- **Pergunta:** “Por que a multiplicação aparece abaixo da adição?”
- **Dados enviados:** o texto montado por `montar_contexto`: o nó e seus
  atributos, a regra `termo` com a produção EBNF, o caminho
  `PROGRAMA > ATRIBUICAO > ADICAO`, a subárvore, o trecho `5 * 2` e o resumo de
  precedência.
- **Resposta obtida:**

> Vamos entender por que a multiplicação aparece abaixo da adição na árvore sintática (AST).
>
> A gramática do projeto define a precedência das operações, que é uma ordem em que as regras são aplicadas. Nesse caso, a precedência é definida como:
>
> * soma (+, -)
> * termo (*, /, //, %)
> * unário (sinal de um único operando, como -x)
> * potência (**
> * primário (chamada, índice, atributo)
> * atômico (nome, número, texto, parênteses)
>
> A regra da soma chama a regra do termo para cada lado do operador '+'. O lado direito '5 * 2' é reconhecido pela regra do termo e vira um nó MULTIPLICACAO, filho direito do nó ADICAO.
>
> Isso significa que a multiplicação é reconhecida antes da adição, pois a regra do termo é aplicada antes da regra da soma. Portanto, a multiplicação aparece abaixo da adição na árvore sintática, pois é calculada antes.
>
> Em resumo, a ordem em que as regras são aplicadas é determinada pela precedência, e nesse caso, a multiplicação é reconhecida antes da adição, o que explica por que ela aparece abaixo da adição na AST.

**Avaliação:** correta no essencial (a regra `soma` chama `termo` para cada
lado do `+`; `5 * 2` vira o filho direito de `ADICAO`; o nó mais abaixo é
calculado antes). A lista de níveis foi copiada do contexto e está incompleta
(omite `ou`, `e`, `nao` e `comparacao`), e “a regra do termo é aplicada antes
da regra da soma” é impreciso: a regra `soma` **começa** antes e chama `termo`;
o que termina antes é o reconhecimento de `termo`.

**Mesma explicação pelo botão da interface** (pergunta padrão, sem texto do
estudante; é a tela da imagem acima): a resposta acertou a posição (“filho
direito do nó ADICAO”), mas errou ao dizer que o nó “é filho esquerdo do nó
MULTIPLICACAO” e que `termo` chama uma “regra da multiplicação”, que não
existe. Isso mostra a limitação do modelo de 3B parâmetros e por que o aviso
“pode conter erros” é necessário.

### 10.3. Erro sintático

- **Código:** `total = 10 +`
- **Alvo:** primeiro erro sintático (`{"tipo": "erro_sintatico", "indice": 0}`),
  pergunta padrão.
- **Dados enviados:** a mensagem do parser, linha 1, coluna 13, o encontrado
  (`NOVA_LINHA`), o esperado, a regra `atomo` com a produção EBNF e o código.
- **Resposta obtida:**

> Vamos analisar o erro sintático:
>
> A regra da gramática esperada é `atomo → atomo = IDENTIFICADOR | LITERAL_INTEIRO | LITERAL_REAL | LITERAL_STRING | "True" | "False" | "None" | "(" expressao ")" | lista;`.
>
> A construção que estava sendo analisada é a expressão `total = 10 +`. A regra espera que a expressão termine com um valor, como um identificador, um literal inteiro, um literal real, um literal string, "True", "False", "None", um parêntese com uma expressão ou uma lista.
>
> No entanto, o código não atende a essa expectativa porque o operador `+` está sendo usado com um operador de adição, mas não há um valor associado a ele. O código está apenas indicando a linha e a coluna onde o erro ocorreu.
>
> Para corrigir o erro, o estudante precisa fornecer um valor após o operador `+`, como `total = 10 + 5`. Isso completaria a expressão com um valor, atendendo à regra esperada.

**Avaliação:** correta e útil: cita a regra `atomo`, explica que falta um valor
depois do `+` e sugere `total = 10 + 5`. Não contradiz o parser. O trecho “o
operador `+` está sendo usado com um operador de adição” é redundante.

### 10.4. Pergunta conceitual ao professor virtual

- **Pergunta:** “Qual a diferença entre AST e árvore de derivação?”
- **Antes do glossário:** a resposta chamou a AST de “Árvore de Estrutura”,
  disse que ela é construída **depois** da análise sintática e que guarda tipos
  de dados — três erros.
- **Depois do glossário** (resposta obtida):

> A diferença entre AST (Árvore Sintática ABSTRATA) e árvore de derivação (ou árvore concreta) é fundamental para entender como o compilador processa a sintaxe do código-fonte.
>
> **Árvore de Derivação (ou Árvore Concreta)**
>
> A árvore de derivação é um representação detalhada do processo de análise sintática. Ela inclui todos os tokens consumidos pelo parser, incluindo parênteses, colchetes, colons, fins de linha, etc. Além disso, ela também inclui todas as regras intermediárias de precedência aplicadas pelo parser. Isso significa que a árvore de derivação é uma representação detalhada do processo de análise sintática, incluindo todos os detalhes da análise.
>
> **Árvore Sintática ABSTRATA (AST)**
>
> A árvore sintática abstrata, por outro lado, é uma representação simplificada do processo de análise sintática. Ela guarda apenas o que importa para o significado do código-fonte, sem incluir detalhes como parênteses, colchetes, colons, fins de linha, etc. Além disso, ela também não guarda tipos, pois a análise de tipos é uma etapa separada da análise sintática.
>
> Em resumo, a árvore de derivação é uma representação detalhada do processo de análise sintática, enquanto a árvore sintática abstrata é uma representação simplificada do mesmo processo. A árvore sintática abstrata é mais focada no significado do código-fonte, enquanto a árvore de derivação é mais focada nos detalhes da análise.
>
> Para o nosso exemplo, a árvore de derivação para a expressão `10 + 5 * 2` seria um árvore com 38 nós, incluindo todos os detalhes da análise, enquanto a árvore sintática abstrata para a mesma expressão seria um árvore com 6 nós, que guarda apenas o significado da expressão.

**Avaliação:** a diferença principal está correta (derivação com todos os
tokens e regras intermediárias; AST só com o significado; AST sem tipos). O
último parágrafo erra o exemplo: os números 38 e 6 do glossário são de
`x = 5 + 3`, não de `10 + 5 * 2` (que tem 8 nós na AST). O modelo misturou os
exemplos.

### 10.5. Conclusão

A integração funciona de ponta a ponta: o backend envia ao Llama 3.2 apenas os
resultados reais do scanner e do parser e devolve a explicação à interface, com
o aviso de que foi gerada por IA. As respostas ajudam a entender erros e a
estrutura da árvore, mas o modelo de 3B parâmetros ainda comete imprecisões.
Por isso a IA é um **complemento** e os resultados oficiais continuam sendo os
do compilador.
