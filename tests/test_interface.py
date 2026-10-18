
from playwright.sync_api import sync_playwright


def testar_interface():
    with sync_playwright() as playwright:
        navegador = playwright.chromium.launch(headless=True)
        pagina = navegador.new_page()

        pagina.goto("http://frontend", wait_until="domcontentloaded")

        # Verifica o título da aplicação
        assert pagina.locator("h1").inner_text() == "Software Educacional"

        # Seleciona um exemplo
        pagina.locator("#exemplos").select_option("soma")
        assert pagina.locator("#codigo").input_value() == "resultado = 10 + 5"

        # Edita o código
        pagina.locator("#codigo").fill("idade = 21")
        assert pagina.locator("#codigo").input_value() == "idade = 21"

        # Envia o código ao backend
        pagina.locator("#analisar").click()
        pagina.get_by_text("Código recebido com sucesso.").wait_for()

        # Verifica a entrada vazia
        pagina.locator("#codigo").fill("")
        pagina.locator("#analisar").click()
        pagina.get_by_text(
            "Informe um código-fonte antes de solicitar a análise."
        ).wait_for()

        navegador.close()


if __name__ == "__main__":
    testar_interface()
    print("Testes de interação aprovados!")
