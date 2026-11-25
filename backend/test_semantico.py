import builtins
import contextlib
import io
import unittest

from analisador_semantico import EMBUTIDAS, REGRAS, analisar_semanticamente
from analisador_sintatico import analisar_sintaticamente
from scanner import analisar_lexicamente


def analisar(codigo):
    lexico = analisar_lexicamente(codigo)
    assert not lexico["erros"], lexico["erros"]
    sintatico = analisar_sintaticamente(lexico["tokens"])
    assert sintatico["sucesso"], sintatico["erros"]
    return analisar_semanticamente(sintatico["ast"], lexico["tokens"]), sintatico, lexico


def regras(codigo, avisos=False):
    resultado = analisar(codigo)[0]
    return [d["regra"] for d in resultado["avisos" if avisos else "erros"]]


def simbolo(resultado, nome, escopo=None):
    for s in resultado["tabela_simbolos"]:
        if s["nome"] == nome and (escopo is None or s["escopo"] == escopo):
            return s
    raise AssertionError(f"símbolo {nome} não encontrado")


class TestTabelaDeSimbolos(unittest.TestCase):

    def test_variavel_global_com_tipo_inferido(self):
        r = analisar("idade = 21\nnome = 'Ana'\naltura = 1.7\nok = True\nv = [1, 2]\nn = None")[0]
        tipos = {s["nome"]: s["tipo"] for s in r["tabela_simbolos"]}
        self.assertEqual(tipos, {"idade": "int", "nome": "str", "altura": "float",
                                 "ok": "bool", "v": "list", "n": "None"})
        s = simbolo(r, "idade")
        self.assertEqual((s["categoria"], s["escopo"], s["linha"], s["coluna"]),
                         ("variavel", "global", 1, 1))
        self.assertTrue(s["inicializado"])

    def test_formato_do_simbolo(self):
        r = analisar("x = 1\nprint(x)")[0]
        campos = {"nome", "categoria", "tipo", "tipos", "escopo", "escopo_rotulo", "linha", "coluna",
                  "linha_fim", "coluna_fim", "no_id", "inicializado", "usado", "usos", "atribuicoes"}
        for s in r["tabela_simbolos"]:
            self.assertLessEqual(campos, set(s))

    def test_tipo_de_expressoes(self):
        r = analisar("a = 7 / 2\nb = 7 // 2\nc = 2 + 1.5\nd = 'ab' * 3\ne = [1] + [2]\n"
                     "f = 3 > 2\ng = not 1\nh = -4\ni = len('abc')\nj = input()\nk = str(3)")[0]
        tipos = {s["nome"]: s["tipo"] for s in r["tabela_simbolos"] if s["escopo"] == "global"}
        self.assertEqual(tipos, {"a": "float", "b": "int", "c": "float", "d": "str", "e": "list",
                                 "f": "bool", "g": "bool", "h": "int", "i": "int", "j": "str", "k": "str"})

    def test_usos_registrados(self):
        r = analisar("x = 1\ny = x + x\nprint(y)")[0]
        x = simbolo(r, "x")
        self.assertTrue(x["usado"])
        self.assertEqual([(u["linha"], u["coluna"]) for u in x["usos"]], [(2, 5), (2, 9)])
        self.assertFalse(simbolo(r, "y")["usos"] == [])

    def test_funcao_parametros_e_escopo_local(self):
        r = analisar("def soma(a, b):\n    total = a + b\n    return total\nx = soma(1, 2)")[0]
        f = simbolo(r, "soma")
        self.assertEqual((f["categoria"], f["parametros"], f["escopo"]), ("funcao", ["a", "b"], "global"))
        self.assertEqual((f["linha"], f["coluna"]), (1, 5))   # posição do nome, não do 'def'
        self.assertEqual(simbolo(r, "a")["categoria"], "parametro")
        self.assertEqual(simbolo(r, "total")["escopo"], "soma")
        escopos = [e["nome"] for e in r["escopos"]]
        self.assertEqual(escopos[:2], ["global", "soma"])
        self.assertEqual(r["escopos"][1]["pai"], "global")

    def test_tipo_de_retorno_inferido(self):
        r = analisar("def um():\n    return 1\ndef nada():\n    pass\nx = um()\ny = nada()")[0]
        self.assertEqual(simbolo(r, "um")["retorno"], "int")
        self.assertEqual(simbolo(r, "nada")["retorno"], "None")
        self.assertEqual(simbolo(r, "x")["tipo"], "int")

    def test_embutidas_usadas_aparecem_no_escopo_embutido(self):
        r = analisar("print(len('a'))")[0]
        nomes = {s["nome"]: s["escopo"] for s in r["tabela_simbolos"]}
        self.assertEqual(nomes, {"print": "embutido", "len": "embutido"})
        self.assertEqual(r["escopos"][-1]["nome"], "embutido")

    def test_sombreamento_de_global_por_local(self):
        r = analisar("x = 10\ndef f():\n    x = 20\n    return x")[0]
        local = simbolo(r, "x", "f")
        self.assertIn("escopo global", local["sombreia"])
        self.assertEqual(simbolo(r, "x", "global")["tipo"], "int")
        self.assertTrue(r["sucesso"])

    def test_blocos_nao_criam_escopo(self):
        r = analisar("if True:\n    y = 1\nelse:\n    y = 2\nprint(y)")[0]
        self.assertEqual(simbolo(r, "y")["escopo"], "global")
        self.assertEqual(r["erros"] + r["avisos"], [])

    def test_variavel_do_for(self):
        r = analisar("for i in range(3):\n    print(i)\nfor c in 'ab':\n    print(c)")[0]
        self.assertEqual(simbolo(r, "i")["tipo"], "int")
        self.assertEqual(simbolo(r, "c")["tipo"], "str")


