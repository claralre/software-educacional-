(function () {
    "use strict";

    const TEMPO_LIMITE_MS = 150000;

    function escaparHtml(texto) {
        return String(texto)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#39;");
    }

    // Formatação mínima e segura da resposta do modelo: primeiro escapa
    // todo o HTML, depois converte **negrito** e `código`.
    function formatarResposta(texto) {
        return escaparHtml(texto)
            .replace(/\*\*([^*\n]+)\*\*/g, "<strong>$1</strong>")
            .replace(/`([^`\n]+)`/g, "<code>$1</code>");
    }

    function montarPedido(alvo, codigo, pergunta) {
        const pedido = { codigo: codigo || "", alvo: alvo };
        if (pergunta) {
            pedido.pergunta = pergunta;
        }
        return pedido;
    }

    function alvoDoBotao(botao) {
        const tipo = botao.dataset.iaTipo;
        if (tipo === "no") {
            return { tipo: "no", id: Number(botao.dataset.iaId) };
        }
        return { tipo: tipo, indice: Number(botao.dataset.iaIndice) };
    }

    const api = {
        escaparHtml: escaparHtml,
        formatarResposta: formatarResposta,
        montarPedido: montarPedido
    };

    if (typeof module !== "undefined" && module.exports) {
        module.exports = api;
    }

    if (typeof document === "undefined") {
        return;
    }

    const TITULOS = {
        token: "Explicação do token",
        no: "Explicação do nó da AST",
        erro_sintatico: "Entendendo o erro sintático",
        erro_lexico: "Entendendo o erro léxico",
        conceito: "Professor virtual"
    };

    const statusIA = document.getElementById("status-ia");
    const dialogo = document.getElementById("dialogo-ia");
    let ultimoCodigo = "";
    let disponivel = false;

    async function verificarStatus() {
        try {
            const resposta = await fetch("/api/ia/status");
            const dados = await resposta.json();
            disponivel = Boolean(dados.disponivel);
            statusIA.textContent = dados.mensagem;
        } catch (erro) {
            disponivel = false;
            statusIA.textContent = "Não foi possível consultar o assistente de IA.";
        }
        statusIA.className = disponivel ? "status-ia disponivel" : "status-ia indisponivel";
    }

    async function consultar(pedido, destino) {
        destino.innerHTML = "<p class=\"carregando\" role=\"status\"><span class=\"giro\" aria-hidden=\"true\"></span> " +
            "Consultando o assistente de IA… Na primeira pergunta o modelo pode levar mais de um minuto para carregar.</p>";
        const controle = new AbortController();
        const prazo = setTimeout(function () { controle.abort(); }, TEMPO_LIMITE_MS);
        try {
            const resposta = await fetch("/api/ia/explicar", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(pedido),
                signal: controle.signal
            });
            const dados = await resposta.json();
            if (!resposta.ok || !dados.sucesso) {
                destino.innerHTML = "<p class=\"falha-ia\">" + escaparHtml(dados.mensagem ||
                    "O assistente de IA não conseguiu responder.") + "</p>";
                return;
            }
            destino.innerHTML = "<p class=\"aviso-ia\">🤖 " + escaparHtml(dados.aviso) + "</p>" +
                "<div class=\"resposta-ia\">" + formatarResposta(dados.resposta) + "</div>";
        } catch (erro) {
            destino.innerHTML = "<p class=\"falha-ia\">" + (erro.name === "AbortError"
                ? "O assistente de IA demorou demais para responder. Tente novamente."
                : "Não foi possível comunicar com o servidor.") + "</p>";
        } finally {
            clearTimeout(prazo);
        }
    }

    // Botões "Explicar com IA" espalhados pela interface.
    document.addEventListener("click", function (evento) {
        const botao = evento.target.closest(".botao-ia");
        if (!botao) {
            return;
        }
        evento.preventDefault();
        evento.stopPropagation();
        const alvo = alvoDoBotao(botao);
        document.getElementById("titulo-dialogo-ia").textContent = TITULOS[alvo.tipo];
        const destino = document.getElementById("conteudo-dialogo-ia");
        if (typeof dialogo.showModal === "function") {
            dialogo.showModal();
        } else {
            dialogo.setAttribute("open", "");
        }
        if (!disponivel) {
            // O status pode ter mudado (ex.: o modelo terminou de baixar).
            verificarStatus();
        }
        consultar(montarPedido(alvo, ultimoCodigo), destino);
    }, true);

    document.getElementById("fechar-dialogo-ia").addEventListener("click", function () {
        if (typeof dialogo.close === "function") {
            dialogo.close();
        } else {
            dialogo.removeAttribute("open");
        }
    });

    // Professor virtual
    const pergunta = document.getElementById("pergunta-ia");
    const respostaProfessor = document.getElementById("resposta-professor");

    document.getElementById("perguntar-ia").addEventListener("click", function () {
        const texto = pergunta.value.trim();
        if (!texto) {
            respostaProfessor.innerHTML = "<p class=\"falha-ia\">Escreva uma pergunta.</p>";
            return;
        }
        const codigo = ultimoCodigo.length <= 4000 ? ultimoCodigo : "";
        consultar(montarPedido({ tipo: "conceito" }, codigo, texto), respostaProfessor);
    });

    document.querySelectorAll(".sugestao-ia").forEach(function (botao) {
        botao.addEventListener("click", function () {
            pergunta.value = botao.textContent;
            pergunta.focus();
        });
    });

    document.addEventListener("analise-concluida", function (evento) {
        ultimoCodigo = evento.detail.codigo;
    });

    verificarStatus();
})();
