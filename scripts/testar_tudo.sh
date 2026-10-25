#!/bin/sh
# Executa toda a bateria de testes (regressão das Etapas 1, 2 e 3).
# Uso, na pasta principal do projeto:  sh scripts/testar_tudo.sh
set -e

echo "== 1. Subindo os serviços com Docker Compose"
docker compose up -d --build

echo "== 2. Testes do backend (scanner + endpoints)"
docker compose run --rm backend python -m unittest -v test_scanner test_app

echo "== 3. Testes do frontend (Node.js)"
docker run --rm -v "$PWD/frontend:/app" -w /app node:22-alpine node --test test_interface.js

echo "== 4. Verificando a comunicação frontend -> backend"
curl -sf -X POST http://localhost:3000/api/analisar \
    -H "Content-Type: application/json" \
    -d '{"codigo": "idade = 21"}' > /dev/null
echo "Comunicação OK"

echo "== 5. Testes de interação (Playwright)"
if python -c "import playwright" 2>/dev/null; then
    python tests/test_interface.py
else
    echo "Playwright não instalado: pulei os testes de interação."
    echo "Instale com: python -m pip install playwright && python -m playwright install chromium"
fi

echo "== Todos os testes executados."
