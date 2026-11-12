import unittest

from analisador_sintatico import GRAMATICA, TIPOS_NO, analisar_sintaticamente
from scanner import analisar_lexicamente


def analisar(codigo):
    lexico = analisar_lexicamente(codigo)
    assert not lexico["erros"], lexico["erros"]
    return analisar_sintaticamente(lexico["tokens"])


def ast(codigo):
    resultado = analisar(codigo)
    assert resultado["sucesso"], resultado["erros"]
    return resultado["ast"]


def erros(codigo):
    return analisar(codigo)["erros"]


def resumo(no):
    """Notação compacta da AST, usada como referência nos testes.

    Literais e nomes aparecem pelo valor; os demais nós como TIPO(filhos).
    """
    if no["tipo"] == "IDENTIFICADOR":
        return no["atributos"]["nome"]
    if no["tipo"] in ("NUMERO_INTEIRO", "NUMERO_REAL", "TEXTO", "LOGICO", "NULO"):
        return no["atributos"]["valor"]
    filhos = ", ".join(resumo(f) for f in no["filhos"])
    operador = no["atributos"].get("operador")
    nome = no["tipo"] + (f"[{operador}]" if operador and no["tipo"] in (
        "COMPARACAO", "OPERACAO_LOGICA", "ATRIBUICAO", "UNARIO") else "")
    return f"{nome}({filhos})"


def expressao(codigo):
    """Resumo da expressão do lado direito de 'x = ...'."""
    programa = ast(f"x = {codigo}")
    return resumo(programa["filhos"][0]["filhos"][1])


class TestPrecedenciaEAssociatividade(unittest.TestCase):

    def test_multiplicacao_antes_da_adicao(self):
        self.assertEqual(expressao("10 + 5 * 2"), "ADICAO(10, MULTIPLICACAO(5, 2))")
        self.assertEqual(expressao("2 + 3 * 4"), "ADICAO(2, MULTIPLICACAO(3, 4))")
        self.assertEqual(expressao("2 * 3 + 4"), "ADICAO(MULTIPLICACAO(2, 3), 4)")

    def test_subtracao_associativa_a_esquerda(self):
        self.assertEqual(expressao("20 - 5 - 3"), "SUBTRACAO(SUBTRACAO(20, 5), 3)")
        self.assertEqual(expressao("10 - 3 - 2"), "SUBTRACAO(SUBTRACAO(10, 3), 2)")

    def test_divisao_associativa_a_esquerda(self):
        self.assertEqual(expressao("8 / 4 / 2"), "DIVISAO(DIVISAO(8, 4), 2)")

    def test_parenteses_mudam_a_arvore(self):
        self.assertEqual(expressao("(10 + 5) * 2"), "MULTIPLICACAO(ADICAO(10, 5), 2)")
        self.assertEqual(expressao("20 - (5 - 3)"), "SUBTRACAO(20, SUBTRACAO(5, 3))")

    def test_parenteses_nao_viram_no(self):
        self.assertEqual(expressao("((7))"), "7")

    def test_potencia_associativa_a_direita(self):
        self.assertEqual(expressao("2 ** 3 ** 2"), "POTENCIA(2, POTENCIA(3, 2))")

    def test_menos_unario_e_potencia(self):
        # Como em Python: -2 ** 2 == -(2 ** 2)
        self.assertEqual(expressao("-2 ** 2"), "UNARIO[-](POTENCIA(2, 2))")
        self.assertEqual(expressao("2 ** -1"), "POTENCIA(2, UNARIO[-](1))")

    def test_demais_operadores_aritmeticos(self):
        self.assertEqual(expressao("7 // 2 % 3"), "RESTO(DIVISAO_INTEIRA(7, 2), 3)")

    def test_comparacao_abaixo_da_aritmetica(self):
        self.assertEqual(expressao("a + 1 > b * 2"),
                         "COMPARACAO[>](ADICAO(a, 1), MULTIPLICACAO(b, 2))")

    def test_precedencia_logica(self):
        # not > and > or
        self.assertEqual(
            expressao("a or b and not c"),
            "OPERACAO_LOGICA[or](a, OPERACAO_LOGICA[and](b, NEGACAO(c)))")
        self.assertEqual(expressao("not a == b"), "NEGACAO(COMPARACAO[==](a, b))")

    def test_operadores_de_comparacao_com_palavras(self):
        self.assertEqual(expressao("x in lista"), "COMPARACAO[in](x, lista)")
        self.assertEqual(expressao("x not in lista"), "COMPARACAO[not in](x, lista)")
        self.assertEqual(expressao("x is None"), "COMPARACAO[is](x, None)")
        self.assertEqual(expressao("x is not None"), "COMPARACAO[is not](x, None)")


