import unittest

from scanner import (
    DELIMITADORES,
    OPERADORES,
    PALAVRAS_RESERVADAS,
    analisar_lexicamente,
)


def tokens(codigo):
    return analisar_lexicamente(codigo)["tokens"]


def pares(codigo, ignorar_estrutura=True):
    """Lista (tipo, lexema) sem os tokens estruturais, para comparar."""
    estruturais = {"NOVA_LINHA", "INDENTA", "DEDENTA", "FIM"}
    return [
        (t["tipo"], t["lexema"]) for t in tokens(codigo)
        if not (ignorar_estrutura and t["tipo"] in estruturais)
    ]


def erros(codigo):
    return analisar_lexicamente(codigo)["erros"]


class TestPalavrasReservadas(unittest.TestCase):

    def test_cada_palavra_reservada(self):
        for palavra in PALAVRAS_RESERVADAS:
            with self.subTest(palavra=palavra):
                self.assertEqual(pares(palavra), [("PALAVRA_RESERVADA", palavra)])

    def test_diferencia_maiusculas(self):
        # Python diferencia maiúsculas: "If" e "true" são identificadores.
        self.assertEqual(pares("If true"), [
            ("IDENTIFICADOR", "If"), ("IDENTIFICADOR", "true"),
        ])

    def test_palavra_como_prefixo_de_identificador(self):
        self.assertEqual(pares("iffy whiles"), [
            ("IDENTIFICADOR", "iffy"), ("IDENTIFICADOR", "whiles"),
        ])

    def test_operadores_logicos_sao_palavras_reservadas(self):
        for palavra in ("and", "or", "not"):
            with self.subTest(palavra=palavra):
                self.assertIn("operador lógico", tokens(palavra)[0]["descricao"])


class TestIdentificadores(unittest.TestCase):

    def test_formacoes_validas(self):
        for nome in ("x", "numero", "_x1", "__init__", "valor_total", "A1b2", "média"):
            with self.subTest(nome=nome):
                self.assertEqual(pares(nome), [("IDENTIFICADOR", nome)])

    def test_identificador_iniciado_por_digito_e_erro(self):
        lista = erros("1abc = 2")
        self.assertEqual(len(lista), 1)
        self.assertEqual(lista[0]["lexema"], "1abc")
        self.assertIn("malformado", lista[0]["mensagem"])

    def test_identificador_com_caractere_invalido(self):
        self.assertEqual(pares("valor$"), [("IDENTIFICADOR", "valor")])
        self.assertEqual(erros("valor$")[0]["lexema"], "$")


class TestLiterais(unittest.TestCase):

    def test_inteiros(self):
        for numero in ("0", "7", "42", "1000", "1_000", "00"):
            with self.subTest(numero=numero):
                self.assertEqual(pares(numero), [("LITERAL_INTEIRO", numero)])

    def test_reais(self):
        for numero in ("3.14", "0.5", ".5", "2.", "1e10", "1.5e-3", "2E+4", "1.e5"):
            with self.subTest(numero=numero):
                self.assertEqual(pares(numero), [("LITERAL_REAL", numero)])

    def test_strings(self):
        for texto in ('"ola"', "'ola'", '""', '"com \\" aspas"',
                      "'linha\\n'", 'f"nome {x}"', "r'\\d'", '"""várias\nlinhas"""'):
            with self.subTest(texto=texto):
                self.assertEqual(pares(texto), [("LITERAL_STRING", texto)])

    def test_string_com_caracteres_fora_do_escopo(self):
        # Dentro de strings qualquer caractere é permitido.
        self.assertEqual(erros('"email@site.com $ # ?"'), [])

    def test_literais_constantes(self):
        self.assertEqual(pares("True False None"), [
            ("PALAVRA_RESERVADA", "True"),
            ("PALAVRA_RESERVADA", "False"),
            ("PALAVRA_RESERVADA", "None"),
        ])

    def test_inteiro_com_zero_a_esquerda_e_erro(self):
        lista = erros("x = 007")
        self.assertEqual(len(lista), 1)
        self.assertEqual(lista[0]["lexema"], "007")

    def test_real_com_dois_pontos_e_erro(self):
        self.assertEqual(erros("3.14.15")[0]["lexema"], "3.14.15")

    def test_sublinhado_invalido_em_numero(self):
        for numero in ("1__0", "10_"):
            with self.subTest(numero=numero):
                self.assertEqual(erros(numero)[0]["lexema"], numero)

    def test_string_nao_fechada(self):
        lista = erros('nome = "Ana\nidade = 3')
        self.assertEqual(len(lista), 1)
        self.assertEqual((lista[0]["linha"], lista[0]["coluna"]), (1, 8))
        self.assertIn("não foi fechada", lista[0]["mensagem"])
        # O scanner continua na linha seguinte.
        self.assertIn(("IDENTIFICADOR", "idade"), pares('nome = "Ana\nidade = 3'))

    def test_string_tripla_nao_fechada(self):
        lista = erros('x = """texto\nsem fim')
        self.assertEqual(len(lista), 1)
        self.assertIn('"""', lista[0]["mensagem"])


