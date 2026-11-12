import os

from playwright.sync_api import expect, sync_playwright

URL = os.environ.get("URL_APLICACAO", "http://localhost:3000")
# Opcional: caminho de um Chromium já instalado no sistema.
CAMINHO_CHROMIUM = os.environ.get("CAMINHO_CHROMIUM") or None


def abrir(navegador, **opcoes):
    pagina = navegador.new_page(**opcoes)
    erros_js = []
    pagina.on("pageerror", lambda erro: erros_js.append(str(erro)))
    pagina.goto(URL, wait_until="domcontentloaded")
    return pagina, erros_js


def analisar(pagina, codigo):
    pagina.locator("#codigo").fill(codigo)
    pagina.locator("#analisar").click()


def testar_regressao_etapa2(navegador):
    """Fluxo da Etapa 2: exemplos, edição, envio e validação."""
    pagina, erros_js = abrir(navegador)

    assert pagina.locator("h1").inner_text() == "Software Educacional"

    pagina.locator("#exemplos").select_option("soma")
    assert pagina.locator("#codigo").input_value() == "resultado = 10 + 5"

    pagina.locator("#codigo").fill("idade = 21")
    assert pagina.locator("#codigo").input_value() == "idade = 21"

    pagina.locator("#analisar").click()
    expect(pagina.locator("#resultado")).to_contain_text("Análise léxica concluída")

    pagina.locator("#codigo").fill("")
    pagina.locator("#analisar").click()
    pagina.get_by_text(
        "Informe um código-fonte antes de solicitar a análise."
    ).wait_for()
    expect(pagina.locator("#painel")).to_be_hidden()

    assert erros_js == [], erros_js
    pagina.close()


def testar_tabela_de_tokens(navegador):
    pagina, erros_js = abrir(navegador)

    pagina.locator("#exemplos").select_option("variavel")
    pagina.locator("#analisar").click()
    expect(pagina.locator("#resultado")).to_have_text(
        "Análise léxica concluída: 5 token(s) reconhecido(s)."
    )

    pagina.get_by_role("tab", name="Tabela de tokens").click()
    linhas = pagina.locator("#tabela-tokens tbody tr")
    expect(linhas).to_have_count(5)
    primeira = linhas.nth(0).locator("td")
    assert primeira.nth(1).inner_text() == "IDENTIFICADOR"
    assert primeira.nth(2).inner_text() == "idade"
    assert primeira.nth(3).inner_text() == "1"
    assert primeira.nth(4).inner_text() == "1"

    # Esconder tokens estruturais deixa só os 3 tokens "visíveis".
    pagina.locator("#mostrar-estruturais").uncheck()
    expect(linhas).to_have_count(3)

    pagina.locator("#filtro-tipo").select_option("OPERADOR")
    expect(linhas).to_have_count(1)

    expect(pagina.locator("#erros")).to_contain_text("Nenhum erro léxico encontrado.")
    assert erros_js == [], erros_js
    pagina.close()


def testar_codigo_colorido_e_detalhes(navegador):
    pagina, erros_js = abrir(navegador)

    pagina.locator("#exemplos").select_option("funcao")
    pagina.locator("#analisar").click()

    destaque = pagina.locator("#codigo-destacado")
    expect(destaque.locator(".tk-PALAVRA_RESERVADA").first).to_have_text("def")
    expect(destaque.locator(".tk-COMENTARIO").first).to_contain_text("# Calcula")

    destaque.locator(".tk-IDENTIFICADOR", has_text="media").first.click()
    expect(pagina.locator("#detalhe-token")).to_contain_text("IDENTIFICADOR")
    expect(pagina.locator("#detalhe-token")).to_contain_text("linha 2, coluna 5")

    pagina.get_by_role("tab", name="Sequência").click()
    expect(pagina.locator("#comparacao")).to_contain_text("<PALAVRA_RESERVADA, def>")
    expect(pagina.locator("#comparacao")).to_contain_text("(comentário: ignorado)")

    pagina.get_by_role("tab", name="Resumo").click()
    expect(pagina.locator("#resumo")).to_contain_text("Identificadores distintos")

    assert erros_js == [], erros_js
    pagina.close()