class TestConstrucoesValidas(unittest.TestCase):

    def test_atribuicao(self):
        self.assertEqual(resumo(ast("idade = 21")), "PROGRAMA(ATRIBUICAO[=](idade, 21))")

    def test_atribuicao_composta(self):
        self.assertEqual(resumo(ast("x += 1")), "PROGRAMA(ATRIBUICAO[+=](x, 1))")

    def test_atribuicao_a_item_de_lista(self):
        self.assertEqual(resumo(ast("v[0] = 5")), "PROGRAMA(ATRIBUICAO[=](INDEXACAO(v, 0), 5))")

    def test_literais(self):
        self.assertEqual(
            resumo(ast('x = [1, 2.5, "a", True, None]')),
            'PROGRAMA(ATRIBUICAO[=](x, LISTA(1, 2.5, "a", True, None)))')

    def test_lista_vazia_e_virgula_final(self):
        self.assertEqual(expressao("[]"), "LISTA()")
        self.assertEqual(expressao("[1, 2,]"), "LISTA(1, 2)")

    def test_chamada_indexacao_e_atributo(self):
        self.assertEqual(
            resumo(ast("lista.append(v[i + 1])")),
            "PROGRAMA(COMANDO_EXPRESSAO(CHAMADA(ACESSO_ATRIBUTO(lista), "
            "INDEXACAO(v, ADICAO(i, 1)))))")
        self.assertEqual(resumo(ast("print()")), "PROGRAMA(COMANDO_EXPRESSAO(CHAMADA(print)))")

    def test_if_elif_else(self):
        codigo = (
            "if nota >= 7:\n"
            "    situacao = 'aprovado'\n"
            "elif nota >= 5:\n"
            "    situacao = 'recuperação'\n"
            "else:\n"
            "    situacao = 'reprovado'\n"
        )
        self.assertEqual(
            resumo(ast(codigo)),
            "PROGRAMA(SE(COMPARACAO[>=](nota, 7), "
            "BLOCO(ATRIBUICAO[=](situacao, 'aprovado')), "
            "SENAO_SE(COMPARACAO[>=](nota, 5), BLOCO(ATRIBUICAO[=](situacao, 'recuperação'))), "
            "BLOCO(ATRIBUICAO[=](situacao, 'reprovado'))))")

    def test_papeis_dos_filhos_do_if(self):
        no = ast("if a:\n    b = 1\nelse:\n    b = 2")["filhos"][0]
        self.assertEqual([f["papel"] for f in no["filhos"]], ["condicao", "entao", "senao"])

    def test_while(self):
        self.assertEqual(
            resumo(ast("while i < 3:\n    i += 1\n")),
            "PROGRAMA(ENQUANTO(COMPARACAO[<](i, 3), BLOCO(ATRIBUICAO[+=](i, 1))))")

    def test_for(self):
        no = ast("for i in range(3):\n    print(i)")["filhos"][0]
        self.assertEqual(no["tipo"], "PARA")
        self.assertEqual(no["atributos"]["variavel"], "i")
        self.assertEqual([f["papel"] for f in no["filhos"]], ["variavel", "iteravel", "corpo"])

    def test_funcao_com_parametros_e_retorno(self):
        no = ast("def soma(a, b):\n    return a + b\n")["filhos"][0]
        self.assertEqual(no["tipo"], "FUNCAO")
        self.assertEqual(no["atributos"], {"nome": "soma", "parametros": ["a", "b"]})
        self.assertEqual(resumo(no), "FUNCAO(PARAMETRO(), PARAMETRO(), BLOCO(RETORNO(ADICAO(a, b))))")

    def test_funcao_sem_parametros_e_retorno_vazio(self):
        self.assertEqual(resumo(ast("def f():\n    return\n")),
                         "PROGRAMA(FUNCAO(BLOCO(RETORNO())))")

    def test_pass_break_continue(self):
        self.assertEqual(
            resumo(ast("while True:\n    pass\n    break\n    continue\n")),
            "PROGRAMA(ENQUANTO(True, BLOCO(PASSE(), INTERROMPE(), CONTINUA())))")

    def test_bloco_na_mesma_linha(self):
        self.assertEqual(resumo(ast("if x: y = 1")),
                         "PROGRAMA(SE(x, BLOCO(ATRIBUICAO[=](y, 1))))")

    def test_varios_comandos_com_ponto_e_virgula(self):
        self.assertEqual(resumo(ast("a = 1; b = 2;")),
                         "PROGRAMA(ATRIBUICAO[=](a, 1), ATRIBUICAO[=](b, 2))")

    def test_construcoes_aninhadas(self):
        codigo = (
            "def classificar(lista):\n"
            "    for n in lista:\n"
            "        while n > 0:\n"
            "            if n % 2 == 0:\n"
            "                print(n)\n"
            "            n -= 1\n"
            "    return lista\n"
        )
        funcao = ast(codigo)["filhos"][0]
        para = funcao["filhos"][1]["filhos"][0]
        enquanto = para["filhos"][2]["filhos"][0]
        se = enquanto["filhos"][1]["filhos"][0]
        self.assertEqual([funcao["tipo"], para["tipo"], enquanto["tipo"], se["tipo"]],
                         ["FUNCAO", "PARA", "ENQUANTO", "SE"])
        self.assertEqual(resumo(se["filhos"][0]),
                         "COMPARACAO[==](RESTO(n, 2), 0)")

    def test_programa_com_varios_comandos(self):
        self.assertEqual(len(ast("a = 1\nb = 2\nprint(a + b)\n")["filhos"]), 3)

    def test_quebra_de_linha_dentro_de_parenteses(self):
        self.assertEqual(expressao("(1 +\n     2)"), "ADICAO(1, 2)")