class TestNomeNaoDefinido(unittest.TestCase):

    def test_valido(self):
        self.assertEqual(regras("total = 0\ntotal = total + 1"), [])

    def test_nunca_definido_com_sugestao(self):
        r = analisar("total = 10\nprint(totl)")[0]
        e = r["erros"][0]
        self.assertEqual((e["regra"], e["linha"], e["coluna"]), ("IDENTIFICADOR_NAO_DEFINIDO", 2, 7))
        self.assertIn("Você quis dizer 'total'?", e["sugestao"])
        self.assertEqual(e["erro_python"], "NameError")

    def test_usado_antes_da_atribuicao(self):
        e = analisar("print(y)\ny = 2")[0]["erros"][0]
        self.assertIn("só recebe valor na linha 2", e["mensagem"])

    def test_funcao_chamada_antes_do_def(self):
        e = analisar("f()\ndef f():\n    pass")[0]["erros"][0]
        self.assertIn("só é definida (def) na linha 2", e["mensagem"])

    def test_lado_direito_avaliado_antes(self):
        self.assertEqual(regras("x = x + 1"), ["IDENTIFICADOR_NAO_DEFINIDO"])

    def test_sem_erro_em_cascata(self):
        # O mesmo nome indefinido é apontado uma vez, e o tipo desconhecido não
        # gera erros de tipo adicionais.
        self.assertEqual(regras("a = b + 1\nc = b * 'x'\nd = -b"), ["IDENTIFICADOR_NAO_DEFINIDO"])

    def test_funcao_pode_usar_global_definida_depois(self):
        # O corpo só é executado na chamada, quando a global já existe.
        self.assertEqual(regras("def f():\n    return limite\nlimite = 3\nprint(f())"), [])

    def test_funcao_chama_funcao_definida_depois(self):
        r = analisar("def a():\n    return b()\ndef b():\n    return 1\nprint(a())")[0]
        self.assertEqual(r["erros"], [])
        self.assertTrue(simbolo(r, "b")["usado"])

    def test_dentro_de_funcao_nome_inexistente(self):
        e = analisar("def f():\n    return z")[0]["erros"][0]
        self.assertIn("nem na função 'f' nem fora dela", e["mensagem"])

    def test_fechamento_le_variavel_da_funcao_externa(self):
        self.assertEqual(regras("def ext():\n    n = 1\n    def inn():\n        return n\n    return inn()"), [])


