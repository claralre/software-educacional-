(function () {
    "use strict";

    // Funções compartilhadas com arvore.js (no navegador, window.ArvoreAPI;
    // no Node.js, require).
    const arvore = (typeof window !== "undefined" && window.ArvoreAPI) ||
        (typeof require === "function" ? require("./arvore.js") : null);
    const escaparHtml = arvore.escaparHtml;
    const prepararCodigo = arvore.prepararCodigo;

    const CATEGORIAS = {
        variavel: "variável",
        funcao: "função",
        parametro: "parâmetro",
        embutida: "função embutida"
    };

    const DICA_ESCOPO = {
        global: "nomes definidos fora de qualquer função; valem no programa inteiro",
        funcao: "nomes que recebem valor dentro desta função (variáveis locais e parâmetros); só valem nela",
        embutido: "funções que já vêm com o Python, como print e len"
    };

    // -- Funções puras (testadas com Node.js) ------------------------------

    function rotuloCategoria(categoria) {
        return CATEGORIAS[categoria] || categoria;
    }

    function descreverTipo(simbolo) {
        if (simbolo.categoria === "funcao" || simbolo.categoria === "embutida") {
            const parametros = simbolo.categoria === "embutida"
                ? (simbolo.argumentos ? simbolo.argumentos + " arg." : "")
                : (simbolo.parametros || []).join(", ");
            return "função(" + parametros + ") → " + (simbolo.retorno || "desconhecido");
        }
        const tipos = simbolo.tipos || [];
        if (simbolo.tipo === "desconhecido" && tipos.length) {
            // Começou com um tipo conhecido e depois recebeu um valor de tipo desconhecido.
            return tipos.join(" → ") + " → desconhecido";
        }
        if (tipos.length > 1) {
            return tipos.join(" → ");
        }
        return simbolo.tipo;
    }

    function agruparPorEscopo(tabela, escopos) {
        return (escopos || []).map(function (escopo) {
            return {
                escopo: escopo,
                simbolos: (tabela || []).map(function (s, i) { return { simbolo: s, indice: i }; })
                    .filter(function (item) { return item.simbolo.escopo === escopo.nome; })
            };
        }).filter(function (grupo) { return grupo.simbolos.length || grupo.escopo.tipo !== "embutido"; });
    }

    function faixaDe(item) {
        return { linha: item.linha, coluna: item.coluna,
            linha_fim: item.linha_fim || item.linha, coluna_fim: item.coluna_fim || item.coluna };
    }

    // Trechos a destacar ao selecionar um símbolo: a definição e cada uso.
    function faixasDoSimbolo(simbolo) {
        const faixas = [];
        if (simbolo.linha) {
            faixas.push({ faixa: faixaDe(simbolo), classe: "destaque-def" });
        }
        (simbolo.usos || []).forEach(function (uso) {
            faixas.push({ faixa: faixaDe(uso), classe: "destaque-uso" });
        });
        return faixas;
    }

    // Código com vários trechos marcados (sem sobreposição: o primeiro vence).
    function renderizarCodigoMarcado(preparado, faixas) {
        const c = preparado.caracteres;
        const intervalos = (faixas || []).map(function (f) {
            const inicio = preparado.posicao(f.faixa.linha, f.faixa.coluna);
            const fim = Math.max(preparado.posicao(f.faixa.linha_fim, f.faixa.coluna_fim) + 1, inicio + 1);
            return { inicio: inicio, fim: fim, classe: f.classe };
        }).sort(function (a, b) { return a.inicio - b.inicio; });
        let html = "";
        let cursor = 0;
        intervalos.forEach(function (it) {
            if (it.inicio < cursor) {
                return;
            }
            html += escaparHtml(c.slice(cursor, it.inicio).join("")) +
                "<mark class=\"" + it.classe + "\">" + escaparHtml(c.slice(it.inicio, it.fim).join("")) + "</mark>";
            cursor = it.fim;
        });
        return html + escaparHtml(c.slice(cursor).join(""));
    }

    // Situação das três fases, para o estudante ver onde a análise parou.
    function resumoFases(dados) {
        const lexico = dados.lexico || { sucesso: dados.sucesso, erros: dados.erros || [] };
        const sintatico = dados.sintatico || { executado: false };
        const semantico = dados.semantico || { executado: false };
        function fase(nome, executado, sucesso, erros, avisos) {
            if (!executado) {
                return { fase: nome, estado: "nao_executada", texto: "não executada" };
            }
            if (!sucesso) {
                return { fase: nome, estado: "erro", texto: erros + " erro(s)" };
            }
            if (avisos) {
                return { fase: nome, estado: "aviso", texto: "ok, " + avisos + " aviso(s)" };
            }
            return { fase: nome, estado: "ok", texto: "ok" };
        }
        return [
            fase("Léxica", true, lexico.sucesso, (lexico.erros || []).length, 0),
            fase("Sintática", sintatico.executado, sintatico.sucesso, (sintatico.erros || []).length, 0),
            fase("Semântica", semantico.executado, semantico.sucesso, (semantico.erros || []).length,
                (semantico.avisos || []).length)
        ];
    }

    const api = {
        rotuloCategoria: rotuloCategoria,
        descreverTipo: descreverTipo,
        agruparPorEscopo: agruparPorEscopo,
        faixasDoSimbolo: faixasDoSimbolo,
        renderizarCodigoMarcado: renderizarCodigoMarcado,
        resumoFases: resumoFases
    };

    if (typeof module !== "undefined" && module.exports) {
        module.exports = api;
    }

    if (typeof document === "undefined") {
        return;
    }

    // -- Interface ----------------------------------------------------------

    const painel = document.getElementById("painel-semantico");
    const fases = document.getElementById("fases");
    const status = document.getElementById("resultado-semantico");
    const conteudo = document.getElementById("semantico-conteudo");
    const codigoSemantico = document.getElementById("codigo-semantico");
    const areaTabela = document.getElementById("tabela-simbolos");
    const detalhe = document.getElementById("detalhe-simbolo");
    const areaErros = document.getElementById("erros-semanticos");
    const areaAvisos = document.getElementById("avisos-semanticos");
    const blocoAvisos = document.getElementById("bloco-avisos");
    const listaRegras = document.getElementById("lista-regras-semanticas");

    let estado = null; // { codigo, dados, preparado }
    let regras = null;

    function botaoIA(tipo, indice, texto, lista) {
        return "<button type=\"button\" class=\"botao-ia\" data-ia-tipo=\"" + tipo + "\" data-ia-indice=\"" +
            indice + "\"" + (lista ? " data-ia-lista=\"" + lista + "\"" : "") + ">✨ " + escaparHtml(texto) + "</button>";
    }

    function botaoAst(id) {
        return id === null || id === undefined ? "" :
            "<button type=\"button\" class=\"ver-no\" data-no-id=\"" + id + "\">🌳 Ver o nó na AST</button>";
    }

    // Abas
    const botoesAba = document.querySelectorAll(".abas-semanticas button");

    function abrirAba(nome) {
        botoesAba.forEach(function (b) {
            const ativa = b.dataset.aba === nome;
            b.setAttribute("aria-selected", ativa ? "true" : "false");
            document.getElementById("aba-" + b.dataset.aba).hidden = !ativa;
        });
    }

    botoesAba.forEach(function (b) {
        b.addEventListener("click", function () { abrirAba(b.dataset.aba); });
    });

    async function carregarRegras() {
        try {
            const resposta = await fetch("/api/semantica");
            regras = await resposta.json();
            listaRegras.innerHTML = regras.regras.map(function (r) {
                return "<li data-regra=\"" + r.codigo + "\"><strong>" + escaparHtml(r.titulo) + "</strong> " +
                    "<span class=\"etiqueta-erro " + (r.gravidade === "erro" ? "semantico" : "aviso") + "\">" +
                    (r.gravidade === "erro" ? "ERRO" : "AVISO") + "</span> <code>" + escaparHtml(r.codigo) +
                    "</code><br>" + escaparHtml(r.explicacao) +
                    "<br><span class=\"ajuda\">Ao executar, o Python mostraria: <strong>" +
                    escaparHtml(r.erro_python) + "</strong></span></li>";
            }).join("");
        } catch (erro) {
            listaRegras.textContent = "Não foi possível carregar as regras semânticas.";
        }
    }

    function destacarRegra(codigo) {
        listaRegras.querySelectorAll("li").forEach(function (li) {
            li.classList.toggle("regra-ativa", li.dataset.regra === codigo);
        });
    }

    function mostrarFases(dados) {
        fases.innerHTML = resumoFases(dados).map(function (f, i) {
            const simbolo = { ok: "✔", aviso: "⚠", erro: "✖", nao_executada: "–" }[f.estado];
            return (i ? "<span class=\"seta-fase\" aria-hidden=\"true\">→</span>" : "") +
                "<span class=\"fase fase-" + f.estado + "\"><span aria-hidden=\"true\">" + simbolo + "</span> " +
                "<strong>" + f.fase + "</strong>: " + escaparHtml(f.texto) + "</span>";
        }).join("");
    }

    function mostrarTabela() {
        const semantico = estado.dados.semantico;
        const grupos = agruparPorEscopo(semantico.tabela_simbolos, semantico.escopos);
        areaTabela.innerHTML = grupos.map(function (grupo) {
            const e = grupo.escopo;
            const linhas = grupo.simbolos.map(function (item) {
                const s = item.simbolo;
                const usos = s.usos.length
                    ? s.usos.length + " (" + s.usos.slice(0, 4).map(function (u) { return "l." + u.linha; }).join(", ") +
                      (s.usos.length > 4 ? ", …" : "") + ")"
                    : "<span class=\"nao-usado\">nenhum</span>";
                return "<tr tabindex=\"0\" data-indice=\"" + item.indice + "\">" +
                    "<td><code>" + escaparHtml(s.nome) + "</code>" +
                    (s.sombreia ? " <span class=\"marca-sombra\" title=\"Sombreia " + escaparHtml(s.sombreia) +
                        "\">sombreia</span>" : "") + "</td>" +
                    "<td>" + escaparHtml(rotuloCategoria(s.categoria)) + "</td>" +
                    "<td><code>" + escaparHtml(descreverTipo(s)) + "</code></td>" +
                    "<td>" + (s.linha ? "linha " + s.linha + ", coluna " + s.coluna : "embutida") + "</td>" +
                    "<td>" + usos + "</td></tr>";
            }).join("");
            return "<div class=\"grupo-escopo escopo-" + e.tipo + "\">" +
                "<h3>" + escaparHtml(e.rotulo) + (e.linha && e.tipo === "funcao" ? " <span class=\"ajuda\">(linha " +
                    e.linha + ")</span>" : "") + "</h3>" +
                "<p class=\"ajuda\">" + escaparHtml(DICA_ESCOPO[e.tipo]) +
                (e.pai && e.tipo === "funcao" ? ". Escopo externo: " + escaparHtml(e.pai) : "") + ".</p>" +
                (linhas
                    ? "<div class=\"rolavel\"><table><thead><tr><th>Nome</th><th>Categoria</th><th>Tipo (inferido)</th>" +
                      "<th>Definido em</th><th>Usos</th></tr></thead><tbody>" + linhas + "</tbody></table></div>"
                    : "<p class=\"ajuda\">Nenhum nome neste escopo.</p>") +
                "</div>";
        }).join("") || "<p class=\"ajuda\">O programa não define nem usa nenhum nome.</p>";
    }

    function selecionarSimbolo(indice) {
        const s = estado.dados.semantico.tabela_simbolos[indice];
        if (!s) {
            return;
        }
        areaTabela.querySelectorAll("tr.selecionado").forEach(function (tr) { tr.classList.remove("selecionado"); });
        const linha = areaTabela.querySelector("tr[data-indice=\"" + indice + "\"]");
        if (linha) {
            linha.classList.add("selecionado");
        }
        codigoSemantico.innerHTML = renderizarCodigoMarcado(estado.preparado, faixasDoSimbolo(s));
        const marca = codigoSemantico.querySelector("mark");
        if (marca) {
            marca.scrollIntoView({ block: "nearest", inline: "nearest" });
        }
        const explicaTipo = s.categoria === "parametro"
            ? "Parâmetros podem receber valores de qualquer tipo na chamada, então o tipo fica desconhecido."
            : s.categoria === "embutida" ? "Função que já vem com o Python."
            : s.tipo === "desconhecido" ? "Não foi possível saber o tipo só lendo o código (por exemplo, o valor vem de um parâmetro ou de uma função)."
            : "Tipo inferido a partir do valor atribuído: Python não declara tipos, cada valor carrega o seu.";
        detalhe.innerHTML =
            "<p><strong><code>" + escaparHtml(s.nome) + "</code></strong> — " + escaparHtml(rotuloCategoria(s.categoria)) +
            " do <strong>" + escaparHtml(s.escopo_rotulo.toLowerCase()) + "</strong></p>" +
            "<p>Tipo: <code>" + escaparHtml(descreverTipo(s)) + "</code>. " + escaparHtml(explicaTipo) + "</p>" +
            (s.tipos && s.tipos.length > 1 ? "<p>Recebeu valores de tipos diferentes ao longo do programa: " +
                escaparHtml(s.tipos.join(", ")) + ".</p>" : "") +
            (s.linha ? "<p>Definido na linha " + s.linha + ", coluna " + s.coluna + " (destaque <mark class=\"destaque-def\">" +
                "verde</mark> no código)" + (s.atribuicoes > 1 ? "; recebe valor " + s.atribuicoes + " vezes" : "") + ".</p>" : "") +
            "<p>Usado " + s.usos.length + " vez(es)" + (s.usos.length ? " (destaque <mark class=\"destaque-uso\">azul</mark>)" : "") +
            ".</p>" +
            (s.sombreia ? "<p>Este nome <strong>sombreia</strong> " + escaparHtml(s.sombreia) +
                ": dentro deste escopo, o nome se refere a este símbolo, e não ao de fora.</p>" : "") +
            botaoAst(s.no_id) + " " + botaoIA("simbolo", indice, "Explicar este símbolo com IA");
    }

    function htmlDiagnostico(d, i, lista) {
        const erro = lista === "erros";
        return "<div class=\"erro " + (erro ? "erro-semantico" : "aviso-semantico") + "\" tabindex=\"0\" data-lista=\"" +
            lista + "\" data-indice=\"" + i + "\">" +
            "<span class=\"etiqueta-erro " + (erro ? "semantico" : "aviso") + "\">" +
            (erro ? "ERRO SEMÂNTICO" : "AVISO SEMÂNTICO") + "</span> <strong>" + escaparHtml(d.mensagem) + "</strong>" +
            "<div class=\"dica\"><strong>Regra:</strong> " + escaparHtml(d.titulo) + " <code>" + escaparHtml(d.regra) + "</code></div>" +
            "<div class=\"dica\"><strong>Por quê:</strong> " + escaparHtml(d.explicacao) + "</div>" +
            (d.sugestao ? "<div class=\"dica sugestao\"><strong>💡 Como corrigir:</strong> " + escaparHtml(d.sugestao) + "</div>" : "") +
            "<div class=\"dica\">Ao executar, o Python mostraria: <strong>" + escaparHtml(d.erro_python) + "</strong></div>" +
            botaoAst(d.no_id) + " " + botaoIA("erro_semantico", i, erro ? "Entender erro com IA" : "Entender aviso com IA",
                erro ? "" : "avisos") +
            "</div>";
    }

    function mostrarDiagnosticos() {
        const semantico = estado.dados.semantico;
        areaErros.innerHTML = semantico.erros.length
            ? semantico.erros.map(function (d, i) { return htmlDiagnostico(d, i, "erros"); }).join("")
            : "<p class=\"sem-erros\">Nenhum erro semântico encontrado.</p>";
        areaAvisos.innerHTML = semantico.avisos.length
            ? semantico.avisos.map(function (d, i) { return htmlDiagnostico(d, i, "avisos"); }).join("")
            : "<p class=\"ajuda\">Nenhum aviso.</p>";
    }

    function selecionarDiagnostico(alvo) {
        const d = estado.dados.semantico[alvo.dataset.lista][Number(alvo.dataset.indice)];
        codigoSemantico.innerHTML = renderizarCodigoMarcado(estado.preparado,
            [{ faixa: faixaDe(d), classe: alvo.dataset.lista === "erros" ? "destaque-erro" : "destaque-aviso" }]);
        destacarRegra(d.regra);
        codigoSemantico.scrollIntoView({ block: "nearest" });
    }

    function aoClicarDiagnostico(evento) {
        if (evento.target.closest(".botao-ia, .ver-no")) {
            return;
        }
        const alvo = evento.target.closest(".erro");
        if (alvo) {
            selecionarDiagnostico(alvo);
        }
    }

    [areaErros, areaAvisos].forEach(function (area) {
        area.addEventListener("click", aoClicarDiagnostico);
        area.addEventListener("keydown", function (evento) {
            if (evento.key === "Enter") {
                aoClicarDiagnostico(evento);
            }
        });
    });

    areaTabela.addEventListener("click", function (evento) {
        const tr = evento.target.closest("tr[data-indice]");
        if (tr) {
            selecionarSimbolo(Number(tr.dataset.indice));
        }
    });
    areaTabela.addEventListener("keydown", function (evento) {
        const tr = evento.target.closest("tr[data-indice]");
        if (tr && evento.key === "Enter") {
            selecionarSimbolo(Number(tr.dataset.indice));
        }
    });

    // Relação com a AST: pede ao módulo da árvore para selecionar o nó.
    document.addEventListener("click", function (evento) {
        const botao = evento.target.closest(".ver-no");
        if (botao && painel.contains(botao)) {
            document.dispatchEvent(new CustomEvent("mostrar-no-ast", { detail: { id: Number(botao.dataset.noId) } }));
        }
    });

    function mostrar(codigo, dados) {
        estado = { codigo: codigo, dados: dados, preparado: prepararCodigo(codigo) };
        painel.hidden = false;
        mostrarFases(dados);
        const semantico = dados.semantico;
        status.textContent = semantico ? semantico.mensagem : "";
        status.className = semantico && semantico.executado && semantico.sucesso ? "sucesso" : "falha";

        if (!semantico || !semantico.executado) {
            conteudo.hidden = true;
            areaErros.innerHTML = "<p class=\"aviso-nao-executado\">A análise semântica percorre a AST, que só existe " +
                "quando o código não tem erros léxicos nem sintáticos. Corrija os erros indicados acima e analise de novo.</p>";
            areaAvisos.innerHTML = "";
            blocoAvisos.hidden = true;
            return;
        }
        conteudo.hidden = false;
        blocoAvisos.hidden = false;
        codigoSemantico.innerHTML = renderizarCodigoMarcado(estado.preparado, []);
        detalhe.innerHTML = "Selecione um símbolo da tabela para ver onde ele é definido e usado no código.";
        mostrarTabela();
        mostrarDiagnosticos();
        destacarRegra(null);
        abrirAba("simbolos");
    }

    function esconder() {
        estado = null;
        painel.hidden = true;
        fases.innerHTML = "";
    }

    document.addEventListener("analise-concluida", function (evento) {
        mostrar(evento.detail.codigo, evento.detail.dados);
    });
    document.addEventListener("analise-limpa", esconder);

    carregarRegras();
})();