class TestEstruturaDosNos(unittest.TestCase):

    def test_formato_de_todos_os_nos(self):
        chaves = {"id", "tipo", "rotulo", "categoria", "regra", "papel", "atributos",
                  "linha", "coluna", "linha_fim", "coluna_fim", "filhos"}

        def verificar(no):
            self.assertEqual(set(no), chaves)
            self.assertIn(no["tipo"], TIPOS_NO)
            self.assertIn(no["regra"], GRAMATICA)
            for filho in no["filhos"]:
                verificar(filho)

        verificar(ast("def f(a):\n    if a: return [a, 1]\n    x = -a.b(2)[0]\n"))

    def test_ids_unicos(self):
        ids = []

        def coletar(no):
            ids.append(no["id"])
            for filho in no["filhos"]:
                coletar(filho)

        coletar(ast("x = 1 + 2\nif x: print(x)"))
        self.assertEqual(len(ids), len(set(ids)))

    def test_regra_de_cada_no(self):
        atribuicao = ast("x = 1 + 2 * 3")["filhos"][0]
        adicao = atribuicao["filhos"][1]
        self.assertEqual(adicao["regra"], "soma")
        self.assertEqual(adicao["filhos"][1]["regra"], "termo")
        self.assertEqual(adicao["filhos"][0]["regra"], "atomo")


