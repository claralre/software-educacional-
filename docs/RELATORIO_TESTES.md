
# Relatório de Testes — Segunda Etapa

## 1. Testes do Backend

Ferramenta: Python unittest

Comando:
docker compose run --rm --build backend python -m unittest -v test_app

Resultado:
- Testes executados: 7
- Testes aprovados: 7
- Testes reprovados: 0

Funcionalidades verificadas:
- Rota inicial Hello, World!
- Recebimento de código válido
- Rejeição de código vazio
- Rejeição de entradas com espaços
- Rejeição de campos ausentes
- Rejeição de JSON inválido
- Rejeição de tipos inválidos

## 2. Testes da Interface

Ferramenta: Node.js Test Runner

Comando:
docker run --rm -v "$PWD/frontend:/app" -w /app node:22-alpine node --test test_interface.js

Resultado:
- Testes executados: 8
- Testes aprovados: 8
- Testes reprovados: 0

Funcionalidades verificadas:
- Identificação do software
- Campo de entrada de código
- Botão de análise
- Área de resultados
- Seleção de exemplos
- Presença de três exemplos Python
- Código de comunicação com o backend
- Código de validação de entrada vazia

## 3. Testes Manuais

Ambiente: Docker Compose e navegador Safari.

Verificações realizadas:
- Interface acessível em http://localhost:3000
- Exemplo de operação aritmética carregado corretamente
- Código enviado ao backend
- Mensagem "Código recebido com sucesso."
- Entrada vazia rejeitada com mensagem apropriada

## 4. Limitações

Os testes automatizados da interface verificam
elementos e trechos do código-fonte, mas ainda
não simulam interações reais no navegador.

A análise léxica, sintática e semântica ainda
não foi implementada, conforme o escopo
da segunda etapa.


## Testes automatizados de interação — Playwright

Foi utilizado o Playwright com Python e Chromium para
verificar o funcionamento da interface web.

### Cenários testados

1. Abertura da página do Software Educacional.
2. Verificação do título da aplicação.
3. Seleção de um exemplo de código Python.
4. Preenchimento automático do campo de código.
5. Edição manual do código-fonte.
6. Envio do código para análise.
7. Exibição da mensagem de sucesso retornada pelo backend.
8. Validação da mensagem de erro para código vazio.

### Ambiente de execução

- Sistema operacional: macOS.
- Linguagem dos testes: Python.
- Ferramenta: Playwright com Chromium.
- Aplicação executada com Docker Compose.
- Endereço da interface: http://localhost:3000.

### Comando utilizado

python tests/test_interface.py

### Resultado

Todos os cenários de interação executados foram aprovados.

Mensagem apresentada no terminal:

Testes de interação aprovados!

