"""
Analisador léxico (scanner) para um subconjunto da linguagem Python.

O scanner foi escrito à mão, sem bibliotecas de geração de analisadores
e sem usar o módulo `tokenize` do Python, para que cada decisão fique
visível ao estudante. Ele percorre o código caractere a caractere,
agrupa os caracteres em lexemas e classifica cada lexema em uma
categoria de token, registrando linha e coluna (ambas começando em 1).

Como Python usa a indentação para delimitar blocos, o scanner também
gera os tokens estruturais NOVA_LINHA, INDENTA, DEDENTA e FIM, da mesma
forma que o tokenizador oficial da linguagem.

Erros léxicos não interrompem a análise: são acumulados em uma lista e
o scanner continua a partir do próximo caractere, para que o usuário
veja todos os problemas de uma só vez.
"""

# ---------------------------------------------------------------------------
# Tabelas do escopo léxico
# ---------------------------------------------------------------------------

# Todas as palavras reservadas do Python 3. Mesmo as que ainda não serão
# usadas nas próximas etapas (ex.: class, try) são reconhecidas, pois
# lexicamente não podem ser usadas como identificadores.
PALAVRAS_RESERVADAS = {
    "False", "None", "True", "and", "as", "assert", "async", "await",
    "break", "class", "continue", "def", "del", "elif", "else", "except",
    "finally", "for", "from", "global", "if", "import", "in", "is",
    "lambda", "nonlocal", "not", "or", "pass", "raise", "return", "try",
    "while", "with", "yield",
}

PREFIXOS_STRING = {"r", "u", "f", "b", "rb", "br", "fr", "rf"}

PALAVRAS_LOGICAS = {"and", "or", "not"}
PALAVRAS_LITERAIS = {"True", "False", "None"}

# Operadores ordenados do maior para o menor, para aplicar a regra do
# "casamento mais longo" (maximal munch): `**=` antes de `**` antes de `*`.
OPERADORES = {
    "**=": "atribuição composta",
    "//=": "atribuição composta",
    "**": "aritmético (potência)",
    "//": "aritmético (divisão inteira)",
    "==": "relacional (igual a)",
    "!=": "relacional (diferente de)",
    "<=": "relacional (menor ou igual)",
    ">=": "relacional (maior ou igual)",
    "+=": "atribuição composta",
    "-=": "atribuição composta",
    "*=": "atribuição composta",
    "/=": "atribuição composta",
    "%=": "atribuição composta",
    "+": "aritmético (soma)",
    "-": "aritmético (subtração)",
    "*": "aritmético (multiplicação)",
    "/": "aritmético (divisão)",
    "%": "aritmético (resto)",
    "<": "relacional (menor que)",
    ">": "relacional (maior que)",
    "=": "atribuição",
}
OPERADORES_ORDENADOS = sorted(OPERADORES, key=len, reverse=True)

DELIMITADORES = {
    "(": "abre parênteses",
    ")": "fecha parênteses",
    "[": "abre colchetes",
    "]": "fecha colchetes",
    "{": "abre chaves",
    "}": "fecha chaves",
    ",": "vírgula",
    ":": "dois-pontos (início de bloco)",
    ".": "ponto (acesso a atributo)",
    ";": "ponto e vírgula",
}
ABERTURAS = {"(": ")", "[": "]", "{": "}"}
FECHAMENTOS = {v: k for k, v in ABERTURAS.items()}

# Mensagens específicas para caracteres comuns fora do subconjunto.
DICAS_CARACTERES = {
    "@": "Decoradores e o operador '@' não fazem parte do subconjunto suportado.",
    "$": "Em Python, '$' não é usado em nomes de variáveis.",
    "?": "Python não possui o operador ternário '?:'. Use 'x if cond else y'.",
    "!": "Sozinho, '!' não existe em Python. Para negação use 'not'; para 'diferente' use '!='.",
    "&": "Para o 'e' lógico, use a palavra reservada 'and'.",
    "|": "Para o 'ou' lógico, use a palavra reservada 'or'.",
    "~": "O operador bit a bit '~' não faz parte do subconjunto suportado.",
    "^": "O operador bit a bit '^' não faz parte do subconjunto suportado. Para potência use '**'.",
    "`": "A crase não é utilizada em Python. Para textos, use aspas simples ou duplas.",
    "\\": "A barra invertida só é permitida no fim da linha (continuação) ou dentro de strings.",
}