def testar_passo_a_passo(navegador):
    pagina, erros_js = abrir(navegador)

    analisar(pagina, "x = 1")
    pagina.get_by_role("tab", name="Passo a passo").click()

    expect(pagina.locator("#passo-contador")).to_have_text("Passo 0 de 5")
    pagina.locator("#passo-proximo").click()
    expect(pagina.locator("#passo-contador")).to_have_text("Passo 1 de 5")
    expect(pagina.locator("#passo-codigo .atual")).to_have_text("x")
    expect(pagina.locator("#passo-explicacao")).to_contain_text("IDENTIFICADOR")

    pagina.locator("#passo-proximo").click()
    expect(pagina.locator("#passo-codigo .atual")).to_have_text("=")
    expect(pagina.locator("#passo-tabela tbody tr")).to_have_count(2)

    pagina.locator("#passo-anterior").click()
    expect(pagina.locator("#passo-contador")).to_have_text("Passo 1 de 5")

    pagina.locator("#passo-velocidade").fill("5")
    pagina.locator("#passo-play").click()
    expect(pagina.locator("#passo-contador")).to_have_text("Passo 5 de 5", timeout=5000)
    expect(pagina.locator("#passo-explicacao")).to_contain_text("FIM")

    pagina.locator("#passo-inicio").click()
    expect(pagina.locator("#passo-contador")).to_have_text("Passo 0 de 5")

    assert erros_js == [], erros_js
    pagina.close()


def testar_erros_lexicos(navegador):
    pagina, erros_js = abrir(navegador)

    pagina.locator("#exemplos").select_option("erros")
    pagina.locator("#analisar").click()

    expect(pagina.locator("#resultado")).to_contain_text("5 erro(s) léxico(s)")
    erros = pagina.locator("#erros .erro")
    expect(erros).to_have_count(5)
    expect(erros.nth(0)).to_contain_text(
        "Erro léxico na linha 1, coluna 12: caractere não reconhecido '@'."
    )
    expect(pagina.locator("#codigo-destacado .tk-ERRO")).to_have_count(5)

    erros.nth(1).click()
    expect(pagina.locator("#detalhe-token")).to_contain_text("1nome")

    # Tokens válidos continuam sendo exibidos.
    pagina.get_by_role("tab", name="Tabela de tokens").click()
    expect(pagina.locator("#tabela-tokens tbody")).to_contain_text("valor")

    pagina.get_by_role("tab", name="Sequência").click()
    expect(pagina.locator("#comparacao")).to_contain_text("<ERRO_LEXICO, @>")

    assert erros_js == [], erros_js
    pagina.close()


def testar_entradas_hostis_nao_quebram(navegador):
    pagina, erros_js = abrir(navegador)

    analisar(pagina, "<img src=x onerror=\"document.body.dataset.xss=1\"> @ ¬ 😀")
    expect(pagina.locator("#resultado")).to_contain_text("erro(s) léxico(s)")
    assert pagina.evaluate("document.body.dataset.xss") is None
    expect(pagina.locator("#codigo-destacado")).to_contain_text("<img src=x")

    analisar(pagina, "    \n\t\n")
    expect(pagina.locator("#resultado")).to_have_text(
        "Informe um código-fonte antes de solicitar a análise."
    )

    analisar(pagina, "# apenas um comentário")
    expect(pagina.locator("#resultado")).to_contain_text("1 token(s)")

    assert erros_js == [], erros_js
    pagina.close()


def testar_escopo_e_conceitos(navegador):
    pagina, erros_js = abrir(navegador)

    pagina.locator("#conceitos summary").click()
    expect(pagina.locator("#conceitos")).to_contain_text("Lexema")

    pagina.locator("#escopo summary").click()
    expect(pagina.locator("#escopo-conteudo")).to_contain_text("while")
    expect(pagina.locator("#escopo-conteudo")).to_contain_text("relacional")

    assert erros_js == [], erros_js
    pagina.close()


