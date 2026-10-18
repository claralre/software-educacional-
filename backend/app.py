
from flask import Flask, jsonify, request

app = Flask(__name__)


@app.route("/")
def inicio():
    return jsonify(mensagem="Hello, World!")


@app.route("/analisar", methods=["POST"])
def analisar():
    dados = request.get_json(silent=True)

    if not isinstance(dados, dict):
        return jsonify(
            mensagem="Requisição inválida."
        ), 400

    codigo = dados.get("codigo")

    if not isinstance(codigo, str):
        return jsonify(
            mensagem="Informe um código-fonte válido."
        ), 400

    if not codigo.strip():
        return jsonify(
            mensagem="Informe um código-fonte antes de solicitar a análise."
        ), 400

    return jsonify(
        mensagem="Código recebido com sucesso.",
        recebido=True
    ), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