TIPOS_TOKEN = [
    "PALAVRA_RESERVADA",
    "IDENTIFICADOR",
    "LITERAL_INTEIRO",
    "LITERAL_REAL",
    "LITERAL_STRING",
    "OPERADOR",
    "DELIMITADOR",
    "NOVA_LINHA",
    "INDENTA",
    "DEDENTA",
    "FIM",
]

TAMANHO_TABULACAO = 8


def _eh_inicio_identificador(c):
    return c == "_" or c.isalpha()


def _eh_parte_identificador(c):
    return c == "_" or c.isalnum()


class Scanner:
    """Percorre o código-fonte e produz tokens e erros léxicos."""

    def __init__(self, codigo):
        # Normaliza quebras de linha do Windows (\r\n) e do Mac antigo (\r).
        self.codigo = codigo.replace("\r\n", "\n").replace("\r", "\n")
        self.pos = 0
        self.linha = 1
        self.coluna = 1
        self.tokens = []
        self.erros = []
        self.comentarios = []
        self.pilha_indentacao = [0]
        self.pilha_agrupamento = []  # (caractere, linha, coluna)
        self.inicio_de_linha = True

    # -- navegação --------------------------------------------------------

    def _atual(self, deslocamento=0):
        indice = self.pos + deslocamento
        if indice < len(self.codigo):
            return self.codigo[indice]
        return ""

    def _avancar(self):
        c = self.codigo[self.pos]
        self.pos += 1
        if c == "\n":
            self.linha += 1
            self.coluna = 1
        else:
            self.coluna += 1
        return c

    def _fim(self):
        return self.pos >= len(self.codigo)

    # -- registro ---------------------------------------------------------

    def _token(self, tipo, lexema, linha, coluna, descricao, explicacao):
        self.tokens.append({
            "tipo": tipo,
            "lexema": lexema,
            "linha": linha,
            "coluna": coluna,
            "descricao": descricao,
            "explicacao": explicacao,
        })

    def _erro(self, lexema, linha, coluna, mensagem, dica):
        self.erros.append({
            "tipo": "ERRO_LEXICO",
            "lexema": lexema,
            "linha": linha,
            "coluna": coluna,
            "mensagem": mensagem,
            "dica": dica,
        })

    # -- laço principal ---------------------------------------------------

    def analisar(self):
        while not self._fim():
            if self.inicio_de_linha:
                self._tratar_indentacao()
                if self._fim():
                    break

            c = self._atual()

            if c == "\n":
                self._tratar_quebra_de_linha()
            elif c in " \t\f":
                self._avancar()
            elif c == "#":
                self._ler_comentario()
            elif c == "\\":
                self._ler_continuacao()
            elif _eh_inicio_identificador(c):
                self._ler_identificador()
            elif c.isdigit() or (c == "." and self._atual(1).isdigit()):
                self._ler_numero()
            elif c in "\"'":
                self._ler_string()
            elif self._tentar_operador():
                pass
            elif c in DELIMITADORES:
                self._ler_delimitador()
            else:
                self._ler_caractere_invalido()

        self._finalizar()
        return self.resultado()

    def resultado(self):
        contagem = {}
        for token in self.tokens:
            contagem[token["tipo"]] = contagem.get(token["tipo"], 0) + 1
        self.erros.sort(key=lambda erro: (erro["linha"], erro["coluna"]))
        return {
            "tokens": self.tokens,
            "erros": self.erros,
            "comentarios": self.comentarios,
            "resumo": {
                "total_tokens": len(self.tokens),
                "total_erros": len(self.erros),
                "por_tipo": contagem,
            },
        }

    # -- linhas e indentação ----------------------------------------------

    def _tratar_indentacao(self):
        """Mede a indentação no começo de uma linha lógica."""
        linha = self.linha
        largura = 0
        texto = ""
        while self._atual() in (" ", "\t", "\f"):
            c = self._avancar()
            texto += c
            if c == " ":
                largura += 1
            elif c == "\t":
                largura = (largura // TAMANHO_TABULACAO + 1) * TAMANHO_TABULACAO
            else:
                largura = 0

        # Linhas em branco ou só com comentário não alteram a indentação.
        if self._atual() in ("\n", "#", ""):
            return

        self.inicio_de_linha = False

        if " " in texto and "\t" in texto:
            self._erro(
                texto, linha, 1,
                f"Erro léxico na linha {linha}, coluna 1: indentação "
                "mistura espaços e tabulações.",
                "Use apenas espaços (de preferência 4 por nível) para indentar.",
            )

        topo = self.pilha_indentacao[-1]
        if largura > topo:
            self.pilha_indentacao.append(largura)
            self._token(
                "INDENTA", texto, linha, 1,
                "aumento de indentação (abre bloco)",
                f"A linha começa com {largura} espaço(s), mais do que o "
                f"bloco anterior ({topo}). Isso abre um novo bloco.",
            )
        elif largura < topo:
            while largura < self.pilha_indentacao[-1]:
                self.pilha_indentacao.pop()
                self._token(
                    "DEDENTA", "", linha, len(texto) + 1,
                    "redução de indentação (fecha bloco)",
                    f"A linha começa com {largura} espaço(s), menos do que "
                    "o bloco anterior. Isso fecha um bloco.",
                )
            if largura != self.pilha_indentacao[-1]:
                self._erro(
                    texto, linha, 1,
                    f"Erro léxico na linha {linha}, coluna 1: a indentação "
                    f"({largura} espaço(s)) não corresponde a nenhum bloco "
                    "aberto anteriormente.",
                    "Alinhe a linha com o início de um bloco anterior.",
                )
                # Recupera-se assumindo a nova largura como um nível válido.
                self.pilha_indentacao.append(largura)

    def _tratar_quebra_de_linha(self):
        linha, coluna = self.linha, self.coluna
        self._avancar()
        # Dentro de (), [] ou {} a quebra de linha é ignorada
        # (junção implícita de linhas).
        if self.pilha_agrupamento:
            return
        # Só emite NOVA_LINHA se a linha tiver algum token (linhas em
        # branco ou só com comentários são ignoradas).
        if self.tokens and self.tokens[-1]["tipo"] not in ("NOVA_LINHA", "INDENTA", "DEDENTA"):
            self._token(
                "NOVA_LINHA", "\n", linha, coluna,
                "fim de linha lógica",
                "Em Python, a quebra de linha encerra uma instrução.",
            )
        self.inicio_de_linha = True

    def _ler_continuacao(self):
        linha, coluna = self.linha, self.coluna
        if self._atual(1) == "\n":
            self._avancar()
            self._avancar()  # junção explícita: linha continua na próxima
            return
        self._avancar()
        self._erro(
            "\\", linha, coluna,
            f"Erro léxico na linha {linha}, coluna {coluna}: caractere "
            "não reconhecido '\\'.",
            DICAS_CARACTERES["\\"],
        )

    def _finalizar(self):
        for abertura, linha, coluna in self.pilha_agrupamento:
            self._erro(
                abertura, linha, coluna,
                f"Erro léxico na linha {linha}, coluna {coluna}: "
                f"'{abertura}' foi aberto e nunca fechado.",
                f"Feche com '{ABERTURAS[abertura]}' antes do fim do código.",
            )
        if self.tokens and self.tokens[-1]["tipo"] not in ("NOVA_LINHA", "DEDENTA"):
            self._token(
                "NOVA_LINHA", "", self.linha, self.coluna,
                "fim de linha lógica",
                "O código terminou sem quebra de linha; o scanner insere "
                "o fim da última instrução automaticamente.",
            )
        while len(self.pilha_indentacao) > 1:
            self.pilha_indentacao.pop()
            self._token(
                "DEDENTA", "", self.linha, self.coluna,
                "redução de indentação (fecha bloco)",
                "No fim do código, todos os blocos abertos são fechados.",
            )
        self._token(
            "FIM", "", self.linha, self.coluna,
            "fim do código-fonte",
            "Marca o fim da entrada. O analisador sintático usará este token.",
        )

    # -- reconhecedores ---------------------------------------------------

    def _ler_comentario(self):
        linha, coluna = self.linha, self.coluna
        inicio = self.pos
        while not self._fim() and self._atual() != "\n":
            self._avancar()
        self.comentarios.append({
            "lexema": self.codigo[inicio:self.pos],
            "linha": linha,
            "coluna": coluna,
        })

    def _ler_identificador(self):
        linha, coluna = self.linha, self.coluna
        inicio = self.pos
        while not self._fim() and _eh_parte_identificador(self._atual()):
            self._avancar()
        lexema = self.codigo[inicio:self.pos]

        # Prefixos de string: r"...", f"...", b"..." etc.
        if lexema.lower() in PREFIXOS_STRING and self._atual() in ("'", '"'):
            self._ler_string(inicio, linha, coluna)
            return

        if lexema in PALAVRAS_RESERVADAS:
            if lexema in PALAVRAS_LOGICAS:
                descricao = "palavra reservada (operador lógico)"
            elif lexema in PALAVRAS_LITERAIS:
                descricao = "palavra reservada (valor constante)"
            else:
                descricao = "palavra reservada"
            self._token(
                "PALAVRA_RESERVADA", lexema, linha, coluna, descricao,
                f"'{lexema}' começa com letra, como um identificador, mas "
                "está na tabela de palavras reservadas.",
            )
        else:
            self._token(
                "IDENTIFICADOR", lexema, linha, coluna, "nome definido pelo programador",
                f"'{lexema}' começa com letra ou '_' e continua com letras, "
                "dígitos ou '_', e não é palavra reservada.",
            )

    def _ler_digitos(self):
        while not self._fim() and (self._atual().isdigit() or self._atual() == "_"):
            self._avancar()

    def _ler_numero(self):
        linha, coluna = self.linha, self.coluna
        inicio = self.pos
        real = False

        self._ler_digitos()
        if self._atual() == "." and (
                not _eh_inicio_identificador(self._atual(1))
                or (self._atual(1) in ("e", "E") and self._atual(2).isdigit())):
            real = True
            self._avancar()
            self._ler_digitos()
        if self._atual() in ("e", "E"):
            prox = self._atual(1)
            if prox.isdigit() or (prox in "+-" and prox and self._atual(2).isdigit()):
                real = True
                self._avancar()
                if self._atual() in "+-":
                    self._avancar()
                self._ler_digitos()

        # Letras ou dígitos colados ao número formam um literal malformado
        # (ex.: 12abc, 3.14.15).
        if not self._fim() and (_eh_parte_identificador(self._atual()) or
                                (self._atual() == "." and self._atual(1).isdigit())):
            while not self._fim() and (_eh_parte_identificador(self._atual()) or self._atual() == "."):
                self._avancar()
            lexema = self.codigo[inicio:self.pos]
            self._erro(
                lexema, linha, coluna,
                f"Erro léxico na linha {linha}, coluna {coluna}: literal "
                f"numérico malformado '{lexema}'.",
                "Um identificador não pode começar com dígito, e um número "
                "só pode ter um ponto decimal.",
            )
            return

        lexema = self.codigo[inicio:self.pos]

        if "__" in lexema or lexema.endswith("_") or "_." in lexema or "._" in lexema:
            self._erro(
                lexema, linha, coluna,
                f"Erro léxico na linha {linha}, coluna {coluna}: uso "
                f"inválido de '_' no número '{lexema}'.",
                "O '_' pode separar dígitos (ex.: 1_000), mas apenas um por "
                "vez e nunca no fim.",
            )
            return

        if real:
            self._token(
                "LITERAL_REAL", lexema, linha, coluna, "número real (ponto flutuante)",
                f"'{lexema}' é formado por dígitos com ponto decimal e/ou expoente.",
            )
            return

        if len(lexema) > 1 and lexema[0] == "0" and lexema.replace("_", "").strip("0"):
            self._erro(
                lexema, linha, coluna,
                f"Erro léxico na linha {linha}, coluna {coluna}: o inteiro "
                f"'{lexema}' começa com zero.",
                "Em Python, inteiros diferentes de zero não podem começar com "
                "'0'. Remova os zeros à esquerda.",
            )
            return

        self._token(
            "LITERAL_INTEIRO", lexema, linha, coluna, "número inteiro",
            f"'{lexema}' é formado apenas por dígitos.",
        )

    def _ler_string(self, inicio=None, linha=None, coluna=None):
        if inicio is None:
            inicio, linha, coluna = self.pos, self.linha, self.coluna
        aspa = self._atual()
        tripla = self._atual(1) == aspa and self._atual(2) == aspa
        delimitador = aspa * 3 if tripla else aspa
        for _ in delimitador:
            self._avancar()

        while True:
            if self._fim():
                lexema = self.codigo[inicio:self.pos]
                self._erro(
                    lexema, linha, coluna,
                    f"Erro léxico na linha {linha}, coluna {coluna}: string "
                    f"iniciada com {delimitador} não foi fechada.",
                    f"Feche a string com {delimitador}.",
                )
                return
            c = self._atual()
            if c == "\n" and not tripla:
                lexema = self.codigo[inicio:self.pos]
                self._erro(
                    lexema, linha, coluna,
                    f"Erro léxico na linha {linha}, coluna {coluna}: string "
                    f"iniciada com {aspa} não foi fechada nesta linha.",
                    f"Feche a string com {aspa} na mesma linha ou use aspas "
                    "triplas para textos com várias linhas.",
                )
                return
            if c == "\\":
                self._avancar()
                if not self._fim():
                    self._avancar()
                continue
            if self.codigo.startswith(delimitador, self.pos):
                for _ in delimitador:
                    self._avancar()
                break
            self._avancar()

        lexema = self.codigo[inicio:self.pos]
        self._token(
            "LITERAL_STRING", lexema, linha, coluna, "texto (string)",
            f"Começa com {delimitador} e vai até o próximo {delimitador}.",
        )

    def _tentar_operador(self):
        for operador in OPERADORES_ORDENADOS:
            if self.codigo.startswith(operador, self.pos):
                linha, coluna = self.linha, self.coluna
                for _ in operador:
                    self._avancar()
                if len(operador) > 1:
                    explicacao = (f"O scanner leu '{operador}' como um único "
                                  "token (regra do casamento mais longo).")
                else:
                    explicacao = f"'{operador}' é um operador do subconjunto."
                self._token("OPERADOR", operador, linha, coluna,
                            OPERADORES[operador], explicacao)
                return True
        return False

    def _ler_delimitador(self):
        linha, coluna = self.linha, self.coluna
        c = self._avancar()
        if c in ABERTURAS:
            self.pilha_agrupamento.append((c, linha, coluna))
        elif c in FECHAMENTOS:
            if self.pilha_agrupamento and self.pilha_agrupamento[-1][0] == FECHAMENTOS[c]:
                self.pilha_agrupamento.pop()
            # Fechamentos sem par são problemas de estrutura; o parser
            # (Etapa 4) é quem os reportará. O scanner apenas os tokeniza.
        self._token("DELIMITADOR", c, linha, coluna, DELIMITADORES[c],
                    f"'{c}' é um delimitador do subconjunto.")

    def _ler_caractere_invalido(self):
        linha, coluna = self.linha, self.coluna
        c = self._avancar()
        dica = DICAS_CARACTERES.get(
            c, "Verifique se ele faz parte do subconjunto suportado."
        )
        self._erro(
            c, linha, coluna,
            f"Erro léxico na linha {linha}, coluna {coluna}: caractere não "
            f"reconhecido '{c}'.",
            dica,
        )


def escopo_lexico():
    """Descreve o subconjunto léxico, para ser exibido pela interface."""
    return {
        "linguagem": "Python (subconjunto)",
        "palavras_reservadas": sorted(PALAVRAS_RESERVADAS, key=str.lower),
        "operadores": [
            {"lexema": op, "descricao": OPERADORES[op]}
            for op in sorted(OPERADORES, key=len)
        ],
        "delimitadores": [
            {"lexema": d, "descricao": DELIMITADORES[d]} for d in DELIMITADORES
        ],
        "tipos_token": TIPOS_TOKEN,
    }


def analisar_lexicamente(codigo):
    """Função de conveniência usada pelo backend."""
    return Scanner(codigo).analisar()