class TestAtribuicaoComposta(unittest.TestCase):

    def test_valido(self):
        self.assertEqual(regras("c = 0\nc += 1\nc *= 2"), [])

    def test_sem_valor_anterior(self):
        r = analisar("cont += 1")[0]
        self.assertEqual(r["erros"][0]["regra"], "ATRIBUICAO_COMPOSTA_SEM_VALOR")
        self.assertIn("cont = 0", r["erros"][0]["sugestao"])

    def test_tipo_verificado(self):
        self.assertEqual(regras("t = 'a'\nt += 1"), ["TIPOS_INCOMPATIVEIS"])


class TestVariavelLocal(unittest.TestCase):

    def test_valido(self):
        self.assertEqual(regras("x = 1\ndef f():\n    return x"), [])

    def test_local_lida_antes_de_receber_valor(self):
        e = analisar("x = 1\ndef f():\n    print(x)\n    x = 2")[0]["erros"][0]
        self.assertEqual((e["regra"], e["erro_python"]), ("VARIAVEL_LOCAL_SEM_VALOR", "UnboundLocalError"))
        self.assertIn("de fora da função não é usado", e["mensagem"])

    def test_composta_em_global_dentro_de_funcao(self):
        self.assertEqual(regras("total = 0\ndef f():\n    total += 1"), ["VARIAVEL_LOCAL_SEM_VALOR"])


class TestTipos(unittest.TestCase):

    def test_validos(self):
        self.assertEqual(regras("a = 1 + 2.5\nb = 'a' + 'b'\nc = [1] * 2\nd = 3 * 'x'\ne = 'v: %d' % 3\n"
                                "f = True + 1\ng = 'a' < 'b'\nh = 1 < 2.5\ni = 'a' in 'abc'\nj = 1 in [1]"), [])

    def test_texto_mais_numero(self):
        e = analisar("idade = 21\nmsg = 'idade: ' + idade")[0]["erros"][0]
        self.assertEqual((e["regra"], e["linha"], e["coluna"]), ("TIPOS_INCOMPATIVEIS", 2, 7))
        self.assertIn("entre str e int", e["mensagem"])
        self.assertIn("str(...)", e["sugestao"])

    def test_outras_combinacoes_invalidas(self):
        for codigo in ("x = 'a' - 'b'", "x = [1] / 2", "x = 'a' * 'b'", "x = None + 1",
                       "x = [1] + 'a'", "x = 'a' * 2.5", "x = 2 ** 'a'"):
            with self.subTest(codigo=codigo):
                self.assertEqual(regras(codigo), ["TIPOS_INCOMPATIVEIS"])

    def test_tipo_desconhecido_nao_gera_erro(self):
        self.assertEqual(regras("def f(a):\n    return a + 1\nx = input() + 'a'"), [])

    def test_operando_invalido(self):
        self.assertEqual(regras("x = -'a'"), ["OPERANDO_INVALIDO"])
        self.assertEqual(regras("x = -[1]"), ["OPERANDO_INVALIDO"])
        self.assertEqual(regras("x = -True"), [])

    def test_comparacao_invalida(self):
        self.assertEqual(regras("x = 'a' < 3"), ["COMPARACAO_INVALIDA"])
        self.assertEqual(regras("x = 'a' == 3"), [])

    def test_in_com_tipos_invalidos(self):
        self.assertEqual(regras("x = 1 in 5"), ["NAO_ITERAVEL"])
        self.assertEqual(regras("x = 1 in 'abc'"), ["TIPOS_INCOMPATIVEIS"])


