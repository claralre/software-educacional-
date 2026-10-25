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
