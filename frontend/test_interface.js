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

// -- Etapa 4: análise sintática ------------------------------------------------

const arvore = require("./arvore.js");
const ia = require("./ia.js");

test("página carrega os scripts da análise sintática e da IA", () => {
    assert.match(html, /<script src="arvore.js"><\/script>/);
    assert.match(html, /<script src="ia.js"><\/script>/);
    const dockerfile = fs.readFileSync("Dockerfile", "utf8");
    for (const arquivo of ["index.html", "style.css", "app.js", "arvore.js", "ia.js"]) {
        assert.match(dockerfile, new RegExp(arquivo.replace(".", "\\.")));
    }
});

test("possui as seções da análise sintática", () => {
    for (const id of ["painel-sintatico", "resultado-sintatico", "arvore-ast", "detalhe-no",
        "erros-sintaticos", "construcao-arvore", "arvore-derivacao", "lista-gramatica",
        "json-ast", "baixar-json", "expandir-ast", "recolher-ast", "filtro-no"]) {
        assert.match(html, new RegExp(`id="${id}"`), id);
    }
});

test("explica análise sintática, AST e árvore de derivação", () => {
    assert.match(html, /O que é análise sintática\? E a AST\?/);
    assert.match(html, /árvore de derivação/i);
});

test("possui professor virtual e diálogo da IA", () => {
    assert.match(html, /id="professor-virtual"/);
    assert.match(html, /id="dialogo-ia"/);
    assert.match(fs.readFileSync("ia.js", "utf8"), /fetch\("\/api\/ia\/explicar"/);
});

test("nginx espera tempo suficiente pelas respostas da IA", () => {
    assert.match(fs.readFileSync("nginx.conf", "utf8"), /proxy_read_timeout 180s;/);
});

// AST de "resultado = 10 + 5 * 2", no formato devolvido pelo backend.
function no(id, tipo, categoria, regra, atributos, posicao, filhos, papel) {
    return {
        id, tipo, rotulo: { ADICAO: "Adição", MULTIPLICACAO: "Multiplicação",
            NUMERO_INTEIRO: "Número inteiro", IDENTIFICADOR: "Identificador",
            ATRIBUICAO: "Atribuição", PROGRAMA: "Programa" }[tipo],
        categoria, regra, papel: papel || null, atributos,
        linha: 1, coluna: posicao[0], linha_fim: 1, coluna_fim: posicao[1], filhos
    };
}
const astExemplo = no(7, "PROGRAMA", "estrutura", "programa", {}, [1, 22], [
    no(6, "ATRIBUICAO", "comando", "atribuicao_ou_expressao", { operador: "=" }, [1, 22], [
        no(0, "IDENTIFICADOR", "literal", "atomo", { nome: "resultado" }, [1, 9], [], "alvo"),
        no(5, "ADICAO", "expressao", "soma", { operador: "+" }, [13, 22], [
            no(1, "NUMERO_INTEIRO", "literal", "atomo", { valor: "10" }, [13, 14], [], "esquerda"),
            no(4, "MULTIPLICACAO", "expressao", "termo", { operador: "*" }, [18, 22], [
                no(2, "NUMERO_INTEIRO", "literal", "atomo", { valor: "5" }, [18, 18], [], "esquerda"),
                no(3, "NUMERO_INTEIRO", "literal", "atomo", { valor: "2" }, [22, 22], [], "direita")
            ], "direita")
        ], "valor")
    ], "comando")
]);
const codigoAst = "resultado = 10 + 5 * 2";

test("rotuloNo mostra tipo e valor de cada nó", () => {
    const nos = arvore.indexarNos(astExemplo);
    assert.equal(arvore.rotuloNo(nos[0].no), "Identificador: resultado");
    assert.equal(arvore.rotuloNo(nos[1].no), "Número inteiro: 10");
    assert.equal(arvore.rotuloNo(nos[5].no), "Adição (+)");
    assert.equal(arvore.rotuloNo({ tipo: "FUNCAO", atributos: { nome: "f", parametros: ["a", "b"] } }),
        "Função f(a, b)");
});

test("indexarNos guarda o pai de cada nó", () => {
    const nos = arvore.indexarNos(astExemplo);
    assert.equal(Object.keys(nos).length, 8);
    assert.equal(nos[4].pai.tipo, "ADICAO");
    assert.equal(nos[7].pai, null);
});

test("lista e diagrama mostram todos os nós com papel e forma", () => {
    const lista = arvore.renderizarLista(astExemplo);
    const diagrama = arvore.renderizarDiagrama([astExemplo]);
    for (const saida of [lista, diagrama]) {
        assert.equal((saida.match(/class="no-ast/g) || []).length, 8);
        assert.match(saida, /data-id="4"/);
        assert.match(saida, /<span class="papel">direita<\/span>/);
        assert.match(saida, /class="forma" aria-hidden="true">●/);
    }
    // Só nós com filhos podem ser recolhidos na lista.
    assert.equal((lista.match(/<details open>/g) || []).length, 4);
});

test("renderização da árvore escapa HTML", () => {
    const perigoso = no(0, "IDENTIFICADOR", "literal", "atomo", { nome: "<img src=x onerror=alert(1)>" }, [1, 1], []);
    const saida = arvore.renderizarDiagrama([perigoso]) + arvore.renderizarLista(perigoso);
    assert.doesNotMatch(saida, /<img/);
    assert.match(saida, /&lt;img/);
});

test("código destacado marca exatamente o trecho do nó", () => {
    const preparado = arvore.prepararCodigo(codigoAst);
    const nos = arvore.indexarNos(astExemplo);
    assert.equal(
        arvore.renderizarCodigoDestacado(preparado, nos[4].no),
        "resultado = 10 + <mark class=\"destaque\">5 * 2</mark>"
    );
    assert.equal(arvore.renderizarCodigoDestacado(preparado, null), codigoAst);
});

test("erro no fim da linha não apaga a quebra de linha", () => {
    const preparado = arvore.prepararCodigo("x = 1 +\ny = 2");
    const saida = arvore.renderizarCodigoDestacado(preparado, { linha: 1, coluna: 8 }, "destaque-erro");
    assert.equal(saida, "x = 1 +<mark class=\"destaque-erro\">␣</mark>\ny = 2");
});

test("tokensDoNo devolve os tokens cobertos pelo nó", () => {
    const tokens = [
        { tipo: "IDENTIFICADOR", lexema: "resultado", linha: 1, coluna: 1 },
        { tipo: "OPERADOR", lexema: "=", linha: 1, coluna: 11 },
        { tipo: "LITERAL_INTEIRO", lexema: "10", linha: 1, coluna: 13 },
        { tipo: "OPERADOR", lexema: "+", linha: 1, coluna: 16 },
        { tipo: "LITERAL_INTEIRO", lexema: "5", linha: 1, coluna: 18 },
        { tipo: "OPERADOR", lexema: "*", linha: 1, coluna: 20 },
        { tipo: "LITERAL_INTEIRO", lexema: "2", linha: 1, coluna: 22 },
        { tipo: "NOVA_LINHA", lexema: "", linha: 1, coluna: 23 }
    ];
    const nos = arvore.indexarNos(astExemplo);
    assert.deepEqual(arvore.tokensDoNo(nos[4].no, tokens).map((t) => t.lexema), ["5", "*", "2"]);
    assert.equal(arvore.tokensDoNo(nos[7].no, tokens).length, 7);
});

test("passos da construção guardam a pilha de regras", () => {
    const eventos = [
        { acao: "entrar", regra: "programa" },
        { acao: "entrar", regra: "atomo" },
        { acao: "consumir", token: 0 },
        { acao: "criar", no: 0 },
        { acao: "sair", regra: "atomo" },
        { acao: "consumir", token: 1 },
        { acao: "sair", regra: "programa" }
    ];
    const passos = arvore.montarPassosConstrucao(eventos);
    assert.equal(passos.length, 3);
    assert.deepEqual(passos[0], { acao: "consumir", token: 0, no: undefined, pilha: ["programa", "atomo"] });
    assert.deepEqual(passos[2].pilha, ["programa"]);
});

test("floresta da construção cresce de baixo para cima", () => {
    const nos = arvore.indexarNos(astExemplo);
    const passos = [0, 1, 2, 3, 4, 5, 6, 7].map((id) => ({ acao: "criar", no: id, pilha: [] }));
    // Depois de criar 0..4: 'resultado', '10' e a multiplicação são raízes.
    let floresta = arvore.florestaNoPasso(passos, 4, nos);
    assert.deepEqual(floresta.raizes.map((n) => n.id), [0, 1, 4]);
    assert.equal(floresta.visiveis.size, 5);
    floresta = arvore.florestaNoPasso(passos, 7, nos);
    assert.deepEqual(floresta.raizes.map((n) => n.id), [7]);
    const desenho = arvore.renderizarDiagrama(floresta.raizes, { visiveis: floresta.visiveis, atual: 7 });
    assert.match(desenho, /no-ast cat-estrutura novo/);
});

test("árvore de derivação mostra terminais e não terminais", () => {
    const derivacao = { regra: "programa", filhos: [
        { regra: "atomo", filhos: [{ terminal: "IDENTIFICADOR", lexema: "x", token: 0 }] },
        { terminal: "FIM", lexema: "", token: 1 }
    ] };
    const saida = arvore.renderizarDerivacao(derivacao);
    assert.match(saida, /‹programa›/);
    assert.match(saida, /‹atomo›/);
    assert.match(saida, /IDENTIFICADOR <code>x<\/code>/);
    assert.deepEqual(arvore.contarDerivacao(derivacao), { terminais: 2, naoTerminais: 2 });
});

test("tiposPresentes conta os nós por tipo", () => {
    assert.deepEqual(arvore.tiposPresentes(arvore.indexarNos(astExemplo)), {
        PROGRAMA: 1, ATRIBUICAO: 1, IDENTIFICADOR: 1, ADICAO: 1, MULTIPLICACAO: 1, NUMERO_INTEIRO: 3
    });
});

test("resposta da IA é exibida sem executar HTML", () => {
    assert.equal(
        ia.formatarResposta("**Nó** `ADICAO` <script>alert(1)</script>"),
        "<strong>Nó</strong> <code>ADICAO</code> &lt;script&gt;alert(1)&lt;/script&gt;"
    );
});

test("pedido à IA envia o alvo e o código analisado", () => {
    assert.deepEqual(ia.montarPedido({ tipo: "no", id: 4 }, "x = 1"),
        { codigo: "x = 1", alvo: { tipo: "no", id: 4 } });
    assert.deepEqual(ia.montarPedido({ tipo: "conceito" }, "", "O que é AST?"),
        { codigo: "", alvo: { tipo: "conceito" }, pergunta: "O que é AST?" });
});

// -- Etapa 5: análise semântica ----------------------------------------------

const semantica = require("./semantica.js");

// Saída real do backend para:  x = 1 / def f(a): / return a + x / print(f(x))
const codigoSem = "x = 1\ndef f(a):\n    return a + x\nprint(f(x))";
const tabelaSem = [
    { nome: "x", categoria: "variavel", tipo: "int", tipos: ["int"], escopo: "global", escopo_rotulo: "Escopo global",
        linha: 1, coluna: 1, linha_fim: 1, coluna_fim: 1, no_id: 0,
        usos: [{ linha: 3, coluna: 16, linha_fim: 3, coluna_fim: 16 }, { linha: 4, coluna: 9, linha_fim: 4, coluna_fim: 9 }] },
    { nome: "f", categoria: "funcao", tipo: "função", tipos: ["função"], escopo: "global", escopo_rotulo: "Escopo global",
        linha: 2, coluna: 5, linha_fim: 2, coluna_fim: 5, no_id: 9,
        usos: [{ linha: 4, coluna: 7, linha_fim: 4, coluna_fim: 7 }], parametros: ["a"], retorno: "desconhecido" },
    { nome: "a", categoria: "parametro", tipo: "desconhecido", tipos: [], escopo: "f", escopo_rotulo: "Função f",
        linha: 2, coluna: 7, linha_fim: 2, coluna_fim: 7, no_id: 3,
        usos: [{ linha: 3, coluna: 12, linha_fim: 3, coluna_fim: 12 }] },
    { nome: "print", categoria: "embutida", tipo: "função", tipos: ["função"], escopo: "embutido",
        escopo_rotulo: "Funções embutidas do Python", linha: null, coluna: null, linha_fim: null, coluna_fim: null,
        no_id: null, usos: [{ linha: 4, coluna: 1, linha_fim: 4, coluna_fim: 5 }], parametros: [], retorno: "None",
        argumentos: "0 ou mais" }
];
const escoposSem = [
    { nome: "global", rotulo: "Escopo global", tipo: "global", pai: null },
    { nome: "f", rotulo: "Função f", tipo: "funcao", pai: "global" },
    { nome: "embutido", rotulo: "Funções embutidas do Python", tipo: "embutido", pai: null }
];

test("página carrega o script da análise semântica", () => {
    assert.match(html, /<script src="arvore.js"><\/script>\s*<script src="semantica.js"><\/script>/);
    assert.match(fs.readFileSync("Dockerfile", "utf8"), /semantica\.js/);
    assert.match(fs.readFileSync("semantica.js", "utf8"), /fetch\("\/api\/semantica"\)/);
});

test("possui as seções da análise semântica", () => {
    for (const id of ["painel-semantico", "resultado-semantico", "fases", "codigo-semantico",
        "tabela-simbolos", "detalhe-simbolo", "erros-semanticos", "avisos-semanticos",
        "lista-regras-semanticas", "conceitos-semantico"]) {
        assert.match(html, new RegExp(`id="${id}"`), id);
    }
    assert.match(html, /O que é análise semântica\? E a tabela de símbolos\?/);
    assert.match(html, /não<\/strong> criam escopo/);
});

test("exemplos da Etapa 5 estão no seletor e no código", () => {
    for (const exemplo of ["escopos", "semanticos"]) {
        assert.match(html, new RegExp(`<option value="${exemplo}">`));
        assert.match(js, new RegExp(`${exemplo}: \\[`));
    }
});

test("rótulos e tipos legíveis na tabela de símbolos", () => {
    assert.equal(semantica.rotuloCategoria("parametro"), "parâmetro");
    assert.equal(semantica.rotuloCategoria("embutida"), "função embutida");
    assert.equal(semantica.descreverTipo(tabelaSem[0]), "int");
    assert.equal(semantica.descreverTipo(tabelaSem[1]), "função(a) → desconhecido");
    assert.equal(semantica.descreverTipo(tabelaSem[3]), "função(0 ou mais arg.) → None");
    assert.equal(semantica.descreverTipo({ categoria: "variavel", tipo: "str", tipos: ["int", "str"] }), "int → str");
    assert.equal(semantica.descreverTipo({ categoria: "variavel", tipo: "desconhecido", tipos: ["int"] }),
        "int → desconhecido");
});

test("tabela de símbolos é agrupada por escopo, na ordem dos escopos", () => {
    const grupos = semantica.agruparPorEscopo(tabelaSem, escoposSem);
    assert.deepEqual(grupos.map((g) => g.escopo.nome), ["global", "f", "embutido"]);
    assert.deepEqual(grupos[0].simbolos.map((s) => s.simbolo.nome), ["x", "f"]);
    assert.deepEqual(grupos[1].simbolos.map((s) => s.indice), [2]);
    // Sem embutidas usadas, o grupo "embutido" não aparece.
    assert.equal(semantica.agruparPorEscopo(tabelaSem.slice(0, 3), escoposSem).length, 2);
});

test("selecionar um símbolo destaca a definição e todos os usos", () => {
    const faixas = semantica.faixasDoSimbolo(tabelaSem[0]);
    assert.deepEqual(faixas.map((f) => f.classe), ["destaque-def", "destaque-uso", "destaque-uso"]);
    const html2 = semantica.renderizarCodigoMarcado(arvore.prepararCodigo(codigoSem), faixas);
    const marcas = [...html2.matchAll(/<mark class="([^"]+)">([^<]*)<\/mark>/g)].map((m) => [m[1], m[2]]);
    assert.deepEqual(marcas, [["destaque-def", "x"], ["destaque-uso", "x"], ["destaque-uso", "x"]]);
    assert.equal(html2.replace(/<[^>]+>/g, "").replace(/&gt;/g, ">"), codigoSem);
    // Embutida: só os usos (não há definição no código).
    assert.deepEqual(semantica.faixasDoSimbolo(tabelaSem[3]).map((f) => f.classe), ["destaque-uso"]);
});

test("código marcado escapa HTML", () => {
    const preparado = arvore.prepararCodigo("s = '<b>'");
    const html2 = semantica.renderizarCodigoMarcado(preparado,
        [{ faixa: { linha: 1, coluna: 5, linha_fim: 1, coluna_fim: 9 }, classe: "destaque-uso" }]);
    assert.ok(!html2.includes("<b>"));
    assert.match(html2, /&lt;b&gt;/);
});

test("resumo das três fases mostra onde a análise parou", () => {
    const ok = semantica.resumoFases({ lexico: { sucesso: true, erros: [] },
        sintatico: { executado: true, sucesso: true, erros: [] },
        semantico: { executado: true, sucesso: true, erros: [], avisos: [{}] } });
    assert.deepEqual(ok.map((f) => f.estado), ["ok", "ok", "aviso"]);
    const sint = semantica.resumoFases({ lexico: { sucesso: true, erros: [] },
        sintatico: { executado: true, sucesso: false, erros: [{}, {}] },
        semantico: { executado: false } });
    assert.deepEqual(sint.map((f) => f.estado), ["ok", "erro", "nao_executada"]);
    assert.equal(sint[1].texto, "2 erro(s)");
    const lex = semantica.resumoFases({ lexico: { sucesso: false, erros: [{}] },
        sintatico: { executado: false }, semantico: { executado: false } });
    assert.deepEqual(lex.map((f) => f.estado), ["erro", "nao_executada", "nao_executada"]);
});

test("distingue visualmente erro léxico, sintático e semântico (texto e estilo)", () => {
    const css = fs.readFileSync("style.css", "utf8");
    const sem = fs.readFileSync("semantica.js", "utf8");
    assert.match(js, /ERRO LÉXICO/);
    assert.match(fs.readFileSync("arvore.js", "utf8"), /ERRO SINTÁTICO/);
    assert.match(sem, /ERRO SEMÂNTICO/);
    assert.match(sem, /AVISO SEMÂNTICO/);
    for (const classe of ["etiqueta-erro.lexico", "etiqueta-erro.sintatico", "etiqueta-erro.semantico",
        "erro.erro-semantico", "erro.aviso-semantico"]) {
        assert.match(css, new RegExp("\\." + classe.replace(".", "\\.")), classe);
    }
});

test("diagnóstico semântico mostra regra, explicação, sugestão e erro do Python", () => {
    const sem = fs.readFileSync("semantica.js", "utf8");
    for (const trecho of ["Regra:", "Por quê:", "Como corrigir:", "Ao executar, o Python mostraria",
        "Ver o nó na AST", "erro_semantico", "data-ia-lista"]) {
        assert.ok(sem.includes(trecho), trecho);
    }
});

test("pedido à IA para aviso semântico informa a lista", () => {
    assert.match(fs.readFileSync("ia.js", "utf8"), /alvo\.lista = botao\.dataset\.iaLista/);
    const pedido = ia.montarPedido({ tipo: "erro_semantico", indice: 0, lista: "avisos" }, "x = 1");
    assert.deepEqual(pedido.alvo, { tipo: "erro_semantico", indice: 0, lista: "avisos" });
});