class TestColecoes(unittest.TestCase):

    def test_validos(self):
        self.assertEqual(regras("v = [1, 2]\nv[0] = 5\nx = v[1]\nt = 'abc'\nc = t[0]\n"
                                "for n in v:\n    pass\nfor i in range(2):\n    pass"), [])

    def test_for_em_numero(self):
        e = analisar("for i in 10:\n    pass")[0]["erros"][0]
        self.assertEqual(e["regra"], "NAO_ITERAVEL")
        self.assertIn("range(", e["sugestao"])

    def test_indexar_numero(self):
        self.assertEqual(regras("n = 5\nx = n[0]"), ["NAO_INDEXAVEL"])

    def test_indice_nao_inteiro(self):
        self.assertEqual(regras("v = [1]\nx = v['a']"), ["INDICE_INVALIDO"])
        self.assertEqual(regras("v = [1]\nx = v[1.5]"), ["INDICE_INVALIDO"])

    def test_alterar_letra_de_texto(self):
        self.assertEqual(regras("t = 'abc'\nt[0] = 'x'"), ["ITEM_IMUTAVEL"])


class TestChamadas(unittest.TestCase):

    def test_validos(self):
        self.assertEqual(regras("def f(a, b):\n    return a\nf(1, 2)\nprint()\nprint(1, 2, 3)\n"
                                "range(1, 10, 2)\nmax(1, 2)\nlen([1])"), [])

    def test_numero_errado_de_argumentos(self):
        e = analisar("def f(a, b):\n    return a\nf(1)")[0]["erros"][0]
        self.assertEqual((e["regra"], e["linha"]), ("ARGUMENTOS_INCORRETOS", 3))
        self.assertIn("espera 2 argumento(s) (a, b), mas recebeu 1", e["mensagem"])
        self.assertEqual(regras("def f():\n    pass\nf(1)"), ["ARGUMENTOS_INCORRETOS"])

    def test_embutidas(self):
        self.assertEqual(regras("len()"), ["ARGUMENTOS_INCORRETOS"])
        self.assertEqual(regras("input(1, 2)"), ["ARGUMENTOS_INCORRETOS"])
        self.assertEqual(regras("x = len(5)"), ["ARGUMENTO_INVALIDO"])
        self.assertEqual(regras("x = range('a')"), ["ARGUMENTO_INVALIDO"])

    def test_chamar_valor_que_nao_e_funcao(self):
        self.assertEqual(regras("x = 3\nx()"), ["NAO_CHAMAVEL"])

    def test_parametro_duplicado(self):
        e = analisar("def g(a, a):\n    pass")[0]["erros"][0]
        self.assertEqual((e["regra"], e["coluna"]), ("PARAMETRO_DUPLICADO", 10))

    def test_metodo_nao_e_verificado(self):
        self.assertEqual(regras("v = []\nv.append(1)"), [])


class TestContexto(unittest.TestCase):

    def test_validos(self):
        self.assertEqual(regras("def f():\n    return 1\nwhile True:\n    break\nfor i in [1]:\n    continue"), [])

    def test_return_fora_de_funcao(self):
        self.assertEqual(regras("return 1"), ["RETORNO_FORA_DE_FUNCAO"])

    def test_break_e_continue_fora_de_laco(self):
        self.assertEqual(regras("break\ncontinue"), ["FORA_DE_LACO", "FORA_DE_LACO"])

    def test_funcao_dentro_de_laco_comeca_sem_laco(self):
        self.assertEqual(regras("while True:\n    def h():\n        break\n    break"), ["FORA_DE_LACO"])


