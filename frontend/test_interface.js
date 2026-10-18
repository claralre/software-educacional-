
const fs = require("node:fs");
const assert = require("node:assert/strict");
const test = require("node:test");

const html = fs.readFileSync(
    "index.html",
    "utf8"
);

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
    assert.match(html, /variavel:/);
    assert.match(html, /soma:/);
    assert.match(html, /multiplicacao:/);
});

test("envia código ao backend", () => {
    assert.match(html, /fetch\("\/api\/analisar"/);
});

test("verifica entradas vazias", () => {
    assert.match(html, /codigo\.trim\(\)/);
});
