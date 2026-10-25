(function () {
    "use strict";

    const exemplos = {
        variavel: "idade = 21",
        soma: "resultado = 10 + 5",
        multiplicacao: "total = 4 * 3",
        condicional: [
            "nota = 7.5",
            "if nota >= 7:",
            "    situacao = \"aprovado\"",
            "else:",
            "    situacao = \"recuperação\""
        ].join("\n"),
        laco: [
            "contador = 0",
            "while contador < 5:",
            "    contador += 1",
            "print(contador)"
        ].join("\n"),
        funcao: [
            "# Calcula a média de dois números",
            "def media(a, b):",
            "    soma = a + b  # soma os valores",
            "    return soma / 2",
            "",
            "resultado = media(8, 6.5)"
        ].join("\n"),
        literais: [
            "inteiro = 42",
            "real = 3.14",
            "cientifico = 1.5e-3",
            "texto = \"Olá, mundo!\"",
            "caractere = 'A'",
            "logico = True",
            "nada = None"
        ].join("\n"),
        operadores: [
            "x = 10",
            "x += 5",
            "y = x ** 2 // 3 % 4",
            "igual = x == y",
            "diferente = x != y",
            "ok = x >= 1 and not y <= 0"
        ].join("\n"),
        erros: [
            "valor = 10 @ 2",
            "1nome = \"Ana\"",
            "preco = 3.14.15",
            "mensagem = \"texto sem fim",
            "total = valor $ 5"
        ].join("\n")
    };

    const TIPOS = [
        "PALAVRA_RESERVADA", "IDENTIFICADOR", "LITERAL_INTEIRO", "LITERAL_REAL",
        "LITERAL_STRING", "OPERADOR", "DELIMITADOR", "NOVA_LINHA", "INDENTA",
        "DEDENTA", "FIM"
    ];

    const ESTRUTURAIS = ["NOVA_LINHA", "INDENTA", "DEDENTA", "FIM"];

    const NOMES = {
        PALAVRA_RESERVADA: "Palavra reservada",
        IDENTIFICADOR: "Identificador",
        LITERAL_INTEIRO: "Literal inteiro",
        LITERAL_REAL: "Literal real",
        LITERAL_STRING: "Literal string",
        OPERADOR: "Operador",
        DELIMITADOR: "Delimitador",
        NOVA_LINHA: "Nova linha",
        INDENTA: "Indenta (abre bloco)",
        DEDENTA: "Dedenta (fecha bloco)",
        FIM: "Fim do código",
        COMENTARIO: "Comentário (ignorado)",
        ERRO: "Erro léxico"
    };

    const ATRASOS = [1400, 900, 550, 300, 120];

    // -- Funções puras (testadas com Node.js) ------------------------------

    function escaparHtml(texto) {
        return String(texto)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#39;");
    }

    function lexemaVisivel(tipo, lexema) {
        if (tipo === "NOVA_LINHA") {
            return lexema ? "\\n" : "(fim do código)";
        }
        if (tipo === "INDENTA") {
            return lexema.replace(/ /g, "·").replace(/\t/g, "→");
        }
        if (lexema === "") {
            return "(vazio)";
        }
        return lexema.replace(/\t/g, "\\t").replace(/\n/g, "\\n");
    }

    function normalizarCodigo(codigo) {
        return codigo.replace(/\r\n?/g, "\n");
    }

    // O scanner conta colunas por caractere (code point), assim como o
    // Python; por isso o texto é convertido com Array.from.
    function inicioDasLinhas(caracteres) {
        const inicios = [0];
        caracteres.forEach(function (c, i) {
            if (c === "\n") {
                inicios.push(i + 1);
            }
        });
        return inicios;
    }

    function deslocamento(inicios, total, linha, coluna) {
        if (linha - 1 >= inicios.length) {
            return total;
        }
        return Math.min(inicios[linha - 1] + coluna - 1, total);
    }

    function calcularSegmentos(codigo, dados) {
        const caracteres = Array.from(normalizarCodigo(codigo));
        const inicios = inicioDasLinhas(caracteres);
        const total = caracteres.length;
        const brutos = [];

        function adicionar(item, classe, origem, indice, prioridade) {
            const inicio = deslocamento(inicios, total, item.linha, item.coluna);
            const tamanho = Array.from(item.lexema || "").length;
            brutos.push({
                inicio: inicio,
                fim: Math.min(inicio + tamanho, total),
                classe: classe,
                origem: origem,
                indice: indice,
                prioridade: prioridade
            });
        }

        (dados.erros || []).forEach(function (e, i) { adicionar(e, "ERRO", "erro", i, 0); });
        (dados.tokens || []).forEach(function (t, i) { adicionar(t, t.tipo, "token", i, 1); });
        (dados.comentarios || []).forEach(function (c, i) { adicionar(c, "COMENTARIO", "comentario", i, 2); });

        // Ordena por posição; na mesma posição, marcas vazias (DEDENTA,
        // FIM) vêm antes, e erros antes de tokens.
        brutos.sort(function (a, b) {
            const vazioA = a.fim === a.inicio ? 0 : 1;
            const vazioB = b.fim === b.inicio ? 0 : 1;
            return (a.inicio - b.inicio) || (vazioA - vazioB) ||
                (a.prioridade - b.prioridade);
        });

        // Remove sobreposições: um erro tem preferência sobre o token
        // que começa na mesma posição.
        const segmentos = [];
        let ultimoFim = 0;
        brutos.forEach(function (s) {
            if (s.inicio >= ultimoFim) {
                segmentos.push(s);
                ultimoFim = Math.max(ultimoFim, s.fim);
            }
        });

        return {
            caracteres: caracteres,
            segmentos: segmentos,
            posicao: function (item) {
                return deslocamento(inicios, total, item.linha, item.coluna);
            }
        };
    }

    function montarPassos(tokens, erros) {
        const pendentes = (erros || []).slice();
        const passos = [];

        function antes(e, t) {
            return e.linha < t.linha || (e.linha === t.linha && e.coluna <= t.coluna);
        }

        (tokens || []).forEach(function (t, i) {
            while (pendentes.length && antes(pendentes[0], t)) {
                passos.push({ origem: "erro", indice: (erros || []).indexOf(pendentes.shift()) });
            }
            passos.push({ origem: "token", indice: i });
        });
        pendentes.forEach(function (e) {
            passos.push({ origem: "erro", indice: erros.indexOf(e) });
        });
        return passos;
    }

    function contarPorTipo(tokens) {
        const contagem = {};
        (tokens || []).forEach(function (t) {
            contagem[t.tipo] = (contagem[t.tipo] || 0) + 1;
        });
        return contagem;
    }

    function renderizarCodigo(caracteres, segmentos, opcoes) {
        opcoes = opcoes || {};
        let html = "";
        let pos = 0;

        segmentos.forEach(function (s) {
            html += escaparHtml(caracteres.slice(pos, s.inicio).join(""));
            pos = Math.max(pos, s.fim);

            let estado = "";
            if (opcoes.estado) {
                estado = opcoes.estado(s);
                if (s.inicio === s.fim && estado !== "atual") {
                    return;
                }
            } else if (s.inicio === s.fim) {
                return;
            }

            const atributos =
                " class=\"tk tk-" + s.classe + (estado ? " " + estado : "") + "\"" +
                " data-origem=\"" + s.origem + "\" data-indice=\"" + s.indice + "\"" +
                " tabindex=\"0\" title=\"" + escaparHtml(NOMES[s.classe] || s.classe) + "\"";

            if (s.inicio === s.fim) {
                html += "<span" + atributos + "><span class=\"marca\">" +
                    escaparHtml(s.classe) + "</span></span>";
                return;
            }

            const texto = caracteres.slice(s.inicio, s.fim).join("");
            if (s.classe === "NOVA_LINHA") {
                html += "<span" + atributos + "><span class=\"marca-nl\">↵</span></span>\n";
                return;
            }
            html += "<span" + atributos + ">" + escaparHtml(texto) + "</span>";
        });

        html += escaparHtml(caracteres.slice(pos).join(""));
        return html;
    }

    const api = {
        exemplos: exemplos,
        escaparHtml: escaparHtml,
        lexemaVisivel: lexemaVisivel,
        calcularSegmentos: calcularSegmentos,
        montarPassos: montarPassos,
        contarPorTipo: contarPorTipo,
        renderizarCodigo: renderizarCodigo
    };

    if (typeof module !== "undefined" && module.exports) {
        module.exports = api;
    }

    if (typeof document === "undefined") {
        return;
    }

        // -- Interface ----------------------------------------------------------

    const campoCodigo = document.getElementById("codigo");
    const seletor = document.getElementById("exemplos");
    const resultado = document.getElementById("resultado");
    const botaoAnalisar = document.getElementById("analisar");
    const painel = document.getElementById("painel");

    let analise = null; // { codigo, dados, caracteres, segmentos, passos }
    let passoAtual = -1;
    let temporizador = null;

    function etiqueta(tipo) {
        return "<span class=\"etiqueta\" style=\"--cor: var(--cor-" + tipo + ")\">" +
            escaparHtml(tipo) + "</span>";
    }

    function itemDe(origem, indice) {
        if (!analise) {
            return null;
        }
        const lista = { token: "tokens", erro: "erros", comentario: "comentarios" }[origem];
        return (analise.dados[lista] || [])[indice] || null;
    }

    function descreverItem(origem, item) {
        if (!item) {
            return "Nenhum token selecionado.";
        }
        if (origem === "erro") {
            return etiqueta("ERRO") + " <strong>" + escaparHtml(item.mensagem) + "</strong>" +
                "<div>" + escaparHtml(item.dica || "") + "</div>";
        }
        if (origem === "comentario") {
            return etiqueta("COMENTARIO") + " <code>" + escaparHtml(item.lexema) + "</code>" +
                "<div>Comentários são lidos pelo scanner, mas descartados: não geram tokens.</div>";
        }
        return etiqueta(item.tipo) +
            " lexema <code>" + escaparHtml(lexemaVisivel(item.tipo, item.lexema)) + "</code>" +
            " — linha " + item.linha + ", coluna " + item.coluna +
            (item.descricao ? " — " + escaparHtml(item.descricao) : "") +
            "<div>" + escaparHtml(item.explicacao || "") + "</div>";
    }

    // Abas
    const botoesAba = document.querySelectorAll(".abas button");

    function abrirAba(nome) {
        botoesAba.forEach(function (b) {
            const ativa = b.dataset.aba === nome;
            b.setAttribute("aria-selected", ativa ? "true" : "false");
            document.getElementById("aba-" + b.dataset.aba).hidden = !ativa;
        });
        if (nome !== "passo") {
            pausar();
        }
    }

    botoesAba.forEach(function (b) {
        b.addEventListener("click", function () { abrirAba(b.dataset.aba); });
    });

    // Código colorido
    const codigoDestacado = document.getElementById("codigo-destacado");
    const detalhe = document.getElementById("detalhe-token");

    function selecionar(origem, indice) {
        codigoDestacado.querySelectorAll(".selecionado").forEach(function (e) {
            e.classList.remove("selecionado");
        });
        const alvo = codigoDestacado.querySelector(
            "[data-origem=\"" + origem + "\"][data-indice=\"" + indice + "\"]"
        );
        if (alvo) {
            alvo.classList.add("selecionado");
            alvo.scrollIntoView({ block: "nearest", inline: "nearest" });
        }
        detalhe.innerHTML = descreverItem(origem, itemDe(origem, indice));
    }

    function ativarSelecao(evento) {
        const alvo = evento.target.closest(".tk");
        if (alvo) {
            selecionar(alvo.dataset.origem, Number(alvo.dataset.indice));
        }
    }

    codigoDestacado.addEventListener("click", ativarSelecao);
    codigoDestacado.addEventListener("keydown", function (evento) {
        if (evento.key === "Enter" || evento.key === " ") {
            evento.preventDefault();
            ativarSelecao(evento);
        }
    });

    function mostrarDestaque() {
        document.getElementById("legenda").innerHTML = TIPOS.concat(["COMENTARIO", "ERRO"])
            .filter(function (t) { return t !== "FIM" && t !== "DEDENTA"; })
            .map(function (t) {
                return "<span style=\"--cor: var(--cor-" + t + ")\">" + escaparHtml(NOMES[t]) + "</span>";
            }).join("");
        codigoDestacado.innerHTML = renderizarCodigo(analise.caracteres, analise.segmentos);
        detalhe.textContent = "Nenhum token selecionado.";
    }

    // Passo a passo
    const passoCodigo = document.getElementById("passo-codigo");
    const passoExplicacao = document.getElementById("passo-explicacao");
    const passoContador = document.getElementById("passo-contador");
    const passoTabela = document.querySelector("#passo-tabela tbody");
    const botaoPlay = document.getElementById("passo-play");

    function linhaTabela(numero, origem, item) {
        if (origem === "erro") {
            return "<tr class=\"linha-erro\"><td>" + numero + "</td><td>" + etiqueta("ERRO") +
                "</td><td><code>" + escaparHtml(item.lexema) + "</code></td><td>" + item.linha +
                "</td><td>" + item.coluna + "</td></tr>";
        }
        return "<tr><td>" + numero + "</td><td>" + etiqueta(item.tipo) + "</td><td><code>" +
            escaparHtml(lexemaVisivel(item.tipo, item.lexema)) + "</code></td><td>" + item.linha +
            "</td><td>" + item.coluna + "</td></tr>";
    }

    function irParaPasso(n) {
        const passos = analise.passos;
        passoAtual = Math.max(-1, Math.min(n, passos.length - 1));

        const mapa = {};
        passos.forEach(function (p, i) { mapa[p.origem + ":" + p.indice] = i; });
        const atual = passos[passoAtual];
        let posicaoAtual = -1;
        if (atual) {
            const segAtual = analise.segmentos.find(function (s) {
                return s.origem === atual.origem && s.indice === atual.indice;
            });
            posicaoAtual = segAtual
                ? segAtual.inicio
                : analise.posicao(itemDe(atual.origem, atual.indice));
        }

        passoCodigo.innerHTML = renderizarCodigo(analise.caracteres, analise.segmentos, {
            estado: function (s) {
                const indice = mapa[s.origem + ":" + s.indice];
                if (indice === undefined) {
                    return s.inicio < posicaoAtual ? "" : "pendente";
                }
                if (indice === passoAtual) {
                    return "atual";
                }
                return indice < passoAtual ? "" : "pendente";
            }
        });
        const marcado = passoCodigo.querySelector(".atual");
        if (marcado) {
            marcado.scrollIntoView({ block: "nearest", inline: "nearest" });
        }

        passoContador.textContent = "Passo " + (passoAtual + 1) + " de " + passos.length;
        passoExplicacao.innerHTML = atual
            ? descreverItem(atual.origem, itemDe(atual.origem, atual.indice))
            : "Clique em ▶ para o scanner começar a ler o código a partir da linha 1, coluna 1.";

        passoTabela.innerHTML = passos.slice(0, passoAtual + 1).map(function (p, i) {
            return linhaTabela(i + 1, p.origem, itemDe(p.origem, p.indice));
        }).join("");

        document.getElementById("passo-anterior").disabled = passoAtual < 0;
        document.getElementById("passo-inicio").disabled = passoAtual < 0;
        document.getElementById("passo-proximo").disabled = passoAtual >= passos.length - 1;
        document.getElementById("passo-fim").disabled = passoAtual >= passos.length - 1;
    }

    function pausar() {
        if (temporizador) {
            clearTimeout(temporizador);
            temporizador = null;
        }
        botaoPlay.textContent = "▶ Reproduzir";
        botaoPlay.setAttribute("aria-label", "Reproduzir");
    }

    function reproduzir() {
        if (!analise) {
            return;
        }
        if (passoAtual >= analise.passos.length - 1) {
            irParaPasso(-1);
        }
        botaoPlay.textContent = "⏸ Pausar";
        botaoPlay.setAttribute("aria-label", "Pausar");
        (function proximo() {
            irParaPasso(passoAtual + 1);
            if (passoAtual >= analise.passos.length - 1) {
                pausar();
                return;
            }
            const velocidade = Number(document.getElementById("passo-velocidade").value);
            temporizador = setTimeout(proximo, ATRASOS[velocidade - 1]);
        })();
    }

    botaoPlay.addEventListener("click", function () {
        if (temporizador) {
            pausar();
        } else {
            reproduzir();
        }
    });
    document.getElementById("passo-proximo").addEventListener("click", function () {
        pausar();
        irParaPasso(passoAtual + 1);
    });
    document.getElementById("passo-anterior").addEventListener("click", function () {
        pausar();
        irParaPasso(passoAtual - 1);
    });
    document.getElementById("passo-inicio").addEventListener("click", function () {
        pausar();
        irParaPasso(-1);
    });
    document.getElementById("passo-fim").addEventListener("click", function () {
        pausar();
        irParaPasso(analise.passos.length - 1);
    });

    // Tabela de tokens
    const filtroTipo = document.getElementById("filtro-tipo");
    const mostrarEstruturais = document.getElementById("mostrar-estruturais");
    const corpoTabela = document.querySelector("#tabela-tokens tbody");

    function mostrarTabela() {
        const tipo = filtroTipo.value;
        const linhas = [];
        analise.dados.tokens.forEach(function (t, i) {
            if (tipo && t.tipo !== tipo) {
                return;
            }
            if (!mostrarEstruturais.checked && ESTRUTURAIS.indexOf(t.tipo) >= 0) {
                return;
            }
            linhas.push(
                "<tr data-indice=\"" + i + "\"><td>" + (i + 1) + "</td><td>" + etiqueta(t.tipo) +
                "</td><td><code>" + escaparHtml(lexemaVisivel(t.tipo, t.lexema)) + "</code></td><td>" +
                t.linha + "</td><td>" + t.coluna + "</td><td>" + escaparHtml(t.descricao || "") +
                "</td></tr>"
            );
        });
        corpoTabela.innerHTML = linhas.join("") ||
            "<tr><td colspan=\"6\">Nenhum token nesta categoria.</td></tr>";
    }

    filtroTipo.addEventListener("change", mostrarTabela);
    mostrarEstruturais.addEventListener("change", mostrarTabela);
    corpoTabela.addEventListener("click", function (evento) {
        const linha = evento.target.closest("tr[data-indice]");
        if (linha) {
            abrirAba("destaque");
            selecionar("token", Number(linha.dataset.indice));
        }
    });

    // Sequência de tokens
    function mostrarSequencia() {
        const linhasCodigo = normalizarCodigo(analise.codigo).split("\n");
        // Agrupa tokens e erros por linha, na ordem em que o scanner os leu.
        const porLinha = {};
        analise.passos.forEach(function (p) {
            const item = itemDe(p.origem, p.indice);
            (porLinha[item.linha] = porLinha[item.linha] || []).push(
                p.origem === "erro" ? { tipo: "ERRO", lexema: item.lexema } : item
            );
        });
        const comentarios = {};
        (analise.dados.comentarios || []).forEach(function (c) { comentarios[c.linha] = true; });

        let html = "<div class=\"cabecalho\">Código original</div>" +
            "<div class=\"cabecalho\">Sequência de tokens</div>";
        const totalLinhas = Math.max(linhasCodigo.length,
            analise.dados.tokens.length ? analise.dados.tokens[analise.dados.tokens.length - 1].linha : 0);

        for (let n = 1; n <= totalLinhas; n++) {
            const pares = (porLinha[n] || []).map(function (t) {
                return "<span class=\"par\" style=\"--cor: var(--cor-" + t.tipo + ")\">&lt;" +
                    escaparHtml(t.tipo === "ERRO" ? "ERRO_LEXICO" : t.tipo) + (t.lexema && t.tipo !== "INDENTA"
                        ? ", " + escaparHtml(lexemaVisivel(t.tipo, t.lexema)) : "") + "&gt;</span>";
            }).join("");
            let vazio = "<em>(linha em branco: nenhum token)</em>";
            if (comentarios[n]) {
                vazio = "<em>(comentário: ignorado)</em>";
            }
            html += "<div class=\"original\">" + n + "  " + escaparHtml(linhasCodigo[n - 1] || "") + "</div>" +
                "<div class=\"tokens\">" + (pares || vazio) + "</div>";
        }
        document.getElementById("comparacao").innerHTML = html;
    }

    // Resumo
    function mostrarResumo() {
        const contagem = contarPorTipo(analise.dados.tokens);
        const maximo = Math.max.apply(null, Object.values(contagem).concat([1]));
        const barras = TIPOS.filter(function (t) { return contagem[t]; }).map(function (t) {
            return "<div class=\"barra\" style=\"--cor: var(--cor-" + t + ")\"><span>" +
                escaparHtml(NOMES[t]) + "</span><div class=\"trilho\"><div class=\"preenchido\" style=\"width:" +
                (100 * contagem[t] / maximo) + "%\"></div></div><strong>" + contagem[t] + "</strong></div>";
        }).join("");

        const identificadores = [];
        analise.dados.tokens.forEach(function (t) {
            if (t.tipo === "IDENTIFICADOR" && identificadores.indexOf(t.lexema) < 0) {
                identificadores.push(t.lexema);
            }
        });

        document.getElementById("resumo").innerHTML =
            "<p><strong>" + analise.dados.tokens.length + "</strong> token(s), <strong>" +
            analise.dados.erros.length + "</strong> erro(s) léxico(s) e <strong>" +
            (analise.dados.comentarios || []).length + "</strong> comentário(s) descartado(s).</p>" +
            barras +
            "<h3>Identificadores distintos</h3><p>" +
            (identificadores.length
                ? identificadores.map(function (i) { return "<code>" + escaparHtml(i) + "</code>"; }).join(" ")
                : "Nenhum.") +
            "</p><p class=\"ajuda\">Nas próximas etapas, esses nomes formarão a tabela de símbolos.</p>";
    }

    // Erros
    const areaErros = document.getElementById("erros");

    function mostrarErros() {
        const erros = analise.dados.erros;
        if (!erros.length) {
            areaErros.innerHTML = "<p class=\"sem-erros\">Nenhum erro léxico encontrado.</p>";
            return;
        }
        areaErros.innerHTML = erros.map(function (e, i) {
            return "<div class=\"erro\" tabindex=\"0\" data-indice=\"" + i + "\"><strong>" +
                escaparHtml(e.mensagem) + "</strong><div class=\"dica\">" + escaparHtml(e.dica || "") +
                "</div></div>";
        }).join("");
    }

    function abrirErro(evento) {
        const alvo = evento.target.closest(".erro");
        if (alvo) {
            abrirAba("destaque");
            selecionar("erro", Number(alvo.dataset.indice));
        }
    }

    areaErros.addEventListener("click", abrirErro);
    areaErros.addEventListener("keydown", function (evento) {
        if (evento.key === "Enter") {
            abrirErro(evento);
        }
    });

    function mostrarAnalise(codigo, dados) {
        pausar();
        const calculo = calcularSegmentos(codigo, dados);
        analise = {
            codigo: codigo,
            dados: dados,
            caracteres: calculo.caracteres,
            segmentos: calculo.segmentos,
            posicao: calculo.posicao,
            passos: montarPassos(dados.tokens, dados.erros)
        };

        filtroTipo.innerHTML = "<option value=\"\">Todas</option>" + TIPOS.map(function (t) {
            return "<option value=\"" + t + "\">" + escaparHtml(NOMES[t]) + "</option>";
        }).join("");

        mostrarDestaque();
        irParaPasso(-1);
        mostrarTabela();
        mostrarSequencia();
        mostrarResumo();
        mostrarErros();
        painel.hidden = false;
    }

    function esconderAnalise() {
        pausar();
        analise = null;
        painel.hidden = true;
    }

    // Fluxo principal (Etapa 2, ampliado)
    seletor.addEventListener("change", function () {
        if (exemplos[seletor.value]) {
            campoCodigo.value = exemplos[seletor.value];
        }
        resultado.textContent = "Aguardando código...";
        resultado.className = "";
        esconderAnalise();
    });

    botaoAnalisar.addEventListener("click", async function () {
        const codigo = campoCodigo.value;

        if (!codigo.trim()) {
            resultado.textContent =
                "Informe um código-fonte antes de solicitar a análise.";
            resultado.className = "falha";
            esconderAnalise();
            return;
        }

        resultado.textContent = "Enviando código...";
        resultado.className = "";
        botaoAnalisar.disabled = true;

        try {
            const resposta = await fetch("/api/analisar", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ codigo: codigo })
            });

            const dados = await resposta.json();

            resultado.textContent =
                dados.mensagem || "Erro ao processar a resposta.";

            if (resposta.ok && Array.isArray(dados.tokens)) {
                resultado.className = dados.sucesso ? "sucesso" : "falha";
                mostrarAnalise(codigo, dados);
            } else {
                resultado.className = "falha";
                esconderAnalise();
            }
        } catch (erro) {
            resultado.textContent =
                "Não foi possível comunicar com o servidor.";
            resultado.className = "falha";
            esconderAnalise();
        } finally {
            botaoAnalisar.disabled = false;
        }
    });

    // Escopo léxico (carregado do backend, que é a fonte única da verdade)
    async function carregarEscopo() {
        const destino = document.getElementById("escopo-conteudo");
        try {
            const resposta = await fetch("/api/escopo");
            const escopo = await resposta.json();
            const lista = function (itens) {
                return itens.map(function (i) {
                    return "<tr><td><code>" + escaparHtml(i.lexema) + "</code></td><td>" +
                        escaparHtml(i.descricao) + "</td></tr>";
                }).join("");
            };
            destino.innerHTML =
                "<div class=\"rolavel\"><table><thead><tr><th>Categoria</th><th>Regra / exemplos</th></tr></thead><tbody>" +
                "<tr><td>Palavras reservadas</td><td>" + escopo.palavras_reservadas.map(function (p) {
                    return "<code>" + escaparHtml(p) + "</code>";
                }).join(" ") + "</td></tr>" +
                "<tr><td>Identificadores</td><td>letra ou <code>_</code>, seguida de letras, dígitos ou <code>_</code> (ex.: <code>numero</code>, <code>_x1</code>, <code>média</code>)</td></tr>" +
                "<tr><td>Literais inteiros</td><td><code>0</code>, <code>42</code>, <code>1_000</code></td></tr>" +
                "<tr><td>Literais reais</td><td><code>3.14</code>, <code>.5</code>, <code>1e10</code>, <code>1.5e-3</code></td></tr>" +
                "<tr><td>Literais string</td><td><code>\"texto\"</code>, <code>'texto'</code>, <code>\"\"\"várias linhas\"\"\"</code>, <code>f\"...\"</code></td></tr>" +
                "<tr><td>Comentários</td><td><code># até o fim da linha</code> (ignorados)</td></tr>" +
                "<tr><td>Espaços</td><td>ignorados entre tokens; no início da linha geram <code>INDENTA</code>/<code>DEDENTA</code></td></tr>" +
                "</tbody></table></div>" +
                "<h3>Operadores</h3><div class=\"rolavel\"><table><tbody>" + lista(escopo.operadores) + "</tbody></table></div>" +
                "<h3>Delimitadores</h3><div class=\"rolavel\"><table><tbody>" + lista(escopo.delimitadores) + "</tbody></table></div>";
        } catch (erro) {
            destino.textContent = "Não foi possível carregar o escopo léxico do servidor.";
        }
    }

    carregarEscopo();
})();
