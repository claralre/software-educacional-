
import unittest
from app import app


class TestBackend(unittest.TestCase):

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


if __name__ == "__main__":
    unittest.main()
