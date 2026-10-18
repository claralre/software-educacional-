# Software Educacional para Análise de Código Python

## 1. Descrição do projeto

Este projeto tem como objetivo desenvolver uma aplicação web educacional para auxiliar estudantes na compreensão dos processos de análise léxica, sintática e semântica de códigos escritos em Python.

O desenvolvimento é incremental. A primeira etapa contemplou a configuração do ambiente, a estrutura da aplicação e a comunicação entre frontend e backend.

A segunda etapa contempla a implementação da interface web para entrada de código-fonte, seleção de exemplos, envio de requisições ao backend e apresentação de mensagens de retorno.

**Nesta etapa, o sistema ainda não realiza análises léxica, sintática ou semântica.** Essas funcionalidades serão implementadas nas próximas etapas.

## 2. Linguagem escolhida

A linguagem selecionada é **Python**, devido à sua legibilidade, sintaxe relativamente simples e ampla utilização no ensino de programação.

### Subconjunto inicial

O projeto abordará inicialmente:

- Declaração e atribuição de variáveis;
- Identificadores e valores numéricos;
- Operadores aritméticos (`+`, `-`, `*`, `/`);
- Expressões aritméticas simples.

## 3. Tecnologias utilizadas

- **Frontend:** HTML e JavaScript;
- **Backend:** Python com Flask;
- **Servidor web:** Nginx;
- **Conteinerização:** Docker;
- **Orquestração:** Docker Compose;
- **Testes do backend:** Python e unittest;
- **Testes do frontend:** Node.js;
- **Testes de interação:** Playwright com Chromium;
- **Versionamento:** Git e GitHub.

## 4. Estrutura do projeto

```text
software-educacional/
├── frontend/
│   ├── index.html
│   ├── nginx.conf
│   ├── Dockerfile
│   └── test_interface.js
├── backend/
│   ├── app.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── test_app.py
├── tests/
│   └── test_interface.py
├── docs/
│   └── RELATORIO_TESTES.md
├── compose.yaml
└── README.md
```

## 5. Funcionalidades implementadas

A segunda etapa disponibiliza uma interface web com:

- Identificação do projeto e da linguagem Python;
- Campo editável para inserção de código-fonte;
- Seleção de três exemplos de código Python;
- Preenchimento automático do campo ao selecionar um exemplo;
- Botão para solicitar a análise;
- Área para apresentar as mensagens de resposta;
- Comunicação entre frontend e backend por meio de requisições HTTP e JSON;
- Validação de código vazio;
- Tratamento de falhas de comunicação na interface.

### Exemplos disponíveis

**Declaração de variável:**

```python
idade = 21
```

**Operação de soma:**

```python
resultado = 10 + 5
```

**Operação de multiplicação:**

```python
total = 4 * 3
```

Os exemplos podem ser selecionados e modificados pelo usuário.

## 6. Comunicação entre frontend e backend

A interface envia uma requisição HTTP POST para o endpoint `/api/analisar`, encaminhado pelo Nginx ao backend Flask em `/analisar`.

O corpo da requisição utiliza JSON:

```json
{
  "codigo": "idade = 21"
}
```

Quando o código é válido para recebimento, o backend responde:

```json
{
  "mensagem": "Código recebido com sucesso.",
  "recebido": true
}
```

O sistema também verifica situações como:

- Código vazio ou contendo apenas espaços;
- Campo `codigo` ausente;
- Tipo de dado inválido;
- JSON malformado.

As requisições inválidas recebem respostas de erro, com código HTTP 400.

A resposta de sucesso confirma apenas o recebimento do código, não sua correção sintática ou semântica.

## 7. Pré-requisitos

Para executar a aplicação:

- Docker Desktop;
- Docker Compose;
- Navegador web.

Para executar os testes automatizados adicionais:

- Node.js, para os testes de estrutura do frontend;
- Python e Playwright, para os testes de interação;
- Chromium instalado pelo Playwright.

## 8. Como executar a aplicação

Clone o repositório ou baixe o arquivo ZIP no GitHub e descompacte-o.

Abra o Terminal na pasta principal do projeto, onde está localizado o arquivo `compose.yaml`.

Execute:

```bash
docker compose up -d --build
```

Aguarde a inicialização dos serviços.

Abra a interface no navegador:

http://localhost:3000

O backend também pode ser acessado em:

http://localhost:5001

Para encerrar os serviços:

```bash
docker compose down
```

## 9. Testes realizados

O projeto utiliza testes desenvolvidos progressivamente para verificar o backend, a estrutura do frontend e a interação entre os componentes.

### 9.1. Testes do backend

Foram implementados **7 testes automatizados**, utilizando `unittest`.

Os cenários incluem:

- Funcionamento da rota inicial;
- Recebimento de código válido;
- Código vazio;
- Código contendo apenas espaços;
- Ausência do campo `codigo`;
- JSON malformado;
- Tipo de dado inválido.

Para executar:

```bash
docker compose run --rm --build backend python -m unittest -v test_app
```

**Resultado obtido: 7 testes aprovados.**

### 9.2. Testes de estrutura do frontend

Foram implementados **8 testes automatizados** com Node.js, verificando elementos e trechos do código-fonte da interface.

Para executar, a partir da pasta principal do projeto:

```bash
docker run --rm -v "$PWD/frontend:/app" -w /app node:22-alpine node --test test_interface.js
```

**Resultado obtido: 8 testes aprovados.**

Esses testes verificam a estrutura do frontend, mas não substituem os testes de interação no navegador.

### 9.3. Testes automatizados de interação

Foi utilizado o Playwright com Chromium para verificar o comportamento real da interface.

Os cenários executados incluem:

- Abertura da aplicação;
- Verificação do título;
- Seleção de exemplo;
- Preenchimento automático do campo;
- Edição manual do código;
- Envio de requisição;
- Exibição da mensagem de sucesso;
- Validação de código vazio.

Para instalar o Playwright em um ambiente Python:

```bash
python -m pip install playwright
python -m playwright install chromium
```

Com a aplicação em execução em `http://localhost:3000`, execute na pasta principal:

```bash
python tests/test_interface.py
```

**Resultado obtido: testes de interação aprovados.**

### 9.4. Testes manuais

Também foram realizados testes manuais no navegador, incluindo:

- Acesso à interface;
- Seleção de exemplo de código;
- Envio de código preenchido;
- Exibição da resposta do backend;
- Envio de campo vazio.

Os resultados estão documentados em `docs/RELATORIO_TESTES.md`.

## 10. Estado atual do projeto

**Primeira etapa — Concluída**

- Estrutura inicial da aplicação;
- Configuração do Docker e Docker Compose;
- Comunicação básica entre frontend e backend.

**Segunda etapa — Funcionalidades e testes implementados**

- Interface para entrada de código Python;
- Três exemplos disponíveis;
- Envio de código para o backend;
- Respostas em JSON;
- Validação de entradas inválidas;
- Testes automatizados e manuais;
- Documentação dos testes.

## 11. Próximas etapas

As próximas etapas contemplarão a implementação dos mecanismos de análise léxica, sintática e semântica, além