class TestPosicoes(unittest.TestCase):

    def faixa(self, no):
        return (no["linha"], no["coluna"], no["linha_fim"], no["coluna_fim"])

    def test_posicoes_de_expressao(self):
        atribuicao = ast("resultado = 10 + 5 * 2")["filhos"][0]
        adicao = atribuicao["filhos"][1]
        self.assertEqual(self.faixa(atribuicao), (1, 1, 1, 22))
        self.assertEqual(self.faixa(adicao), (1, 13, 1, 22))
        self.assertEqual(self.faixa(adicao["filhos"][0]), (1, 13, 1, 14))
        self.assertEqual(self.faixa(adicao["filhos"][1]), (1, 18, 1, 22))

    def test_posicoes_incluem_parenteses(self):
        multiplicacao = ast("x = (1 + 2) * 3")["filhos"][0]["filhos"][1]
        self.assertEqual(self.faixa(multiplicacao["filhos"][0]), (1, 5, 1, 11))
        self.assertTrue(multiplicacao["filhos"][0]["atributos"]["entre_parenteses"])

    def test_posicoes_em_varias_linhas(self):
        se = ast("x = 0\nif x > 1:\n    y = 2\n    z = 3\n")["filhos"][1]
        self.assertEqual(self.faixa(se), (2, 1, 4, 9))
        self.assertEqual(self.faixa(se["filhos"][1]), (3, 5, 4, 9))

    def test_posicao_de_string_de_varias_linhas(self):
        texto = ast('s = """a\nbc"""')["filhos"][0]["filhos"][1]
        self.assertEqual(self.faixa(texto), (1, 5, 2, 5))

    def test_posicoes_coincidem_com_tokens(self):
        codigo = "total = preco * 2"
        tokens = analisar_lexicamente(codigo)["tokens"]
        atribuicao = ast(codigo)["filhos"][0]
        preco = atribuicao["filhos"][1]["filhos"][0]
        token = [t for t in tokens if t["lexema"] == "preco"][0]
        self.assertEqual((preco["linha"], preco["coluna"]), (token["linha"], token["coluna"]))


