# software-educacional-
Software educacional para análise léxica, sintática e semântica de códigos em Python.


# Software Educacional para Análise de Código Python

## 1. Descrição do projeto

Este projeto tem como objetivo desenvolver uma aplicação web educacional para auxiliar estudantes na compreensão dos processos de análise léxica, sintática e semântica de códigos escritos em Python.

A aplicação será desenvolvida de forma incremental, começando pela estrutura básica do ambiente e evoluindo para a implementação das funcionalidades de análise de código.

## 2. Linguagem escolhida

A linguagem selecionada para análise é **Python**, devido à sua sintaxe relativamente simples, legibilidade e ampla utilização no ensino de programação.

### Subconjunto inicial

Inicialmente, o software abordará:

- Declaração e atribuição de variáveis;
- Identificadores e valores numéricos;
- Operadores aritméticos (`+`, `-`, `*`, `/`);
- Expressões aritméticas simples.

A delimitação desse subconjunto permite desenvolver e testar gradualmente as análises léxica, sintática e semântica.

## 3. Tecnologias utilizadas

- **Frontend:** HTML e JavaScript;
- **Backend:** Python com Flask;
- **Servidor web:** Nginx;
- **Conteinerização:** Docker;
- **Orquestração:** Docker Compose;
- **Versionamento:** GitHub.

## 4. Estrutura do projeto

```text
software-educacional/
├── frontend/
│   ├── index.html
│   ├── nginx.conf
│   └── Dockerfile
├── backend/
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
├── compose.yaml
└── README.md
```

## 5. Pré-requisitos

Para executar o projeto, é necessário ter instalado:

- Docker Desktop com Docker Engine e Docker Compose disponíveis;
- Um navegador web.

Para verificar a instalação, execute:

```bash
docker --version
docker compose version
```

## 6. Como executar

Clone o repositório do GitHub ou baixe seu conteúdo em formato ZIP e descompacte-o.

Abra o Terminal na pasta principal do projeto, onde está localizado o arquivo `compose.yaml`.

Execute:

```bash
docker compose up --build
```

Aguarde a construção e a inicialização dos contêineres.

Acesse a aplicação no navegador:

http://localhost:3000

A interface deverá apresentar a mensagem:

**Hello, World!**

A mensagem é obtida do backend Flask por meio de uma requisição HTTP encaminhada pelo Nginx.

O backend também pode ser acessado diretamente em:

http://localhost:5001

## 7. Como encerrar

No Terminal em que os serviços estão executando, pressione `Ctrl + C`.

Em seguida, execute:

```bash
docker compose down
```

## 8. Validação da instalação

A instalação deve ser validada a partir de uma cópia limpa do repositório, seguindo os comandos documentados.

O teste será considerado bem-sucedido quando:

- Os contêineres iniciarem sem erros;
- O frontend estiver acessível na porta 3000;
- O backend responder corretamente;
- A interface apresentar a mensagem "Hello, World!" recebida do backend.

## 9. Estado atual

A primeira etapa contempla a organização do repositório, a estrutura inicial da aplicação web, a configuração do Docker e a comunicação entre frontend e backend.

As funcionalidades de análise léxica, sintática e semântica serão desenvolvidas nas próximas etapas.