class TestAvisos(unittest.TestCase):

    def test_possivelmente_nao_definida_no_if(self):
        r = analisar("c = 1\nif c > 0:\n    y = 1\nprint(y)")[0]
        self.assertTrue(r["sucesso"])
        self.assertEqual([a["regra"] for a in r["avisos"]], ["POSSIVELMENTE_NAO_DEFINIDA"])

    def test_if_com_else_define_com_certeza(self):
        self.assertEqual(regras("c = 1\nif c:\n    y = 1\nelif c > 2:\n    y = 3\nelse:\n    y = 2\nprint(y)",
                                avisos=True), [])

    def test_variavel_definida_mais_adiante_no_laco(self):
        codigo = "i = 0\nwhile i < 3:\n    if i > 0:\n        print(ult)\n    ult = i\n    i += 1"
        self.assertEqual(regras(codigo), [])
        self.assertEqual(regras(codigo, avisos=True), ["POSSIVELMENTE_NAO_DEFINIDA"])

    def test_mudanca_de_tipo(self):
        r = analisar("x = 1\nx = 'a'")[0]
        self.assertEqual([a["regra"] for a in r["avisos"]], ["MUDANCA_DE_TIPO"])
        self.assertEqual(simbolo(r, "x")["tipos"], ["int", "str"])
        self.assertEqual(regras("x = 1\nx = 2.5", avisos=True), [])   # int -> float: numérico

    def test_sombreia_embutida(self):
        self.assertEqual(regras("list = [1]", avisos=True), ["SOMBREIA_EMBUTIDA"])
        self.assertEqual(regras("def len(a):\n    return a", avisos=True), ["SOMBREIA_EMBUTIDA"])


class TestFormatoEConsistencia(unittest.TestCase):

    def test_formato_do_erro(self):
        e = analisar("print(z)")[0]["erros"][0]
        self.assertEqual(set(e), {"tipo", "regra", "titulo", "linha", "coluna", "linha_fim", "coluna_fim",
                                  "mensagem", "explicacao", "sugestao", "erro_python", "no_id"})
        self.assertEqual(e["tipo"], "ERRO_SEMANTICO")
        self.assertTrue(e["mensagem"].startswith("Erro semântico na linha 1, coluna 7:"))
        self.assertEqual(e["explicacao"], REGRAS["IDENTIFICADOR_NAO_DEFINIDO"]["explicacao"])

    def test_todas_as_regras_tem_texto(self):
        for codigo, info in REGRAS.items():
            with self.subTest(regra=codigo):
                self.assertIn(info["gravidade"], ("erro", "aviso"))
                self.assertGreater(len(info["explicacao"]), 40)
                self.assertTrue(info["titulo"] and info["erro_python"])

    def test_erros_e_simbolos_apontam_para_nos_da_ast(self):
        codigo = "x = 1\ndef f(a):\n    return a + y\nprint(f(x))\nz = 'a' + 1"
        r, sintatico, _ = analisar(codigo)
        ids = {}
        pilha = [sintatico["ast"]]
        while pilha:
            no = pilha.pop()
            ids[no["id"]] = no
            pilha.extend(no["filhos"])
        for e in r["erros"]:
            no = ids[e["no_id"]]
            self.assertEqual((e["linha"], e["coluna"]), (no["linha"], no["coluna"]))
        for s in r["tabela_simbolos"]:
            if s["no_id"] is not None:
                self.assertIn(s["no_id"], ids)
            for uso in s["usos"]:
                self.assertEqual(ids[uso["no_id"]]["atributos"].get("nome"), s["nome"])

    def test_posicoes_coincidem_com_os_tokens(self):
        codigo = "conta = 10\nresultado = conta * 2"
        r, _, lexico = analisar(codigo)
        posicoes = {(t["linha"], t["coluna"]): t["lexema"] for t in lexico["tokens"]}
        for s in r["tabela_simbolos"]:
            self.assertEqual(posicoes[(s["linha"], s["coluna"])], s["nome"])
            for uso in s["usos"]:
                self.assertEqual(posicoes[(uso["linha"], uso["coluna"])], s["nome"])

    def test_erros_ordenados_por_posicao(self):
        r = analisar("a = b\nc = d\ne = 'x' - 1")[0]
        posicoes = [(e["linha"], e["coluna"]) for e in r["erros"]]
        self.assertEqual(posicoes, sorted(posicoes))

    def test_bordas(self):
        for codigo in ("# só comentário", "pass", "x = 1", "def f():\n    pass"):
            with self.subTest(codigo=codigo):
                r = analisar(codigo)[0]
                self.assertTrue(r["sucesso"])
        self.assertEqual(analisar("# nada")[0]["tabela_simbolos"], [])

    def test_resumo(self):
        r = analisar("def f(a):\n    return a\nx = f(1)\nprint(x)\nprint(q)")[0]
        self.assertEqual(r["resumo"]["por_categoria"],
                         {"variavel": 1, "funcao": 1, "parametro": 1, "embutida": 1})
        self.assertEqual(r["resumo"]["total_erros"], 1)

    def test_programa_grande(self):
        codigo = "".join(f"v{i} = {i}\nprint(v{i} + 1)\n" for i in range(800))
        r = analisar(codigo)[0]
        self.assertTrue(r["sucesso"])
        self.assertEqual(r["resumo"]["total_simbolos"], 801)