def testar_celular(navegador):
    pagina, erros_js = abrir(
        navegador,
        viewport={"width": 375, "height": 740},
        is_mobile=True,
        has_touch=True,
    )

    pagina.locator("#exemplos").select_option("condicional")
    pagina.locator("#analisar").tap()
    expect(pagina.locator("#resultado")).to_contain_text("Análise léxica concluída")

    largura = pagina.evaluate("document.documentElement.scrollWidth")
    assert largura <= 375, f"A página tem rolagem horizontal ({largura}px)"

    pagina.get_by_role("tab", name="Passo a passo").tap()
    pagina.locator("#passo-proximo").tap()
    expect(pagina.locator("#passo-contador")).to_contain_text("Passo 1 de")

    # Etapa 4: no celular a AST abre em modo lista, sem rolagem horizontal.
    expect(pagina.locator("#arvore-ast.lista .no-ast").first).to_be_visible()
    largura = pagina.evaluate("document.documentElement.scrollWidth")
    assert largura <= 375, f"A página tem rolagem horizontal ({largura}px)"

    assert erros_js == [], erros_js
    pagina.close()


def testar_ast_para_codigo_valido(navegador):
    pagina, erros_js = abrir(navegador)

    analisar(pagina, "resultado = 10 + 5 * 2")
    expect(pagina.locator("#resultado")).to_have_text(
        "Análise léxica concluída: 9 token(s) reconhecido(s)."
    )
    expect(pagina.locator("#resultado-sintatico")).to_contain_text("AST com 8 nó(s)")
    expect(pagina.locator("#arvore-ast .no-ast")).to_have_count(8)

    # A multiplicação fica abaixo da adição (precedência).
    adicao = pagina.locator("#arvore-ast li", has=pagina.locator(".no-ast", has_text="Adição (+)")).first
    expect(adicao.locator(".no-ast", has_text="Multiplicação (*)")).to_have_count(1)

    # Selecionar um nó destaca o trecho do código e mostra a regra.
    pagina.locator("#arvore-ast .no-ast", has_text="Multiplicação (*)").click()
    expect(pagina.locator("#codigo-sintatico mark")).to_have_text("5 * 2")
    expect(pagina.locator("#detalhe-no")).to_contain_text("linha 1, coluna 18 até linha 1, coluna 22")
    expect(pagina.locator("#detalhe-no")).to_contain_text("termo")
    expect(pagina.locator("#erros-sintaticos")).to_contain_text("Nenhum erro sintático encontrado.")

    assert erros_js == [], erros_js
    pagina.close()


def testar_lista_expandir_recolher_e_filtro(navegador):
    pagina, erros_js = abrir(navegador)

    pagina.locator("#exemplos").select_option("programa")
    pagina.locator("#analisar").click()
    expect(pagina.locator("#resultado-sintatico")).to_contain_text("AST com 45 nó(s)")

    pagina.locator("#modo-lista").click()
    abertos = pagina.locator("#arvore-ast details[open]")
    total = pagina.locator("#arvore-ast details").count()
    assert total > 5
    pagina.locator("#recolher-ast").click()
    expect(abertos).to_have_count(0)
    pagina.locator("#expandir-ast").click()
    expect(abertos).to_have_count(total)

    pagina.locator("#filtro-no").select_option("CHAMADA")
    expect(pagina.locator("#arvore-ast .no-ast.filtrado")).to_have_count(4)
    expect(pagina.locator("#contagem-filtro")).to_contain_text("4 nó(s) do tipo CHAMADA")

    pagina.locator("#modo-diagrama").click()
    expect(pagina.locator("#arvore-ast.diagrama .no-ast")).to_have_count(45)

    assert erros_js == [], erros_js
    pagina.close()


