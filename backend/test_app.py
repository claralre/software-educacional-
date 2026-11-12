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
        # Os campos da Etapa 3 continuam presentes (a Etapa 4 só acrescenta
        # os blocos "lexico" e "sintatico").
        self.assertLessEqual(
            {"sucesso", "recebido", "mensagem", "tokens", "erros",
             "comentarios", "resumo"},
            set(dados)
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



class TestAnaliseSintatica(unittest.TestCase):
    """Testes do endpoint /analisar com o parser (Etapa 4)."""

    def setUp(self):
        self.cliente = app.test_client()

    def analisar(self, codigo):
        resposta = self.cliente.post("/analisar", json={"codigo": codigo})
        return resposta.status_code, resposta.get_json()

    def test_codigo_valido_retorna_ast(self):
        status, dados = self.analisar("resultado = 10 + 5 * 2")
        self.assertEqual(status, 200)
        sintatico = dados["sintatico"]
        self.assertTrue(sintatico["executado"])
        self.assertTrue(sintatico["sucesso"])
        self.assertEqual(sintatico["erros"], [])
        self.assertEqual(sintatico["ast"]["tipo"], "PROGRAMA")
        adicao = sintatico["ast"]["filhos"][0]["filhos"][1]
        self.assertEqual(adicao["tipo"], "ADICAO")
        self.assertEqual(adicao["filhos"][1]["tipo"], "MULTIPLICACAO")
        self.assertIn("AST com 8 nó(s)", sintatico["mensagem"])

    def test_formato_do_contrato_da_etapa_4(self):
        _, dados = self.analisar("x = 1")
        self.assertEqual(set(dados["lexico"]), {"sucesso", "mensagem", "tokens", "erros"})
        self.assertEqual(
            set(dados["sintatico"]),
            {"executado", "sucesso", "mensagem", "ast", "erros", "derivacao",
             "passos", "resumo", "detalhes_omitidos"})
        self.assertEqual(dados["lexico"]["tokens"], dados["tokens"])
        self.assertEqual(dados["sintatico"]["derivacao"]["regra"], "programa")
        self.assertIsInstance(dados["sintatico"]["passos"], list)

    def test_erro_sintatico_retorna_erros_e_ast_nula(self):
        status, dados = self.analisar("x = (1 + 2]\n")
        # ']' sem par é tokenizado normalmente; o '(' aberto é erro léxico.
        self.assertEqual(status, 200)
        status, dados = self.analisar("x = 5 +")
        self.assertEqual(status, 200)
        self.assertTrue(dados["sucesso"])  # léxico (Etapa 3) continua ok
        sintatico = dados["sintatico"]
        self.assertTrue(sintatico["executado"])
        self.assertFalse(sintatico["sucesso"])
        self.assertIsNone(sintatico["ast"])
        self.assertEqual(len(sintatico["erros"]), 1)
        erro = sintatico["erros"][0]
        self.assertEqual(erro["tipo"], "ERRO_SINTATICO")
        self.assertEqual((erro["linha"], erro["coluna"]), (1, 8))
        self.assertIn("1 erro(s) sintático(s)", sintatico["mensagem"])

    def test_erro_lexico_nao_executa_o_parser(self):
        status, dados = self.analisar("x = 5 @ 2")
        self.assertEqual(status, 200)
        self.assertFalse(dados["lexico"]["sucesso"])
        self.assertEqual(len(dados["lexico"]["erros"]), 1)
        sintatico = dados["sintatico"]
        self.assertFalse(sintatico["executado"])
        self.assertFalse(sintatico["sucesso"])
        self.assertIsNone(sintatico["ast"])
        self.assertEqual(sintatico["erros"], [])
        self.assertIn("não executada", sintatico["mensagem"])

    def test_requisicao_vazia_continua_como_na_etapa_2(self):
        resposta = self.cliente.post("/analisar", json={"codigo": "   "})
        self.assertEqual(resposta.status_code, 400)
        self.assertNotIn("sintatico", resposta.get_json())

    def test_codigo_grande_omite_detalhes(self):
        codigo = "x = 1\n" * 1100  # 4400 tokens
        status, dados = self.analisar(codigo)
        self.assertEqual(status, 200)
        sintatico = dados["sintatico"]
        self.assertTrue(sintatico["sucesso"])
        self.assertTrue(sintatico["detalhes_omitidos"])
        self.assertIsNone(sintatico["passos"])
        self.assertIsNotNone(sintatico["ast"])

    def test_falha_interna_do_parser_nao_expoe_detalhes(self):
        with mock.patch("app.analisar_sintaticamente",
                        side_effect=RuntimeError("segredo interno")):
            app.logger.disabled = True
            try:
                resposta = self.cliente.post("/analisar", json={"codigo": "x = 1"})
            finally:
                app.logger.disabled = False
        self.assertEqual(resposta.status_code, 500)
        self.assertNotIn("segredo interno", resposta.get_data(as_text=True))

    def test_endpoint_gramatica(self):
        resposta = self.cliente.get("/gramatica")
        dados = resposta.get_json()
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(dados["simbolo_inicial"], "programa")
        nomes = [r["nome"] for r in dados["regras"]]
        self.assertEqual(nomes[0], "programa")
        self.assertIn("soma", nomes)
        self.assertIn("ADICAO", [t["tipo"] for t in dados["tipos_no"]])


class TestEndpointsIA(unittest.TestCase):
    """O endpoint de IA usa um Ollama simulado: os testes não precisam do modelo."""

    def setUp(self):
        self.cliente = app.test_client()

    def test_status_sem_configuracao(self):
        with mock.patch("ia.BASE_URL", ""):
            dados = self.cliente.get("/ia/status").get_json()
        self.assertFalse(dados["disponivel"])
        self.assertFalse(dados["configurado"])

    def test_explicar_sem_ia_retorna_503_e_analise_continua(self):
        with mock.patch("ia.BASE_URL", ""):
            resposta = self.cliente.post("/ia/explicar", json={
                "codigo": "x = 1", "alvo": {"tipo": "no", "id": 0}})
        self.assertEqual(resposta.status_code, 503)
        self.assertFalse(resposta.get_json()["sucesso"])
        self.assertEqual(
            self.cliente.post("/analisar", json={"codigo": "x = 1"}).status_code, 200)

    def test_explicar_com_ia_simulada(self):
        with mock.patch("ia.BASE_URL", "http://ollama:11434"), \
             mock.patch("ia._requisitar",
                        return_value={"message": {"content": "  Explicação.  "}}) as falso:
            resposta = self.cliente.post("/ia/explicar", json={
                "codigo": "resultado = 10 + 5 * 2", "alvo": {"tipo": "no", "id": 4}})
        self.assertEqual(resposta.status_code, 200)
        dados = resposta.get_json()
        self.assertEqual(dados["resposta"], "Explicação.")
        self.assertTrue(dados["gerado_por_ia"])
        corpo = falso.call_args[0][1]
        self.assertEqual(corpo["messages"][0]["role"], "system")
        # O id 4 é o nó MULTIPLICACAO (ids seguem a ordem de criação).
        self.assertIn("Nó selecionado da AST:\n- MULTIPLICACAO", corpo["messages"][1]["content"])

    def test_pedidos_invalidos(self):
        casos = [
            "nao é objeto",
            {"alvo": {"tipo": "desconhecido"}},
            {"alvo": {"tipo": "conceito"}},
            {"alvo": {"tipo": "no", "id": 0}},
            {"codigo": "x = 1", "alvo": {"tipo": "no", "id": 999}},
            {"codigo": "x = 1", "alvo": {"tipo": "token", "indice": -1}},
            {"codigo": "x = 1", "alvo": {"tipo": "conceito"}, "pergunta": "a" * 601},
            {"codigo": "x" * 4001, "alvo": {"tipo": "conceito"}, "pergunta": "oi"},
        ]
        for corpo in casos:
            with self.subTest(corpo=str(corpo)[:40]):
                resposta = self.cliente.post("/ia/explicar", json=corpo)
                self.assertEqual(resposta.status_code, 400)
                self.assertFalse(resposta.get_json()["sucesso"])


if __name__ == "__main__":
    unittest.main()
    