class TestOperadores(unittest.TestCase):

    def test_cada_operador(self):
        for operador in OPERADORES:
            with self.subTest(operador=operador):
                self.assertEqual(pares(f"a {operador} b"), [
                    ("IDENTIFICADOR", "a"),
                    ("OPERADOR", operador),
                    ("IDENTIFICADOR", "b"),
                ])

    def test_operadores_compostos_sem_espaco(self):
        self.assertEqual(pares("a==b!=c<=d>=e"), [
            ("IDENTIFICADOR", "a"), ("OPERADOR", "=="),
            ("IDENTIFICADOR", "b"), ("OPERADOR", "!="),
            ("IDENTIFICADOR", "c"), ("OPERADOR", "<="),
            ("IDENTIFICADOR", "d"), ("OPERADOR", ">="),
            ("IDENTIFICADOR", "e"),
        ])

    def test_casamento_mais_longo(self):
        self.assertEqual(pares("x **= 2"), [
            ("IDENTIFICADOR", "x"), ("OPERADOR", "**="), ("LITERAL_INTEIRO", "2"),
        ])
        self.assertEqual(pares("a===b"), [
            ("IDENTIFICADOR", "a"), ("OPERADOR", "=="),
            ("OPERADOR", "="), ("IDENTIFICADOR", "b"),
        ])

    def test_exclamacao_sozinha_e_erro(self):
        lista = erros("!x")
        self.assertEqual(lista[0]["lexema"], "!")
        self.assertIn("not", lista[0]["dica"])


class TestDelimitadores(unittest.TestCase):

    def test_cada_delimitador(self):
        for delimitador in DELIMITADORES:
            with self.subTest(delimitador=delimitador):
                self.assertIn(("DELIMITADOR", delimitador), pares(delimitador))

    def test_parenteses_nao_fechado(self):
        lista = erros("print(1")
        self.assertEqual(len(lista), 1)
        self.assertEqual(lista[0]["lexema"], "(")
        self.assertEqual((lista[0]["linha"], lista[0]["coluna"]), (1, 6))


class TestComentariosEEspacos(unittest.TestCase):

    def test_comentario_de_linha_e_ignorado(self):
        self.assertEqual(pares("x = 1  # comentário"), [
            ("IDENTIFICADOR", "x"), ("OPERADOR", "="), ("LITERAL_INTEIRO", "1"),
        ])

    def test_comentario_e_registrado_a_parte(self):
        resultado = analisar_lexicamente("x = 1  # nota")
        self.assertEqual(resultado["comentarios"], [
            {"lexema": "# nota", "linha": 1, "coluna": 8},
        ])

    def test_espacos_nao_geram_tokens(self):
        self.assertEqual(pares("x=1"), pares("x   =    1"))

    def test_tabulacao_entre_tokens(self):
        self.assertEqual(pares("x\t=\t1"), [
            ("IDENTIFICADOR", "x"), ("OPERADOR", "="), ("LITERAL_INTEIRO", "1"),
        ])


