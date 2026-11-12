(function () {
    "use strict";

    // Forma + cor por categoria de nó (a forma garante que a informação não
    // dependa só da cor).
    const FORMAS = {
        estrutura: "▣",
        comando: "■",
        expressao: "●",
        literal: "◆"
    };

    const NOMES_CATEGORIA = {
        estrutura: "estrutura do programa",
        comando: "comando",
        expressao: "expressão (operação)",
        literal: "valor ou nome"
    };

    const PAPEIS = {
        comando: "comando",
        alvo: "alvo",
        valor: "valor",
        expressao: "expressão",
        condicao: "condição",
        entao: "então",
        senao: "senão",
        senao_se: "senão se",
        corpo: "corpo",
        variavel: "variável",
        iteravel: "sequência",
        parametro: "parâmetro",
        esquerda: "esquerda",
        direita: "direita",
        operando: "operando",
        funcao: "função",
        argumento: "argumento",
        objeto: "objeto",
        indice: "índice",
        elemento: "elemento"
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

    function rotuloNo(no) {
        const a = no.atributos || {};
        switch (no.tipo) {
        case "IDENTIFICADOR":
            return "Identificador: " + a.nome;
        case "NUMERO_INTEIRO":
        case "NUMERO_REAL":
        case "TEXTO":
        case "LOGICO":
        case "NULO":
            return no.rotulo + ": " + a.valor;
        case "PARAMETRO":
            return "Parâmetro: " + a.nome;
        case "FUNCAO":
            return "Função " + a.nome + "(" + (a.parametros || []).join(", ") + ")";
        case "CHAMADA":
            return a.nome ? "Chamada: " + a.nome + "(…)" : "Chamada de função";
        case "PARA":
            return "Para (for): " + a.variavel;
        case "ACESSO_ATRIBUTO":
            return "Atributo: ." + a.atributo;
        case "LISTA":
            return "Lista (" + a.total_elementos + " elemento(s))";
        default:
            return a.operador ? no.rotulo + " (" + a.operador + ")" : no.rotulo;
        }
    }

    function papelLegivel(papel) {
        return papel ? (PAPEIS[papel] || papel) : "";
    }

    function indexarNos(raiz) {
        const indice = {};
        (function visitar(no, pai) {
            indice[no.id] = { no: no, pai: pai };
            no.filhos.forEach(function (filho) { visitar(filho, no); });
        })(raiz, null);
        return indice;
    }

    function botaoNo(no, extraClasse) {
        return "<button type=\"button\" class=\"no-ast cat-" + no.categoria +
            (extraClasse ? " " + extraClasse : "") + "\" data-id=\"" + no.id + "\" " +
            "title=\"" + escaparHtml(no.tipo + " — regra: " + no.regra) + "\">" +
            "<span class=\"forma\" aria-hidden=\"true\">" + FORMAS[no.categoria] + "</span>" +
            "<span class=\"rotulo-no\">" + escaparHtml(rotuloNo(no)) + "</span>" +
            "<span class=\"tipo-no\">" + escaparHtml(no.tipo) + "</span>" +
            "</button>";
    }

    function papelHtml(no) {
        return no.papel
            ? "<span class=\"papel\">" + escaparHtml(papelLegivel(no.papel)) + "</span>"
            : "";
    }

    // Árvore hierárquica navegável (nós expansíveis/recolhíveis).
    function renderizarLista(no) {
        if (!no.filhos.length) {
            return "<li>" + papelHtml(no) + botaoNo(no) + "</li>";
        }
        return "<li><details open><summary>" + papelHtml(no) + botaoNo(no) + "</summary><ul>" +
            no.filhos.map(renderizarLista).join("") + "</ul></details></li>";
    }

    // Diagrama (árvore desenhada de cima para baixo). Aceita uma floresta e,
    // opcionalmente, um conjunto de nós visíveis (construção passo a passo).
    function renderizarDiagrama(raizes, opcoes) {
        opcoes = opcoes || {};
        const visivel = opcoes.visiveis
            ? function (no) { return opcoes.visiveis.has(no.id); }
            : function () { return true; };

        function item(no) {
            const filhos = no.filhos.filter(visivel);
            const classe = no.id === opcoes.atual ? "novo" : "";
            return "<li>" + papelHtml(no) + botaoNo(no, classe) +
                (filhos.length ? "<ul>" + filhos.map(item).join("") + "</ul>" : "") + "</li>";
        }

        return "<ul>" + raizes.filter(visivel).map(item).join("") + "</ul>";
    }

    // Árvore de derivação (concreta): não terminais e terminais.
    function renderizarDerivacao(no, nivel) {
        nivel = nivel || 0;
        if (no.terminal) {
            return "<li><span class=\"terminal\" title=\"terminal (token)\">" +
                escaparHtml(no.terminal) +
                (no.lexema && no.lexema !== "\n" ? " <code>" + escaparHtml(no.lexema) + "</code>" : "") +
                "</span></li>";
        }
        return "<li><details" + (nivel < 3 ? " open" : "") + "><summary>" +
            "<span class=\"nao-terminal\" title=\"não terminal (regra da gramática)\">‹" +
            escaparHtml(no.regra) + "›</span></summary><ul>" +
            no.filhos.map(function (f) { return renderizarDerivacao(f, nivel + 1); }).join("") +
            "</ul></details></li>";
    }

    function contarDerivacao(no) {
        if (no.terminal) {
            return { terminais: 1, naoTerminais: 0 };
        }
        return no.filhos.reduce(function (total, filho) {
            const c = contarDerivacao(filho);
            return { terminais: total.terminais + c.terminais, naoTerminais: total.naoTerminais + c.naoTerminais };
        }, { terminais: 0, naoTerminais: 1 });
    }

    // Converte (linha, coluna) em posição no texto, contando caracteres
    // como o scanner (code points).
    function prepararCodigo(codigo) {
        const caracteres = Array.from(codigo.replace(/\r\n?/g, "\n"));
        const inicios = [0];
        caracteres.forEach(function (c, i) {
            if (c === "\n") {
                inicios.push(i + 1);
            }
        });
        return {
            caracteres: caracteres,
            posicao: function (linha, coluna) {
                if (linha - 1 >= inicios.length) {
                    return caracteres.length;
                }
                return Math.min(inicios[linha - 1] + coluna - 1, caracteres.length);
            }
        };
    }

    // Código com um trecho destacado. `faixa` usa colunas inclusivas.
    function renderizarCodigoDestacado(preparado, faixa, classe) {
        const c = preparado.caracteres;
        if (!faixa) {
            return escaparHtml(c.join(""));
        }
        const inicio = preparado.posicao(faixa.linha, faixa.coluna);
        let fim = preparado.posicao(faixa.linha_fim || faixa.linha, faixa.coluna_fim || faixa.coluna) + 1;
        fim = Math.max(fim, inicio + 1);
        const trecho = c.slice(inicio, fim).join("");
        // Um erro no fim da linha aponta para a quebra de linha: mostra um
        // marcador visível sem apagar a quebra.
        const vazio = !trecho || trecho === "\n";
        return escaparHtml(c.slice(0, inicio).join("")) +
            "<mark class=\"" + (classe || "destaque") + "\">" +
            (vazio ? "␣" : escaparHtml(trecho)) + "</mark>" + (trecho === "\n" ? "\n" : "") +
            escaparHtml(c.slice(fim).join(""));
    }

    function faixaDoToken(token) {
        const partes = (token.lexema || " ").split("\n");
        if (partes.length === 1) {
            return { linha: token.linha, coluna: token.coluna, linha_fim: token.linha,
                coluna_fim: token.coluna + Math.max(partes[0].length, 1) - 1 };
        }
        return { linha: token.linha, coluna: token.coluna,
            linha_fim: token.linha + partes.length - 1, coluna_fim: Math.max(partes[partes.length - 1].length, 1) };
    }

    function dentro(no, token) {
        const antes = function (l1, c1, l2, c2) { return l1 < l2 || (l1 === l2 && c1 <= c2); };
        return antes(no.linha, no.coluna, token.linha, token.coluna) &&
            antes(token.linha, token.coluna, no.linha_fim, no.coluna_fim);
    }

    function tokensDoNo(no, tokens) {
        return tokens.filter(function (t) {
            return ["NOVA_LINHA", "INDENTA", "DEDENTA", "FIM"].indexOf(t.tipo) < 0 && dentro(no, t);
        });
    }

    // Converte os eventos do parser em passos exibíveis (consumir/criar),
    // guardando a pilha de regras ativa em cada passo.
    function montarPassosConstrucao(eventos) {
        const pilha = [];
        const passos = [];
        (eventos || []).forEach(function (e) {
            if (e.acao === "entrar") {
                pilha.push(e.regra);
            } else if (e.acao === "sair") {
                pilha.pop();
            } else {
                passos.push({ acao: e.acao, token: e.token, no: e.no, pilha: pilha.slice() });
            }
        });
        return passos;
    }

    // Nós já criados até o passo `indice` e as raízes da floresta resultante.
    function florestaNoPasso(passos, indice, nos) {
        const visiveis = new Set();
        for (let i = 0; i <= indice && i < passos.length; i++) {
            if (passos[i].acao === "criar") {
                visiveis.add(passos[i].no);
            }
        }
        const raizes = [];
        visiveis.forEach(function (id) {
            const pai = nos[id].pai;
            if (!pai || !visiveis.has(pai.id)) {
                raizes.push(nos[id].no);
            }
        });
        raizes.sort(function (a, b) { return a.linha - b.linha || a.coluna - b.coluna; });
        return { visiveis: visiveis, raizes: raizes };
    }

    function tiposPresentes(nos) {
        const contagem = {};
        Object.keys(nos).forEach(function (id) {
            const tipo = nos[id].no.tipo;
            contagem[tipo] = (contagem[tipo] || 0) + 1;
        });
        return contagem;
    }

    const api = {
        escaparHtml: escaparHtml,
        rotuloNo: rotuloNo,
        papelLegivel: papelLegivel,
        indexarNos: indexarNos,
        renderizarLista: renderizarLista,
        renderizarDiagrama: renderizarDiagrama,
        renderizarDerivacao: renderizarDerivacao,
        contarDerivacao: contarDerivacao,
        prepararCodigo: prepararCodigo,
        renderizarCodigoDestacado: renderizarCodigoDestacado,
        faixaDoToken: faixaDoToken,
        tokensDoNo: tokensDoNo,
        montarPassosConstrucao: montarPassosConstrucao,
        florestaNoPasso: florestaNoPasso,
        tiposPresentes: tiposPresentes
    };

    if (typeof module !== "undefined" && module.exports) {
        module.exports = api;
    }

    if (typeof document === "undefined") {
        return;
    }
      // -- Interface ----------------------------------------------------------

    const painel = document.getElementById("painel-sintatico");
    const status = document.getElementById("resultado-sintatico");
    const conteudo = document.getElementById("sintatico-conteudo");
    const codigoSintatico = document.getElementById("codigo-sintatico");
    const arvoreAst = document.getElementById("arvore-ast");
    const detalheNo = document.getElementById("detalhe-no");
    const filtro = document.getElementById("filtro-no");
    const areaErros = document.getElementById("erros-sintaticos");

    let estado = null; // { codigo, dados, preparado, nos, passos, passo, modo }
    let gramatica = null;
    let temporizador = null;

    function botaoIA(tipo, campo, valor, texto) {
        return "<button type=\"button\" class=\"botao-ia\" data-ia-tipo=\"" + tipo + "\" data-ia-" +
            campo + "=\"" + valor + "\">✨ " + escaparHtml(texto) + "</button>";
    }

    function etiquetaToken(t) {
        return "<span class=\"par\" style=\"--cor: var(--cor-" + t.tipo + ")\">&lt;" +
            escaparHtml(t.tipo) + ", " + escaparHtml(t.lexema) + "&gt;</span>";
    }

    // Abas
    const botoesAba = document.querySelectorAll(".abas-sintaticas button");

    function abrirAba(nome) {
        botoesAba.forEach(function (b) {
            const ativa = b.dataset.aba === nome;
            b.setAttribute("aria-selected", ativa ? "true" : "false");
            document.getElementById("aba-" + b.dataset.aba).hidden = !ativa;
        });
        if (nome !== "construcao") {
            pausar();
        }
    }

    botoesAba.forEach(function (b) {
        b.addEventListener("click", function () { abrirAba(b.dataset.aba); });
    });

    // Gramática (carregada do backend)
    async function carregarGramatica() {
        const destino = document.getElementById("lista-gramatica");
        try {
            const resposta = await fetch("/api/gramatica");
            gramatica = await resposta.json();
            destino.innerHTML = gramatica.regras.map(function (r) {
                return "<li id=\"regra-" + escaparHtml(r.nome) + "\"><code>" +
                    escaparHtml(r.producao) + "</code></li>";
            }).join("");
        } catch (erro) {
            destino.textContent = "Não foi possível carregar a gramática do servidor.";
        }
    }

    function producao(regra) {
        if (!gramatica) {
            return "";
        }
        const achada = gramatica.regras.find(function (r) { return r.nome === regra; });
        return achada ? achada.producao : "";
    }

    function destacarRegra(regra) {
        document.querySelectorAll("#lista-gramatica li").forEach(function (li) {
            li.classList.toggle("regra-ativa", li.id === "regra-" + regra);
        });
    }

    // Seleção de nó: destaca o trecho no código e mostra os detalhes.
    function selecionarNo(id) {
        const item = estado && estado.nos[id];
        if (!item) {
            return;
        }
        const no = item.no;
        document.querySelectorAll("#arvore-ast .no-ast.selecionado").forEach(function (b) {
            b.classList.remove("selecionado");
        });
        document.querySelectorAll("#arvore-ast .no-ast[data-id=\"" + id + "\"]").forEach(function (b) {
            b.classList.add("selecionado");
        });
        codigoSintatico.innerHTML = renderizarCodigoDestacado(estado.preparado, no);
        const marca = codigoSintatico.querySelector("mark");
        if (marca) {
            marca.scrollIntoView({ block: "nearest", inline: "nearest" });
        }
        destacarRegra(no.regra);

        const atributos = Object.keys(no.atributos).filter(function (k) {
            return k !== "entre_parenteses";
        }).map(function (k) {
            const v = no.atributos[k];
            return "<li><strong>" + escaparHtml(k) + "</strong>: <code>" +
                escaparHtml(Array.isArray(v) ? "[" + v.join(", ") + "]" : String(v)) + "</code></li>";
        }).join("");
        const tokens = tokensDoNo(no, estado.dados.tokens);
        const pai = item.pai;

        detalheNo.innerHTML =
            "<p><span class=\"forma cat-" + no.categoria + "\" aria-hidden=\"true\">" + FORMAS[no.categoria] +
            "</span> <strong>" + escaparHtml(rotuloNo(no)) + "</strong> <code>" + escaparHtml(no.tipo) +
            "</code> — " + escaparHtml(NOMES_CATEGORIA[no.categoria]) + "</p>" +
            "<p>Posição: linha " + no.linha + ", coluna " + no.coluna + " até linha " + no.linha_fim +
            ", coluna " + no.coluna_fim + ".</p>" +
            (pai ? "<p>Nó pai: <button type=\"button\" class=\"link\" data-ir-no=\"" + pai.id + "\">" +
                escaparHtml(rotuloNo(pai)) + "</button>" +
                (no.papel ? " — papel neste pai: <strong>" + escaparHtml(papelLegivel(no.papel)) + "</strong>" : "") +
                "</p>" : "<p>Este é o nó raiz da árvore.</p>") +
            (atributos ? "<p>Atributos:</p><ul>" + atributos + "</ul>" : "") +
            "<p>Filhos: " + no.filhos.length + ".</p>" +
            "<p>Regra da gramática que reconheceu este nó: <strong>" + escaparHtml(no.regra) + "</strong></p>" +
            "<pre class=\"producao\">" + escaparHtml(producao(no.regra)) + "</pre>" +
            "<p>Tokens que formam este nó:</p><div class=\"sequencia-tokens\">" +
            (tokens.map(etiquetaToken).join(" ") || "<em>nenhum</em>") + "</div>" +
            botaoIA("no", "id", no.id, "Explicar este nó com IA");
    }

    arvoreAst.addEventListener("click", function (evento) {
        const botao = evento.target.closest(".no-ast");
        if (botao) {
            evento.preventDefault(); // não recolhe o <details> ao selecionar
            selecionarNo(Number(botao.dataset.id));
        }
    });

    detalheNo.addEventListener("click", function (evento) {
        const link = evento.target.closest("[data-ir-no]");
        if (link) {
            selecionarNo(Number(link.dataset.irNo));
        }
    });

    // Visualizações da AST
    function desenharAst() {
        const raiz = estado.dados.sintatico.ast;
        arvoreAst.className = "arvore " + (estado.modo === "diagrama" ? "diagrama" : "lista");
        arvoreAst.innerHTML = estado.modo === "diagrama"
            ? renderizarDiagrama([raiz])
            : "<ul>" + renderizarLista(raiz) + "</ul>";
        document.getElementById("modo-diagrama").setAttribute("aria-pressed", estado.modo === "diagrama");
        document.getElementById("modo-lista").setAttribute("aria-pressed", estado.modo === "lista");
        document.getElementById("expandir-ast").disabled = estado.modo !== "lista";
        document.getElementById("recolher-ast").disabled = estado.modo !== "lista";
        if (estado.modo === "diagrama") {
            // Centraliza a raiz quando o diagrama é mais largo que a tela.
            arvoreAst.scrollLeft = (arvoreAst.scrollWidth - arvoreAst.clientWidth) / 2;
        }
        aplicarFiltro();
    }

    function aplicarFiltro() {
        const tipo = filtro.value;
        let total = 0;
        arvoreAst.querySelectorAll(".no-ast").forEach(function (b) {
            const corresponde = tipo && estado.nos[b.dataset.id].no.tipo === tipo;
            b.classList.toggle("filtrado", Boolean(corresponde));
            b.classList.toggle("apagado", Boolean(tipo) && !corresponde);
            if (corresponde) {
                total++;
            }
        });
        document.getElementById("contagem-filtro").textContent = tipo
            ? total + " nó(s) do tipo " + tipo + " destacado(s)." : "";
    }

    filtro.addEventListener("change", aplicarFiltro);

    document.getElementById("modo-diagrama").addEventListener("click", function () {
        estado.modo = "diagrama";
        desenharAst();
    });
    document.getElementById("modo-lista").addEventListener("click", function () {
        estado.modo = "lista";
        desenharAst();
    });

    function alternarTudo(seletor, aberto) {
        document.querySelectorAll(seletor + " details").forEach(function (d) { d.open = aberto; });
    }

    document.getElementById("expandir-ast").addEventListener("click", function () { alternarTudo("#arvore-ast", true); });
    document.getElementById("recolher-ast").addEventListener("click", function () { alternarTudo("#arvore-ast", false); });
    document.getElementById("expandir-derivacao").addEventListener("click", function () { alternarTudo("#arvore-derivacao", true); });
    document.getElementById("recolher-derivacao").addEventListener("click", function () { alternarTudo("#arvore-derivacao", false); });

    // Exportação da AST
    document.getElementById("baixar-json").addEventListener("click", function () {
        const blob = new Blob([JSON.stringify(estado.dados.sintatico.ast, null, 2)], { type: "application/json" });
        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.download = "ast.json";
        document.body.appendChild(link);
        link.click();
        link.remove();
        setTimeout(function () { URL.revokeObjectURL(link.href); }, 1000);
    });

    document.getElementById("copiar-json").addEventListener("click", async function () {
        const aviso = document.getElementById("aviso-json");
        try {
            await navigator.clipboard.writeText(JSON.stringify(estado.dados.sintatico.ast, null, 2));
            aviso.textContent = "JSON copiado para a área de transferência.";
        } catch (erro) {
            aviso.textContent = "Não foi possível copiar automaticamente; selecione o texto abaixo.";
        }
    });

    // Construção passo a passo
    const construcaoCodigo = document.getElementById("construcao-codigo");
    const construcaoArvore = document.getElementById("construcao-arvore");
    const construcaoPilha = document.getElementById("construcao-pilha");
    const construcaoExplicacao = document.getElementById("construcao-explicacao");
    const construcaoContador = document.getElementById("construcao-contador");
    const botaoPlay = document.getElementById("construcao-play");
    const soNos = document.getElementById("construcao-so-nos");

    function irParaPasso(n) {
        const passos = estado.passos;
        estado.passo = Math.max(-1, Math.min(n, passos.length - 1));
        const atual = passos[estado.passo];
        const floresta = florestaNoPasso(passos, estado.passo, estado.nos);

        construcaoArvore.innerHTML = floresta.raizes.length
            ? renderizarDiagrama(floresta.raizes, { visiveis: floresta.visiveis, atual: atual && atual.acao === "criar" ? atual.no : null })
            : "<p class=\"ajuda\">Nenhum nó criado ainda.</p>";
        construcaoContador.textContent = "Passo " + (estado.passo + 1) + " de " + passos.length +
            " — " + floresta.visiveis.size + " de " + Object.keys(estado.nos).length + " nó(s) criados";

        if (!atual) {
            construcaoCodigo.innerHTML = renderizarCodigoDestacado(estado.preparado, null);
            construcaoPilha.innerHTML = "";
            construcaoExplicacao.textContent =
                "Clique em ▶ para ver o parser ler os tokens e montar a árvore. As subárvores aparecem " +
                "de baixo para cima: primeiro as folhas, depois os nós que as ligam.";
        } else {
            construcaoPilha.innerHTML = atual.pilha.map(function (r) {
                return "<span class=\"regra-pilha\">" + escaparHtml(r) + "</span>";
            }).join("<span aria-hidden=\"true\"> › </span>");
            const regraAtual = atual.pilha[atual.pilha.length - 1];
            if (atual.acao === "consumir") {
                const token = estado.dados.tokens[atual.token];
                construcaoCodigo.innerHTML = renderizarCodigoDestacado(estado.preparado, faixaDoToken(token), "destaque-token");
                construcaoExplicacao.innerHTML = "Na regra <strong>‹" + escaparHtml(regraAtual) +
                    "›</strong>, o parser consumiu o token " + etiquetaToken(token) +
                    " (linha " + token.linha + ", coluna " + token.coluna + ").";
            } else {
                const no = estado.nos[atual.no].no;
                construcaoCodigo.innerHTML = renderizarCodigoDestacado(estado.preparado, no);
                const filhos = no.filhos.map(function (f) { return rotuloNo(f); });
                construcaoExplicacao.innerHTML = "Na regra <strong>‹" + escaparHtml(no.regra) +
                    "›</strong>, o parser criou o nó <strong>" + escaparHtml(no.tipo) + "</strong> (" +
                    escaparHtml(rotuloNo(no)) + ")" + (filhos.length
                    ? ", ligando como filhos os nós já construídos: " + escaparHtml(filhos.join("; ")) + "."
                    : ", uma folha da árvore.");
            }
        }
        const marca = construcaoCodigo.querySelector("mark");
        if (marca) {
            marca.scrollIntoView({ block: "nearest", inline: "nearest" });
        }
        document.getElementById("construcao-anterior").disabled = estado.passo < 0;
        document.getElementById("construcao-inicio").disabled = estado.passo < 0;
        document.getElementById("construcao-proximo").disabled = estado.passo >= passos.length - 1;
        document.getElementById("construcao-fim").disabled = estado.passo >= passos.length - 1;
    }

    function proximoIndice(direcao) {
        let i = estado.passo + direcao;
        if (soNos.checked) {
            while (i >= 0 && i < estado.passos.length && estado.passos[i].acao !== "criar") {
                i += direcao;
            }
        }
        return i;
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
        if (estado.passo >= estado.passos.length - 1) {
            irParaPasso(-1);
        }
        botaoPlay.textContent = "⏸ Pausar";
        botaoPlay.setAttribute("aria-label", "Pausar");
        (function proximo() {
            const i = proximoIndice(1);
            irParaPasso(Math.min(i, estado.passos.length - 1));
            if (estado.passo >= estado.passos.length - 1 || i >= estado.passos.length) {
                pausar();
                return;
            }
            const velocidade = Number(document.getElementById("construcao-velocidade").value);
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
    document.getElementById("construcao-proximo").addEventListener("click", function () {
        pausar();
        irParaPasso(Math.min(proximoIndice(1), estado.passos.length - 1));
    });
    document.getElementById("construcao-anterior").addEventListener("click", function () {
        pausar();
        irParaPasso(Math.max(proximoIndice(-1), -1));
    });
    document.getElementById("construcao-inicio").addEventListener("click", function () {
        pausar();
        irParaPasso(-1);
    });
    document.getElementById("construcao-fim").addEventListener("click", function () {
        pausar();
        irParaPasso(estado.passos.length - 1);
    });

    // Erros sintáticos
    function mostrarErros(erros) {
        if (!erros.length) {
            areaErros.innerHTML = "<p class=\"sem-erros\">Nenhum erro sintático encontrado.</p>";
            return;
        }
        areaErros.innerHTML = erros.map(function (e, i) {
            return "<div class=\"erro erro-sintatico\" tabindex=\"0\" data-indice=\"" + i + "\">" +
                "<span class=\"etiqueta-erro sintatico\">ERRO SINTÁTICO</span> <strong>" +
                escaparHtml(e.mensagem) + "</strong>" +
                "<div class=\"dica\">Encontrado: " + escaparHtml(e.encontrado_descricao) +
                " · Esperado: " + escaparHtml(e.esperado.join(" ou ")) + "</div>" +
                (e.dica ? "<div class=\"dica\">" + escaparHtml(e.dica) + "</div>" : "") +
                "<div class=\"dica\">Regra da gramática: <code>" + escaparHtml(e.producao) + "</code></div>" +
                botaoIA("erro_sintatico", "indice", i, "Entender erro com IA") + "</div>";
        }).join("");
    }

    function destacarErro(evento) {
        if (evento.target.closest(".botao-ia")) {
            return;
        }
        const alvo = evento.target.closest(".erro-sintatico");
        if (!alvo) {
            return;
        }
        const erro = estado.dados.sintatico.erros[Number(alvo.dataset.indice)];
        // Destaca o token encontrado inteiro (ou um marcador no fim da linha).
        const estrutural = ["NOVA_LINHA", "FIM", "INDENTA", "DEDENTA"].indexOf(erro.encontrado) >= 0;
        codigoSintatico.innerHTML = renderizarCodigoDestacado(estado.preparado, estrutural
            ? { linha: erro.linha, coluna: erro.coluna }
            : faixaDoToken({ linha: erro.linha, coluna: erro.coluna, lexema: erro.encontrado }),
        "destaque-erro");
        destacarRegra(erro.regra);
        codigoSintatico.scrollIntoView({ block: "nearest" });
    }

    areaErros.addEventListener("click", destacarErro);
    areaErros.addEventListener("keydown", function (evento) {
        if (evento.key === "Enter") {
            destacarErro(evento);
        }
    });

    // Fluxo principal
    function mostrar(codigo, dados) {
        pausar();
        const sintatico = dados.sintatico;
        painel.hidden = false;
        status.textContent = sintatico ? sintatico.mensagem : "";
        status.className = sintatico && sintatico.sucesso ? "sucesso" : "falha";
        estado = { codigo: codigo, dados: dados, preparado: prepararCodigo(codigo), nos: {}, passos: [], passo: -1 };

        if (!sintatico || !sintatico.executado) {
            conteudo.hidden = true;
            areaErros.innerHTML = "<p class=\"aviso-nao-executado\">A análise sintática depende de uma sequência " +
                "de tokens válida. Corrija os erros léxicos indicados acima e analise de novo.</p>";
            return;
        }
        conteudo.hidden = false;
        codigoSintatico.innerHTML = renderizarCodigoDestacado(estado.preparado, null);
        detalheNo.innerHTML = "Selecione um nó da árvore para ver seus detalhes e o trecho correspondente no código.";
        mostrarErros(sintatico.erros);
        destacarRegra(null);

        const temAst = Boolean(sintatico.ast);
        document.querySelectorAll(".somente-ast").forEach(function (el) { el.hidden = !temAst; });
        if (!temAst) {
            abrirAba("gramatica");
            return;
        }

        estado.nos = indexarNos(sintatico.ast);
        estado.modo = (sintatico.resumo.total_nos <= 30 && window.innerWidth > 640) ? "diagrama" : "lista";
        const presentes = tiposPresentes(estado.nos);
        filtro.innerHTML = "<option value=\"\">Nenhum</option>" + Object.keys(presentes).sort().map(function (t) {
            return "<option value=\"" + t + "\">" + t + " (" + presentes[t] + ")</option>";
        }).join("");
        desenharAst();

        document.getElementById("json-ast").textContent = JSON.stringify(sintatico.ast, null, 2);
        document.getElementById("aviso-json").textContent = "";

        const temDetalhes = Boolean(sintatico.passos && sintatico.derivacao);
        document.querySelectorAll(".somente-detalhes").forEach(function (el) { el.hidden = !temDetalhes; });
        document.getElementById("aviso-detalhes").hidden = temDetalhes;
        if (temDetalhes) {
            estado.passos = montarPassosConstrucao(sintatico.passos);
            irParaPasso(-1);
            const contagem = contarDerivacao(sintatico.derivacao);
            document.getElementById("comparacao-arvores").innerHTML =
                "A árvore de derivação deste código tem <strong>" + (contagem.terminais + contagem.naoTerminais) +
                "</strong> nós (" + contagem.naoTerminais + " não terminais e " + contagem.terminais +
                " terminais); a AST tem apenas <strong>" + sintatico.resumo.total_nos + "</strong>.";
            document.getElementById("arvore-derivacao").innerHTML =
                "<ul>" + renderizarDerivacao(sintatico.derivacao) + "</ul>";
        }
        abrirAba("ast");
    }

    function esconder() {
        pausar();
        estado = null;
        painel.hidden = true;
    }

    document.addEventListener("analise-concluida", function (evento) {
        mostrar(evento.detail.codigo, evento.detail.dados);
    });
    document.addEventListener("analise-limpa", esconder);

    carregarGramatica();
})();