def testar_construcao_passo_a_passo_e_derivacao(navegador):
    pagina, erros_js = abrir(navegador)

    analisar(pagina, "x = 1 + 2")
    pagina.get_by_role("tab", name="Construção da árvore").click()
    expect(pagina.locator("#construcao-contador")).to_contain_text("0 de 6 nó(s)")

    pagina.locator("#construcao-proximo").click()
    expect(pagina.locator("#construcao-explicacao")).to_contain_text("consumiu o token")
    expect(pagina.locator("#construcao-pilha")).to_contain_text("programa")

    pagina.locator("#construcao-so-nos").check()
    pagina.locator("#construcao-proximo").click()
    expect(pagina.locator("#construcao-explicacao")).to_contain_text("criou o nó IDENTIFICADOR")
    expect(pagina.locator("#construcao-arvore .no-ast")).to_have_count(1)

    pagina.locator("#construcao-fim").click()
    expect(pagina.locator("#construcao-contador")).to_contain_text("6 de 6 nó(s)")
    expect(pagina.locator("#construcao-arvore .no-ast")).to_have_count(6)

    pagina.get_by_role("tab", name="Árvore de derivação").click()
    expect(pagina.locator("#arvore-derivacao")).to_contain_text("‹programa›")
    expect(pagina.locator("#arvore-derivacao")).to_contain_text("‹soma›")
    expect(pagina.locator("#comparacao-arvores")).to_contain_text("a AST tem apenas 6")

    pagina.get_by_role("tab", name="Gramática").click()
    expect(pagina.locator("#lista-gramatica")).to_contain_text("soma = termo")

    pagina.get_by_role("tab", name="JSON").click()
    expect(pagina.locator("#json-ast")).to_contain_text('"tipo": "PROGRAMA"')
    with pagina.expect_download() as download:
        pagina.locator("#baixar-json").click()
    assert download.value.suggested_filename == "ast.json"

    assert erros_js == [], erros_js
    pagina.close()


def testar_erros_sintaticos(navegador):
    pagina, erros_js = abrir(navegador)

    pagina.locator("#exemplos").select_option("sintaticos")
    pagina.locator("#analisar").click()
    expect(pagina.locator("#resultado-sintatico")).to_contain_text("4 erro(s) sintático(s)")
    erros = pagina.locator("#erros-sintaticos .erro-sintatico")
    expect(erros).to_have_count(4)
    expect(erros.nth(0)).to_contain_text("ERRO SINTÁTICO")
    expect(erros.nth(1)).to_contain_text(
        "Erro sintático na linha 2, coluna 13: a linha terminou, mas era esperado ':'"
    )
    expect(erros.nth(1)).to_contain_text('se = "if" expressao ":" bloco')

    # Sem AST: a aba da árvore some e o erro é destacado no código.
    expect(pagina.get_by_role("tab", name="Árvore (AST)")).to_be_hidden()
    erros.nth(2).click()
    expect(pagina.locator("#codigo-sintatico mark")).to_have_text("if")

    # A distinção entre erro léxico e sintático é visível.
    expect(pagina.locator("#erros")).to_contain_text("Nenhum erro léxico encontrado.")

    assert erros_js == [], erros_js
    pagina.close()


def testar_erro_lexico_nao_executa_parser(navegador):
    pagina, erros_js = abrir(navegador)

    pagina.locator("#exemplos").select_option("erros")
    pagina.locator("#analisar").click()
    expect(pagina.locator("#erros .etiqueta-erro.lexico")).to_have_count(5)
    expect(pagina.locator("#resultado-sintatico")).to_contain_text("Análise sintática não executada")
    expect(pagina.locator("#sintatico-conteudo")).to_be_hidden()

    # Corrigido o código, a análise sintática volta a ser feita.
    analisar(pagina, "valor = 10 * 2")
    expect(pagina.locator("#resultado-sintatico")).to_contain_text("o programa segue a gramática")

    assert erros_js == [], erros_js
    pagina.close()


