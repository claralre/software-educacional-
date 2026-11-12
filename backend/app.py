from flask import Flask, jsonify, request

import ia
from analisador_sintatico import (
    GRAMATICA,
    ORDEM_GRAMATICA,
    TIPOS_NO,
    analisar_sintaticamente,
)
from scanner import analisar_lexicamente, escopo_lexico

app = Flask(__name__)
app.json.ensure_ascii = False
app.json.sort_keys = False

TAMANHO_MAXIMO_CODIGO = 20000
# Acima deste número de tokens, a árvore de derivação e os passos da
# construção não são enviados (a AST continua sendo enviada).
LIMITE_TOKENS_DETALHES = 3000


def resposta_invalida(mensagem, status=400):
    return jsonify(
        sucesso=False,
        mensagem=mensagem,
        tokens=[],
        erros=[]
    ), status


def validar_codigo(dados):
    """Validação da Etapa 2. Retorna (codigo, resposta_de_erro)."""
    if not isinstance(dados, dict):
        return None, resposta_invalida("Requisição inválida.")

    codigo = dados.get("codigo")

    if not isinstance(codigo, str):
        return None, resposta_invalida("Informe um código-fonte válido.")

    if not codigo.strip():
        return None, resposta_invalida(
            "Informe um código-fonte antes de solicitar a análise."
        )

    if len(codigo) > TAMANHO_MAXIMO_CODIGO:
        return None, resposta_invalida(
            "O código é muito grande para ser analisado "
            f"(máximo de {TAMANHO_MAXIMO_CODIGO} caracteres).",
            413
        )

    return codigo, None


def analisar_completo(codigo):
    """Executa o scanner e, se não houver erros léxicos, o parser."""
    lexico = analisar_lexicamente(codigo)
    total_erros_lexicos = len(lexico["erros"])

    if total_erros_lexicos:
        sintatico = {
            "executado": False,
            "sucesso": False,
            "mensagem": (
                "Análise sintática não executada: corrija primeiro os "
                f"{total_erros_lexicos} erro(s) léxico(s). Com caracteres inválidos, "
                "a sequência de tokens está incompleta e o parser produziria "
                "diagnósticos enganosos."
            ),
            "ast": None,
            "erros": [],
            "derivacao": None,
            "passos": None,
            "resumo": None,
            "detalhes_omitidos": False,
        }
        return lexico, sintatico

    detalhes = len(lexico["tokens"]) <= LIMITE_TOKENS_DETALHES
    sintatico = analisar_sintaticamente(lexico["tokens"], registrar_detalhes=detalhes)
    sintatico["executado"] = True
    sintatico["detalhes_omitidos"] = not detalhes
    if sintatico["sucesso"]:
        sintatico["mensagem"] = (
            "Análise sintática concluída: o programa segue a gramática. "
            f"AST com {sintatico['resumo']['total_nos']} nó(s)."
        )
    else:
        sintatico["mensagem"] = (
            "Análise sintática concluída com "
            f"{len(sintatico['erros'])} erro(s) sintático(s)."
        )
    # Ordem estável dos campos na resposta.
    ordem = ["executado", "sucesso", "mensagem", "ast", "erros", "derivacao",
             "passos", "resumo", "detalhes_omitidos"]
    return lexico, {chave: sintatico[chave] for chave in ordem}


@app.route("/")
def inicio():
    return jsonify(mensagem="Hello, World!")


@app.route("/escopo", methods=["GET"])
def escopo():
    return jsonify(escopo_lexico()), 200


@app.route("/gramatica", methods=["GET"])
def gramatica():
    return jsonify(
        simbolo_inicial="programa",
        regras=[{"nome": nome, "producao": GRAMATICA[nome]} for nome in ORDEM_GRAMATICA],
        tipos_no=[
            {"tipo": tipo, "rotulo": rotulo, "categoria": categoria}
            for tipo, (rotulo, categoria) in TIPOS_NO.items()
        ],
    ), 200


@app.route("/analisar", methods=["POST"])
def analisar():
    codigo, erro = validar_codigo(request.get_json(silent=True))
    if erro:
        return erro

    try:
        lexico, sintatico = analisar_completo(codigo)
    except Exception:
        # Nunca expõe detalhes internos (stack trace) ao usuário.
        app.logger.exception("Falha inesperada na análise")
        return resposta_invalida(
            "Ocorreu um erro interno ao analisar o código. Tente novamente.",
            500
        )

    total_erros = len(lexico["erros"])
    if total_erros == 0:
        mensagem = (
            "Análise léxica concluída: "
            f"{lexico['resumo']['total_tokens']} token(s) reconhecido(s)."
        )
    else:
        mensagem = (
            f"Análise léxica concluída com {total_erros} erro(s) léxico(s)."
        )

    # Os campos de nível superior são os da Etapa 3 (análise léxica) e foram
    # mantidos para compatibilidade. Os blocos "lexico" e "sintatico" são o
    # contrato da Etapa 4.
    return jsonify(
        sucesso=total_erros == 0,
        recebido=True,
        mensagem=mensagem,
        tokens=lexico["tokens"],
        erros=lexico["erros"],
        comentarios=lexico["comentarios"],
        resumo=lexico["resumo"],
        lexico={
            "sucesso": total_erros == 0,
            "mensagem": mensagem,
            "tokens": lexico["tokens"],
            "erros": lexico["erros"],
        },
        sintatico=sintatico,
    ), 200


@app.route("/ia/status", methods=["GET"])
def ia_status():
    return jsonify(ia.verificar_status()), 200


@app.route("/ia/explicar", methods=["POST"])
def ia_explicar():
    dados = request.get_json(silent=True)
    if not isinstance(dados, dict):
        return jsonify(sucesso=False, mensagem="Requisição inválida."), 400

    try:
        contexto = ia.montar_contexto(dados, analisar_completo)
    except ia.PedidoInvalido as erro:
        return jsonify(sucesso=False, mensagem=str(erro)), 400
    except Exception:
        app.logger.exception("Falha ao montar o contexto da IA")
        return jsonify(sucesso=False, mensagem="Não foi possível preparar a pergunta."), 500

    try:
        resposta = ia.perguntar(contexto)
    except ia.IAIndisponivel as erro:
        return jsonify(sucesso=False, mensagem=str(erro)), 503
    except ia.IATempoEsgotado as erro:
        return jsonify(sucesso=False, mensagem=str(erro)), 504
    except ia.IARespostaInvalida as erro:
        return jsonify(sucesso=False, mensagem=str(erro)), 502

    return jsonify(
        sucesso=True,
        resposta=resposta,
        modelo=ia.MODELO,
        gerado_por_ia=True,
        aviso=ia.AVISO,
    ), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