class TestErrosSintaticos(unittest.TestCase):

    def um_erro(self, codigo):
        lista = erros(codigo)
        self.assertEqual(len(lista), 1, lista)
        return lista[0]

    def test_formato_do_erro(self):
        erro = self.um_erro("x = 5 +")
        self.assertEqual(set(erro), {"tipo", "linha", "coluna", "encontrado",
                                     "encontrado_descricao", "esperado", "mensagem",
                                     "regra", "producao", "dica"})
        self.assertEqual(erro["tipo"], "ERRO_SINTATICO")
        self.assertEqual(erro["producao"], GRAMATICA[erro["regra"]])
        self.assertIsInstance(erro["esperado"], list)

    def test_expressao_sem_operando(self):
        erro = self.um_erro("x = 5 +")
        self.assertEqual((erro["linha"], erro["coluna"]), (1, 8))
        self.assertEqual(erro["encontrado"], "NOVA_LINHA")
        self.assertIn("depois de '+'", erro["mensagem"])

    def test_operadores_consecutivos(self):
        erro = self.um_erro("x = 5 + * 3")
        self.assertEqual((erro["linha"], erro["coluna"], erro["encontrado"]), (1, 9, "*"))
        self.assertIn("operadores consecutivos", erro["mensagem"])

    def test_falta_dois_pontos(self):
        erro = self.um_erro("if x > 1\n    y = 2\n")
        self.assertEqual(erro["esperado"], ["':'"])
        self.assertEqual(erro["regra"], "se")
        self.assertIn("condição do 'if'", erro["mensagem"])

    def test_falta_fechar_parenteses(self):
        erro = self.um_erro("print(1 2)")
        self.assertEqual(erro["esperado"], ["')'"])
        self.assertEqual(erro["encontrado"], "2")
        self.assertIn("aberto na linha 1, coluna 6", erro["mensagem"])
        self.assertIn("vírgula", erro["dica"])

    def test_falta_fechar_colchete_da_indexacao(self):
        erro = self.um_erro("x = v[1 2]")
        self.assertEqual(erro["esperado"], ["']'"])

    def test_else_sem_if(self):
        erro = self.um_erro("else:\n    x = 1\n")
        self.assertIn("'else' sem um 'if'", erro["mensagem"])
        erro = self.um_erro("x = 1\nelif x:\n    pass")
        self.assertIn("'elif' sem um 'if'", erro["mensagem"])

    def test_palavra_reservada_como_nome(self):
        erro = self.um_erro("def if(x):\n    pass")
        self.assertIn("palavra reservada 'if'", erro["mensagem"])
        erro = self.um_erro("for while in x:\n    pass")
        self.assertEqual(erro["encontrado"], "while")

    def test_palavra_reservada_como_variavel(self):
        erro = self.um_erro("if = 5")
        self.assertIn("condição", erro["mensagem"])
        self.assertIn("palavra reservada", erro["dica"])

    def test_dois_valores_sem_operador(self):
        erro = self.um_erro("x = 5 6")
        self.assertEqual(erro["encontrado"], "6")
        self.assertIn("operador", erro["dica"])

    def test_bloco_sem_indentacao(self):
        erro = self.um_erro("if x:\ny = 1\n")
        self.assertEqual((erro["linha"], erro["coluna"]), (2, 1))
        self.assertIn("bloco indentado", erro["mensagem"])

    def test_fim_inesperado_do_codigo(self):
        erro = self.um_erro("if x:")
        self.assertEqual(erro["encontrado"], "FIM")
        self.assertIn("o código terminou", erro["mensagem"])
        erro = self.um_erro("for i in")
        self.assertIn("terminou", erro["mensagem"])

    def test_indentacao_inesperada(self):
        erro = self.um_erro("x = 1\n    y = 2\n")
        self.assertIn("indentação inesperada", erro["mensagem"])

    def test_atribuicao_invalida(self):
        self.assertIn("literal", self.um_erro("5 = x")["mensagem"])
        self.assertIn("True", self.um_erro("True = 1")["mensagem"])
        self.assertIn("chamada de função", self.um_erro("f(x) = 3")["mensagem"])

    def test_construcoes_fora_do_subconjunto(self):
        for codigo in ("class A:\n    pass", "import math", "x = lambda: 1",
                       "a < b < c", "a = b = 0", "def f(x=1):\n    pass"):
            with self.subTest(codigo=codigo):
                self.assertEqual(len(erros(codigo)), 1)
        self.assertIn("não faz parte do subconjunto", self.um_erro("import math")["mensagem"])

    def test_comando_composto_depois_de_ponto_e_virgula(self):
        self.assertIn("linha própria", self.um_erro("x = 1; if x: pass")["mensagem"])

    def test_aninhamento_excessivo_nao_quebra(self):
        codigo = "x = " + "(" * 200 + "1" + ")" * 200
        erro = self.um_erro(codigo)
        self.assertIn("aninhadas demais", erro["mensagem"])


class TestRecuperacaoDeErros(unittest.TestCase):

    def test_acumula_erros_de_comandos_diferentes(self):
        lista = erros("x = 5 +\ny = * 2\nz = 1\nw =\n")
        self.assertEqual([e["linha"] for e in lista], [1, 2, 4])

    def test_nao_gera_erros_em_cascata_no_bloco(self):
        # O 'if' sem ':' gera um erro só: o bloco indentado é descartado.
        lista = erros("if x > 1\n    y = 2\n    z = 3\nw = 4 +\n")
        self.assertEqual([e["linha"] for e in lista], [1, 4])

    def test_erro_dentro_de_bloco_nao_impede_o_resto(self):
        lista = erros("def f():\n    x = \n    return 1\nprint(f(\n)\ny = )\n")
        self.assertEqual([e["linha"] for e in lista], [2, 6])

    def test_sem_ast_quando_ha_erros(self):
        resultado = analisar("x = 1\ny = 2 +\n")
        self.assertFalse(resultado["sucesso"])
        self.assertIsNone(resultado["ast"])
        self.assertIsNone(resultado["derivacao"])