class TestEstruturaDeLinhas(unittest.TestCase):

    def test_nova_linha_e_fim(self):
        tipos = [t["tipo"] for t in tokens("x = 1\ny = 2\n")]
        self.assertEqual(tipos, [
            "IDENTIFICADOR", "OPERADOR", "LITERAL_INTEIRO", "NOVA_LINHA",
            "IDENTIFICADOR", "OPERADOR", "LITERAL_INTEIRO", "NOVA_LINHA",
            "FIM",
        ])

    def test_linhas_em_branco_nao_geram_nova_linha(self):
        tipos = [t["tipo"] for t in tokens("x = 1\n\n\n# nota\ny = 2")]
        self.assertEqual(tipos.count("NOVA_LINHA"), 2)

    def test_indentacao_gera_indenta_e_dedenta(self):
        codigo = "if x:\n    y = 1\nz = 2\n"
        tipos = [t["tipo"] for t in tokens(codigo)]
        self.assertEqual(tipos, [
            "PALAVRA_RESERVADA", "IDENTIFICADOR", "DELIMITADOR", "NOVA_LINHA",
            "INDENTA", "IDENTIFICADOR", "OPERADOR", "LITERAL_INTEIRO", "NOVA_LINHA",
            "DEDENTA", "IDENTIFICADOR", "OPERADOR", "LITERAL_INTEIRO", "NOVA_LINHA",
            "FIM",
        ])

    def test_blocos_abertos_sao_fechados_no_fim(self):
        tipos = [t["tipo"] for t in tokens("if a:\n    if b:\n        c = 1")]
        self.assertEqual(tipos[-3:], ["DEDENTA", "DEDENTA", "FIM"])

    def test_indentacao_inconsistente_e_erro(self):
        lista = erros("if a:\n        b = 1\n    c = 2\n")
        self.assertEqual(len(lista), 1)
        self.assertEqual(lista[0]["linha"], 3)
        self.assertIn("indentação", lista[0]["mensagem"])

    def test_mistura_de_tabulacao_e_espaco_e_erro(self):
        lista = erros("if a:\n \tb = 1\n")
        self.assertEqual(len(lista), 1)
        self.assertIn("tabulações", lista[0]["mensagem"])

    def test_quebra_dentro_de_parenteses_e_ignorada(self):
        tipos = [t["tipo"] for t in tokens("f(1,\n  2)\n")]
        self.assertEqual(tipos.count("NOVA_LINHA"), 1)
        self.assertNotIn("INDENTA", tipos)

    def test_continuacao_com_barra_invertida(self):
        self.assertEqual(pares("x = 1 + \\\n    2"), [
            ("IDENTIFICADOR", "x"), ("OPERADOR", "="), ("LITERAL_INTEIRO", "1"),
            ("OPERADOR", "+"), ("LITERAL_INTEIRO", "2"),
        ])
        self.assertEqual(erros("x = 1 + \\\n    2"), [])


class TestPosicao(unittest.TestCase):

    def test_posicoes_na_primeira_linha(self):
        posicoes = [(t["lexema"], t["linha"], t["coluna"]) for t in tokens("int numero = 10;")[:5]]
        self.assertEqual(posicoes, [
            ("int", 1, 1), ("numero", 1, 5), ("=", 1, 12), ("10", 1, 14), (";", 1, 16),
        ])

    def test_posicoes_em_varias_linhas(self):
        lista = tokens("a = 1\n\n   \n  # x\nbeta = 22")
        beta = [t for t in lista if t["lexema"] == "beta"][0]
        vinte_e_dois = [t for t in lista if t["lexema"] == "22"][0]
        self.assertEqual((beta["linha"], beta["coluna"]), (5, 1))
        self.assertEqual((vinte_e_dois["linha"], vinte_e_dois["coluna"]), (5, 8))

    def test_posicao_apos_string_de_varias_linhas(self):
        lista = tokens('s = """a\nb"""\nx = 1')
        x = [t for t in lista if t["lexema"] == "x"][0]
        self.assertEqual((x["linha"], x["coluna"]), (3, 1))

    def test_quebra_de_linha_windows(self):
        lista = tokens("a = 1\r\nb = 2")
        b = [t for t in lista if t["lexema"] == "b"][0]
        self.assertEqual((b["linha"], b["coluna"]), (2, 1))