class TestOraculoPython(unittest.TestCase):
    """O próprio Python confere as regras: cada programa é executado de verdade
    e o erro que ele lança deve ser o que o analisador previu."""

    CASOS = {
        "x = 10\nprint(totl)": "NameError",
        "print(y)\ny = 2": "NameError",
        "cont += 1": "NameError",
        "x = 1\ndef f():\n    print(x)\n    x = 2\nf()": "UnboundLocalError",
        "idade = 21\nm = 'idade: ' + idade": "TypeError",
        "x = -'a'": "TypeError",
        "x = 'a' < 3": "TypeError",
        "for i in 10:\n    pass": "TypeError",
        "n = 5\nx = n[0]": "TypeError",
        "v = [1]\nx = v['a']": "TypeError",
        "t = 'abc'\nt[0] = 'x'": "TypeError",
        "x = 3\nx()": "TypeError",
        "def f(a, b):\n    return a\nf(1)": "TypeError",
        "x = len(5)": "TypeError",
        "x = 1 in 5": "TypeError",
        "f()\ndef f():\n    pass": "NameError",
    }

    VALIDOS = [
        "def soma(a, b):\n    return a + b\nx = soma(1, 2)\nnomes = ['a']\nfor n in nomes:\n    print(n)",
        "def f():\n    return limite\nlimite = 3\nprint(f())",
        "c = 1\nif c:\n    y = 1\nelse:\n    y = 2\nprint(y)",
        "a = 'v: %d' % 3\nb = [1] * 2 + [3]\nc = 3 * 'x'\nd = True + 1",
    ]

    def executar(self, codigo):
        with contextlib.redirect_stdout(io.StringIO()):
            exec(compile(codigo, "<teste>", "exec"), {"__builtins__": builtins})

    def test_erro_previsto_e_o_erro_real(self):
        for codigo, esperado in self.CASOS.items():
            with self.subTest(codigo=codigo):
                erros = analisar(codigo)[0]["erros"]
                self.assertTrue(erros, "o analisador não encontrou o erro")
                self.assertEqual(erros[0]["erro_python"], esperado)
                with self.assertRaises(Exception) as captura:
                    self.executar(codigo)
                self.assertEqual(type(captura.exception).__name__, esperado)

    def test_validos_executam_sem_erro(self):
        for codigo in self.VALIDOS:
            with self.subTest(codigo=codigo):
                self.assertEqual(analisar(codigo)[0]["erros"], [])
                self.executar(codigo)

    def test_retorno_e_break_fora_de_contexto_sao_rejeitados_pelo_python(self):
        for codigo in ("return 1", "break", "def g(a, a):\n    pass"):
            with self.subTest(codigo=codigo):
                self.assertTrue(analisar(codigo)[0]["erros"])
                with self.assertRaises(SyntaxError):
                    compile(codigo, "<teste>", "exec")


class TestEmbutidas(unittest.TestCase):

    def test_tabela_coerente(self):
        for nome, info in EMBUTIDAS.items():
            with self.subTest(nome=nome):
                self.assertTrue(callable(getattr(builtins, nome)))
                if info["max"] is not None:
                    self.assertLessEqual(info["min"], info["max"])


if __name__ == "__main__":
    unittest.main()
