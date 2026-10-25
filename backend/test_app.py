import unittest
from unittest import mock

from app import app, TAMANHO_MAXIMO_CODIGO


class TestBackend(unittest.TestCase):
    """Testes da Etapa 2 (regressão), adaptados ao novo contrato."""

    def setUp(self):
        self.cliente = app.test_client()

    def test_hello_world(self):
        resposta = self.cliente.get("/")
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(
            resposta.get_json()["mensagem"],
            "Hello, World!"
        )

    def test_codigo_valido(self):
        resposta = self.cliente.post(
            "/analisar",
            json={"codigo": "idade = 21"}
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertTrue(resposta.get_json()["recebido"])

    def test_codigo_vazio(self):
        resposta = self.cliente.post(
            "/analisar",
            json={"codigo": ""}
        )
        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(
            resposta.get_json()["mensagem"],
            "Informe um código-fonte antes de solicitar a análise."
        )

    def test_apenas_espacos(self):
        resposta = self.cliente.post(
            "/analisar",
            json={"codigo": "   "}
        )
        self.assertEqual(resposta.status_code, 400)

    def test_campo_ausente(self):
        resposta = self.cliente.post(
            "/analisar",
            json={}
        )
        self.assertEqual(resposta.status_code, 400)

    def test_json_invalido(self):
        resposta = self.cliente.post(
            "/analisar",
            data="texto inválido",
            content_type="application/json"
        )
        self.assertEqual(resposta.status_code, 400)

    def test_tipo_invalido(self):
        resposta = self.cliente.post(
            "/analisar",
            json={"codigo": 123}
        )
        self.assertEqual(resposta.status_code, 400)


class TestAnaliseLexica(unittest.TestCase):
    """Testes do endpoint /analisar com o scanner (Etapa 3)."""

    def setUp(self):
        self.cliente = app.test_client()

    def analisar(self, codigo):
        return self.cliente.post("/analisar", json={"codigo": codigo})

    def test_codigo_valido_retorna_tokens(self):
        resposta = self.analisar("idade = 21")
        dados = resposta.get_json()
        self.assertEqual(resposta.status_code, 200)
        self.assertTrue(dados["sucesso"])
        self.assertEqual(dados["erros"], [])
        self.assertEqual(
            [(t["tipo"], t["lexema"]) for t in dados["tokens"][:3]],
            [("IDENTIFICADOR", "idade"), ("OPERADOR", "="),
             ("LITERAL_INTEIRO", "21")]
        )

    def test_formato_da_resposta(self):
        dados = self.analisar("x = 1  # nota").get_json()
        self.assertEqual(
            set(dados),
            {"sucesso", "recebido", "mensagem", "tokens", "erros",
             "comentarios", "resumo"}
        )
        token = dados["tokens"][0]
        self.assertEqual(
            {"tipo", "lexema", "linha", "coluna"} - set(token), set()
        )
        self.assertIsInstance(token["linha"], int)
        self.assertIsInstance(token["coluna"], int)
        self.assertEqual(
            set(dados["resumo"]), {"total_tokens", "total_erros", "por_tipo"}
        )
        self.assertEqual(len(dados["comentarios"]), 1)

    def test_mensagem_de_sucesso(self):
        dados = self.analisar("idade = 21").get_json()
        self.assertEqual(
            dados["mensagem"],
            "Análise léxica concluída: 5 token(s) reconhecido(s)."
        )

    def test_erro_lexico_retorna_sucesso_falso(self):
        resposta = self.analisar("x = 1\nresultado = @")
        dados = resposta.get_json()
        self.assertEqual(resposta.status_code, 200)
        self.assertFalse(dados["sucesso"])
        self.assertEqual(len(dados["erros"]), 1)
        erro = dados["erros"][0]
        self.assertEqual(erro["tipo"], "ERRO_LEXICO")
        self.assertEqual(erro["lexema"], "@")
        self.assertEqual((erro["linha"], erro["coluna"]), (2, 13))
        self.assertIn("caractere não reconhecido", erro["mensagem"])
        self.assertIn("1 erro(s) léxico(s)", dados["mensagem"])

    def test_erro_lexico_mantem_tokens_validos(self):
        dados = self.analisar("a = @ + b").get_json()
        lexemas = [t["lexema"] for t in dados["tokens"]]
        self.assertIn("a", lexemas)
        self.assertIn("b", lexemas)

    def test_erro_sintatico_e_tokenizado_normalmente(self):
        dados = self.analisar("if = = 10 )").get_json()
        self.assertTrue(dados["sucesso"])

    def test_respostas_invalidas_tem_formato_uniforme(self):
        dados = self.analisar("").get_json()
        self.assertFalse(dados["sucesso"])
        self.assertEqual(dados["tokens"], [])
        self.assertEqual(dados["erros"], [])

    def test_codigo_muito_grande(self):
        resposta = self.analisar("x" * (TAMANHO_MAXIMO_CODIGO + 1))
        self.assertEqual(resposta.status_code, 413)
        self.assertFalse(resposta.get_json()["sucesso"])

    def test_falha_interna_nao_expoe_detalhes(self):
        with mock.patch("app.analisar_lexicamente",
                        side_effect=RuntimeError("segredo interno")):
            app.logger.disabled = True
            try:
                resposta = self.analisar("x = 1")
            finally:
                app.logger.disabled = False
        self.assertEqual(resposta.status_code, 500)
        texto = resposta.get_data(as_text=True)
        self.assertNotIn("segredo interno", texto)
        self.assertNotIn("Traceback", texto)

    def test_metodo_get_nao_permitido(self):
        resposta = self.cliente.get("/analisar")
        self.assertEqual(resposta.status_code, 405)

    def test_endpoint_escopo(self):
        resposta = self.cliente.get("/escopo")
        dados = resposta.get_json()
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("while", dados["palavras_reservadas"])
        self.assertIn("==", [o["lexema"] for o in dados["operadores"]])
        self.assertIn("IDENTIFICADOR", dados["tipos_token"])


if __name__ == "__main__":
    unittest.main()