class TestErrosLexicos(unittest.TestCase):

    def test_caracteres_nao_reconhecidos(self):
        for caractere in ("@", "$", "?", "`", "&", "|", "^", "~"):
            with self.subTest(caractere=caractere):
                lista = erros(f"x = {caractere}")
                self.assertEqual(len(lista), 1)
                erro = lista[0]
                self.assertEqual(erro["tipo"], "ERRO_LEXICO")
                self.assertEqual(erro["lexema"], caractere)
                self.assertEqual((erro["linha"], erro["coluna"]), (1, 5))
                self.assertIn("caractere não reconhecido", erro["mensagem"])

    def test_formato_do_erro(self):
        erro = erros("x = 1\nresultado = @")[0]
        self.assertEqual(set(erro), {"tipo", "lexema", "linha", "coluna", "mensagem", "dica"})
        self.assertEqual(
            erro["mensagem"],
            "Erro léxico na linha 2, coluna 13: caractere não reconhecido '@'.",
        )

    def test_acumula_varios_erros_e_continua(self):
        resultado = analisar_lexicamente("a = @\nb = $\nc = 3")
        self.assertEqual([e["lexema"] for e in resultado["erros"]], ["@", "$"])
        self.assertIn("c", [t["lexema"] for t in resultado["tokens"]])

    def test_erros_ordenados_por_posicao(self):
        lista = erros("f(\n@")
        self.assertEqual([(e["linha"], e["coluna"]) for e in lista], [(1, 2), (2, 1)])

    def test_erro_sintatico_nao_e_erro_lexico(self):
        # Tokens válidos em ordem errada são tarefa do parser (Etapa 4).
        self.assertEqual(erros("= = if 10 ) else"), [])


class TestCasosDeBorda(unittest.TestCase):

    def test_codigo_vazio(self):
        resultado = analisar_lexicamente("")
        self.assertEqual([t["tipo"] for t in resultado["tokens"]], ["FIM"])
        self.assertEqual(resultado["erros"], [])

    def test_apenas_espacos(self):
        resultado = analisar_lexicamente("   \n\t\n  ")
        self.assertEqual([t["tipo"] for t in resultado["tokens"]], ["FIM"])
        self.assertEqual(resultado["erros"], [])

    def test_apenas_comentarios(self):
        resultado = analisar_lexicamente("# um\n# dois")
        self.assertEqual([t["tipo"] for t in resultado["tokens"]], ["FIM"])
        self.assertEqual(len(resultado["comentarios"]), 2)

    def test_token_no_fim_sem_quebra_de_linha(self):
        lista = tokens("x = 10")
        self.assertEqual((lista[2]["lexema"], lista[2]["linha"], lista[2]["coluna"]), ("10", 1, 5))
        self.assertEqual([t["tipo"] for t in lista[-2:]], ["NOVA_LINHA", "FIM"])

    def test_resumo_conta_por_tipo(self):
        resumo = analisar_lexicamente("x = x + 1")["resumo"]
        self.assertEqual(resumo["por_tipo"]["IDENTIFICADOR"], 2)
        self.assertEqual(resumo["por_tipo"]["OPERADOR"], 2)
        self.assertEqual(resumo["total_tokens"], sum(resumo["por_tipo"].values()))

    def test_formato_do_token(self):
        token = tokens("numero")[0]
        self.assertEqual(
            set(token), {"tipo", "lexema", "linha", "coluna", "descricao", "explicacao"}
        )


if __name__ == "__main__":
    unittest.main()
