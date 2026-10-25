const fs = require("node:fs");
const assert = require("node:assert/strict");
const test = require("node:test");

const html = fs.readFileSync(
    "index.html",
    "utf8"
);

const js = fs.readFileSync(
    "app.js",
    "utf8"
);

const app = require("./app.js");

// -- Regressão da Etapa 2 ---------------------------------------------------

test("exibe identificação do software", () => {
    assert.match(html, /Software Educacional/);
    assert.match(html, /Python/);
});

test("possui campo para código", () => {
    assert.match(html, /id="codigo"/);
});

test("possui botão de análise", () => {
    assert.match(html, /id="analisar"/);
});

test("possui área de resultados", () => {
    assert.match(html, /id="resultado"/);
});

test("possui seleção de exemplos", () => {
    assert.match(html, /id="exemplos"/);
});

test("possui três exemplos de Python", () => {
    assert.match(js, /variavel:/);
    assert.match(js, /soma:/);
    assert.match(js, /multiplicacao:/);
});

test("envia código ao backend", () => {
    assert.match(js, /fetch\("\/api\/analisar"/);
});

test("verifica entradas vazias", () => {
    assert.match(js, /codigo\.trim\(\)/);
});

// -- Estrutura da Etapa 3 ----------------------------------------------------

test("carrega o script e a folha de estilos", () => {
    assert.match(html, /<script src="app.js"><\/script>/);
    assert.match(html, /<link rel="stylesheet" href="style.css">/);
});

test("possui tabela de tokens com as colunas pedidas", () => {
    assert.match(html, /id="tabela-tokens"/);
    for (const coluna of ["Tipo", "Lexema", "Linha", "Coluna"]) {
        assert.match(html, new RegExp("<th>" + coluna + "</th>"));
    }
});

test("possui seções de erros, destaque, passo a passo e resumo", () => {
    assert.match(html, /id="erros"/);
    assert.match(html, /id="codigo-destacado"/);
    assert.match(html, /id="passo-codigo"/);
    assert.match(html, /id="resumo"/);
    assert.match(html, /id="comparacao"/);
});

test("explica token e lexema", () => {
    assert.match(html, /O que é um token\?/);
    assert.match(html, /Lexema/);
});

test("é adaptada a celulares", () => {
    assert.match(html, /name="viewport"/);
    assert.match(fs.readFileSync("style.css", "utf8"), /@media \(max-width: 640px\)/);
});

test("todos os exemplos do seletor existem no script", () => {
    const valores = [...html.matchAll(/<option value="(\w+)">/g)].map((m) => m[1]);
    assert.ok(valores.length >= 9);
    for (const valor of valores) {
        assert.ok(app.exemplos[valor], "exemplo ausente: " + valor);
    }
});

// -- Funções puras ----------------------------------------------------------

test("escaparHtml impede injeção de HTML", () => {
    assert.equal(
        app.escaparHtml("<img src=x onerror=\"alert('x')\">&"),
        "&lt;img src=x onerror=&quot;alert(&#39;x&#39;)&quot;&gt;&amp;"
    );
});

test("lexemaVisivel mostra caracteres invisíveis", () => {
    assert.equal(app.lexemaVisivel("NOVA_LINHA", "\n"), "\\n");
    assert.equal(app.lexemaVisivel("INDENTA", "    "), "····");
    assert.equal(app.lexemaVisivel("DEDENTA", ""), "(vazio)");
    assert.equal(app.lexemaVisivel("IDENTIFICADOR", "x"), "x");
});

const respostaExemplo = {
    tokens: [
        { tipo: "IDENTIFICADOR", lexema: "x", linha: 1, coluna: 1 },
        { tipo: "OPERADOR", lexema: "=", linha: 1, coluna: 3 },
        { tipo: "LITERAL_STRING", lexema: "\"<b>é</b>\"", linha: 1, coluna: 5 },
        { tipo: "NOVA_LINHA", lexema: "\n", linha: 1, coluna: 15 },
        { tipo: "IDENTIFICADOR", lexema: "y", linha: 2, coluna: 1 },
        { tipo: "NOVA_LINHA", lexema: "", linha: 2, coluna: 6 },
        { tipo: "FIM", lexema: "", linha: 2, coluna: 6 }
    ],
    erros: [
        { tipo: "ERRO_LEXICO", lexema: "@", linha: 2, coluna: 3, mensagem: "m", dica: "d" }
    ],
    comentarios: []
};
const codigoExemplo = "x = \"<b>é</b>\"\ny @ 1";

test("calcularSegmentos converte linha/coluna em posições", () => {
    const { caracteres, segmentos } = app.calcularSegmentos(codigoExemplo, respostaExemplo);
    const textos = segmentos
        .filter((s) => s.fim > s.inicio)
        .map((s) => [s.classe, caracteres.slice(s.inicio, s.fim).join("")]);
    assert.deepEqual(textos, [
        ["IDENTIFICADOR", "x"],
        ["OPERADOR", "="],
        ["LITERAL_STRING", "\"<b>é</b>\""],
        ["NOVA_LINHA", "\n"],
        ["IDENTIFICADOR", "y"],
        ["ERRO", "@"]
    ]);
});

test("erro tem prioridade sobre token na mesma posição", () => {
    const dados = {
        tokens: [{ tipo: "DELIMITADOR", lexema: "(", linha: 1, coluna: 2 }],
        erros: [{ lexema: "(", linha: 1, coluna: 2, mensagem: "m" }],
        comentarios: []
    };
    const { segmentos } = app.calcularSegmentos("f(", dados);
    assert.deepEqual(segmentos.map((s) => s.classe), ["ERRO"]);
});

test("renderizarCodigo escapa o código e preserva o texto", () => {
    const { caracteres, segmentos } = app.calcularSegmentos(codigoExemplo, respostaExemplo);
    const saida = app.renderizarCodigo(caracteres, segmentos);
    assert.doesNotMatch(saida, /<b>/);
    assert.match(saida, /&lt;b&gt;é&lt;\/b&gt;/);
    assert.match(saida, /class="tk tk-ERRO"/);
    const semTags = saida.replace(/<[^>]+>/g, "").replace(/↵/g, "");
    assert.equal(
        semTags.replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, "\"").replace(/&amp;/g, "&"),
        codigoExemplo
    );
});

test("renderizarCodigo marca passos pendentes e atual", () => {
    const { caracteres, segmentos } = app.calcularSegmentos(codigoExemplo, respostaExemplo);
    const saida = app.renderizarCodigo(caracteres, segmentos, {
        estado: (s) => (s.origem === "token" && s.indice === 1 ? "atual" : "pendente")
    });
    assert.match(saida, /tk-OPERADOR atual/);
    assert.match(saida, /tk-IDENTIFICADOR pendente/);
});

test("montarPassos intercala erros na ordem de leitura", () => {
    const passos = app.montarPassos(respostaExemplo.tokens, respostaExemplo.erros);
    assert.equal(passos.length, 8);
    assert.deepEqual(passos[5], { origem: "erro", indice: 0 });
    assert.deepEqual(passos[4], { origem: "token", indice: 4 });
});

test("contarPorTipo agrupa tokens por categoria", () => {
    assert.deepEqual(app.contarPorTipo(respostaExemplo.tokens), {
        IDENTIFICADOR: 2, OPERADOR: 1, LITERAL_STRING: 1, NOVA_LINHA: 2, FIM: 1
    });
});
