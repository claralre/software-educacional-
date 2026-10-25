
from flask import Flask, jsonify, request

from scanner import analisar_lexicamente, escopo_lexico

app = Flask(__name__)
app.json.ensure_ascii = False
app.json.sort_keys = False

TAMANHO_MAXIMO_CODIGO = 20000


def resposta_invalida(mensagem, status=400):
    return jsonify(
        sucesso=False,
        mensagem=mensagem,
        tokens=[],
        erros=[]
    ), status


@app.route("/")
def inicio():
    return jsonify(mensagem="Hello, World!")


@app.route("/escopo", methods=["GET"])
def escopo():
    return jsonify(escopo_lexico()), 200


@app.route("/analisar", methods=["POST"])
def analisar():
    dados = request.get_json(silent=True)

    if not isinstance(dados, dict):
        return resposta_invalida("Requisição inválida.")

    codigo = dados.get("codigo")

    if not isinstance(codigo, str):
        return resposta_invalida("Informe um código-fonte válido.")

    if not codigo.strip():
        return resposta_invalida(
            "Informe um código-fonte antes de solicitar a análise."
        )

    if len(codigo) > TAMANHO_MAXIMO_CODIGO:
        return resposta_invalida(
            "O código é muito grande para ser analisado "
            f"(máximo de {TAMANHO_MAXIMO_CODIGO} caracteres).",
            413
        )

    try:
        resultado = analisar_lexicamente(codigo)
    except Exception:
        # Nunca expõe detalhes internos (stack trace) ao usuário.
        app.logger.exception("Falha inesperada no scanner")
        return resposta_invalida(
            "Ocorreu um erro interno ao analisar o código. Tente novamente.",
            500
        )

    total_erros = len(resultado["erros"])
    if total_erros == 0:
        mensagem = (
            "Análise léxica concluída: "
            f"{resultado['resumo']['total_tokens']} token(s) reconhecido(s)."
        )
    else:
        mensagem = (
            f"Análise léxica concluída com {total_erros} erro(s) léxico(s)."
        )

    return jsonify(
        sucesso=total_erros == 0,
        recebido=True,
        mensagem=mensagem,
        tokens=resultado["tokens"],
        erros=resultado["erros"],
        comentarios=resultado["comentarios"],
        resumo=resultado["resumo"]
    ), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