def testar_consistencia_tokens_e_arvore(navegador):
    pagina, erros_js = abrir(navegador)

    analisar(pagina, "total = preco * 2")
    pagina.get_by_role("tab", name="Tabela de tokens").click()
    linha_preco = pagina.locator("#tabela-tokens tbody tr", has_text="preco")
    linha_tabela = linha_preco.locator("td").nth(3).inner_text()
    coluna_tabela = linha_preco.locator("td").nth(4).inner_text()

    pagina.locator("#arvore-ast .no-ast", has_text="Identificador: preco").click()
    expect(pagina.locator("#detalhe-no")).to_contain_text(
        f"linha {linha_tabela}, coluna {coluna_tabela}")
    expect(pagina.locator("#detalhe-no .sequencia-tokens")).to_have_text("<IDENTIFICADOR, preco>")

    assert erros_js == [], erros_js
    pagina.close()


def testar_entrada_grande_nao_trava(navegador):
    pagina, erros_js = abrir(navegador)

    analisar(pagina, "x = 1\n" * 1100)
    expect(pagina.locator("#resultado-sintatico")).to_contain_text("o programa segue a gramática",
                                                                    timeout=15000)
    expect(pagina.locator("#aviso-detalhes")).to_be_visible()
    expect(pagina.get_by_role("tab", name="Construção da árvore")).to_be_hidden()

    analisar(pagina, "x" * 20001)
    expect(pagina.locator("#resultado")).to_contain_text("muito grande")

    assert erros_js == [], erros_js
    pagina.close()


def testar_ia_contextual(navegador):
    """Funciona com ou sem o Ollama: sem ele, a mensagem explica o motivo."""
    pagina, erros_js = abrir(navegador)

    analisar(pagina, "resultado = 10 + 5 * 2")
    pagina.locator("#arvore-ast .no-ast", has_text="Multiplicação (*)").click()
    pagina.locator("#detalhe-no .botao-ia").click()
    dialogo = pagina.locator("#dialogo-ia")
    expect(dialogo).to_be_visible()
    expect(pagina.locator("#titulo-dialogo-ia")).to_have_text("Explicação do nó da AST")
    expect(pagina.locator("#conteudo-dialogo-ia .aviso-ia, #conteudo-dialogo-ia .falha-ia")
           ).to_have_count(1, timeout=170000)
    pagina.locator("#fechar-dialogo-ia").click()
    expect(dialogo).to_be_hidden()

    # A análise continua funcionando independentemente da IA.
    analisar(pagina, "x = 1")
    expect(pagina.locator("#resultado-sintatico")).to_contain_text("o programa segue a gramática")

    assert erros_js == [], erros_js
    pagina.close()


TESTES = [
    testar_regressao_etapa2,
    testar_tabela_de_tokens,
    testar_codigo_colorido_e_detalhes,
    testar_passo_a_passo,
    testar_erros_lexicos,
    testar_entradas_hostis_nao_quebram,
    testar_escopo_e_conceitos,
    testar_celular,
    testar_ast_para_codigo_valido,
    testar_lista_expandir_recolher_e_filtro,
    testar_construcao_passo_a_passo_e_derivacao,
    testar_erros_sintaticos,
    testar_erro_lexico_nao_executa_parser,
    testar_consistencia_tokens_e_arvore,
    testar_entrada_grande_nao_trava,
    testar_ia_contextual,
]


def testar_interface():
    falhas = 0
    with sync_playwright() as playwright:
        navegador = playwright.chromium.launch(
            headless=True, executable_path=CAMINHO_CHROMIUM
        )
        for teste in TESTES:
            try:
                teste(navegador)
                print(f"ok    {teste.__name__}")
            except Exception as erro:  # noqa: BLE001
                falhas += 1
                print(f"FALHA {teste.__name__}: {erro}")
        navegador.close()
    return falhas


if __name__ == "__main__":
    total_falhas = testar_interface()
    if total_falhas:
        print(f"{total_falhas} teste(s) de interação falharam.")
        raise SystemExit(1)
    print("Testes de interação aprovados!")