class TestCasosDeBorda(unittest.TestCase):

    def test_codigo_vazio(self):
        resultado = analisar("")
        self.assertTrue(resultado["sucesso"])
        self.assertEqual(resumo(resultado["ast"]), "PROGRAMA()")

    def test_apenas_comentarios(self):
        self.assertEqual(resumo(ast("# um\n# dois\n")), "PROGRAMA()")

    def test_unico_comando(self):
        self.assertEqual(resumo(ast("pass")), "PROGRAMA(PASSE())")

    def test_fim_no_meio_da_construcao(self):
        for codigo in ("while x", "for i in", "x = [1, 2,", "print(", "def f(", "x ="):
            lexico = analisar_lexicamente(codigo)
            if lexico["erros"]:
                continue  # parênteses não fechados já são erro léxico
            with self.subTest(codigo=codigo):
                self.assertGreaterEqual(len(analisar_sintaticamente(lexico["tokens"])["erros"]), 1)

    def test_resumo_conta_os_nos(self):
        resultado = analisar("x = 1 + 2")
        # PROGRAMA, ATRIBUICAO, IDENTIFICADOR, ADICAO e dois NUMERO_INTEIRO
        self.assertEqual(resultado["resumo"]["total_nos"], 6)
        self.assertEqual(resultado["resumo"]["por_tipo"]["NUMERO_INTEIRO"], 2)


class TestIntegracaoComScanner(unittest.TestCase):

    CODIGO = (
        "def media(a, b):\n"
        "    soma = a + b  # comentário\n"
        "    return soma / 2\n"
        "\n"
        "if media(8, 6.5) >= 7: print('ok')\n"
    )

    def test_parser_consome_todos_os_tokens_em_ordem(self):
        tokens = analisar_lexicamente(self.CODIGO)["tokens"]
        resultado = analisar_sintaticamente(tokens)
        consumidos = [p["token"] for p in resultado["passos"] if p["acao"] == "consumir"]
        self.assertEqual(consumidos, list(range(len(tokens))))

    def test_folhas_da_derivacao_sao_os_tokens(self):
        tokens = analisar_lexicamente(self.CODIGO)["tokens"]
        resultado = analisar_sintaticamente(tokens)

        def folhas(no):
            if "terminal" in no:
                return [(no["terminal"], no["lexema"])]
            return [folha for filho in no["filhos"] for folha in folhas(filho)]

        self.assertEqual(folhas(resultado["derivacao"]),
                         [(t["tipo"], t["lexema"]) for t in tokens])
        self.assertEqual(resultado["derivacao"]["regra"], "programa")

    def test_passos_criam_cada_no_uma_vez(self):
        resultado = analisar(self.CODIGO)
        criados = [p["no"] for p in resultado["passos"] if p["acao"] == "criar"]
        self.assertEqual(sorted(criados), list(range(resultado["resumo"]["total_nos"])))

    def test_entradas_e_saidas_de_regra_balanceadas(self):
        resultado = analisar(self.CODIGO)
        pilha = []
        for passo in resultado["passos"]:
            if passo["acao"] == "entrar":
                pilha.append(passo["regra"])
            elif passo["acao"] == "sair":
                self.assertEqual(pilha.pop(), passo["regra"])
        self.assertEqual(pilha, [])

    def test_sem_detalhes_quando_desligado(self):
        tokens = analisar_lexicamente("x = 1")["tokens"]
        resultado = analisar_sintaticamente(tokens, registrar_detalhes=False)
        self.assertTrue(resultado["sucesso"])
        self.assertIsNone(resultado["passos"])
        self.assertIsNone(resultado["derivacao"])


if __name__ == "__main__":
    unittest.main()
