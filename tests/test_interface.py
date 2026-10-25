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
