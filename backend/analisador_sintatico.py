"""
Analisador sintático (parser) para o subconjunto de Python do projeto.

Estratégia: descendente recursivo, escrito à mão. Cada não terminal da
gramática (docs/GRAMATICA.md) corresponde a um método desta classe, com o
mesmo nome. O parser recebe a lista de tokens produzida pelo scanner da
Etapa 3 e decide o que fazer olhando apenas o token atual (e, em poucos
casos, o seguinte), sem retrocesso.

Além da AST, o parser registra:
- a árvore de derivação (concreta), com todos os terminais e não terminais;
- os passos da construção (entrar/sair de regra, consumir token, criar nó),
  usados pela interface para animar a construção da árvore.

Erros sintáticos são tratados em "modo pânico": o erro é registrado, o
parser descarta tokens até o fim da linha (e o bloco indentado que vier em
seguida, se houver) e continua no próximo comando. Assim, vários erros
independentes podem ser mostrados de uma vez, sem cascata.
"""

import sys
from contextlib import contextmanager

# ---------------------------------------------------------------------------
# Gramática (EBNF) — usada nas mensagens de erro e exibida na interface
# ---------------------------------------------------------------------------

GRAMATICA = {
    "programa": 'programa = { comando } FIM ;',
    "comando": 'comando = se | enquanto | para | funcao | linha_simples ;',
    "linha_simples": 'linha_simples = comando_simples { ";" comando_simples } [ ";" ] NOVA_LINHA ;',
    "comando_simples": 'comando_simples = retorno | "pass" | "break" | "continue" | atribuicao_ou_expressao ;',
    "atribuicao_ou_expressao": 'atribuicao_ou_expressao = expressao [ op_atribuicao expressao ] ;',
    "op_atribuicao": 'op_atribuicao = "=" | "+=" | "-=" | "*=" | "/=" | "//=" | "%=" | "**=" ;',
    "retorno": 'retorno = "return" [ expressao ] ;',
    "se": 'se = "if" expressao ":" bloco { "elif" expressao ":" bloco } [ "else" ":" bloco ] ;',
    "enquanto": 'enquanto = "while" expressao ":" bloco ;',
    "para": 'para = "for" IDENTIFICADOR "in" expressao ":" bloco ;',
    "funcao": 'funcao = "def" IDENTIFICADOR "(" [ parametros ] ")" ":" bloco ;',
    "parametros": 'parametros = IDENTIFICADOR { "," IDENTIFICADOR } [ "," ] ;',
    "bloco": 'bloco = linha_simples | NOVA_LINHA INDENTA comando { comando } DEDENTA ;',
    "expressao": 'expressao = ou ;',
    "ou": 'ou = e { "or" e } ;',
    "e": 'e = nao { "and" nao } ;',
    "nao": 'nao = "not" nao | comparacao ;',
    "comparacao": 'comparacao = soma [ op_comparacao soma ] ;',
    "op_comparacao": 'op_comparacao = "==" | "!=" | "<" | ">" | "<=" | ">=" | "in" | "not" "in" | "is" [ "not" ] ;',
    "soma": 'soma = termo { ( "+" | "-" ) termo } ;',
    "termo": 'termo = unario { ( "*" | "/" | "//" | "%" ) unario } ;',
    "unario": 'unario = ( "+" | "-" ) unario | potencia ;',
    "potencia": 'potencia = primario [ "**" unario ] ;',
    "primario": 'primario = atomo { chamada | indexacao | atributo } ;',
    "chamada": 'chamada = "(" [ argumentos ] ")" ;',
    "argumentos": 'argumentos = expressao { "," expressao } [ "," ] ;',
    "indexacao": 'indexacao = "[" expressao "]" ;',
    "atributo": 'atributo = "." IDENTIFICADOR ;',
    "atomo": ('atomo = IDENTIFICADOR | LITERAL_INTEIRO | LITERAL_REAL | LITERAL_STRING '
              '| "True" | "False" | "None" | "(" expressao ")" | lista ;'),
    "lista": 'lista = "[" [ expressao { "," expressao } [ "," ] ] "]" ;',
}

ORDEM_GRAMATICA = list(GRAMATICA)

# Nome legível de cada tipo de nó da AST e a categoria usada na interface.
TIPOS_NO = {
    "PROGRAMA": ("Programa", "estrutura"),
    "BLOCO": ("Bloco", "estrutura"),
    "ATRIBUICAO": ("Atribuição", "comando"),
    "COMANDO_EXPRESSAO": ("Comando de expressão", "comando"),
    "SE": ("Se (if)", "comando"),
    "SENAO_SE": ("Senão se (elif)", "comando"),
    "ENQUANTO": ("Enquanto (while)", "comando"),
    "PARA": ("Para (for)", "comando"),
    "FUNCAO": ("Definição de função", "comando"),
    "PARAMETRO": ("Parâmetro", "comando"),
    "RETORNO": ("Retorno", "comando"),
    "PASSE": ("Pass", "comando"),
    "INTERROMPE": ("Break", "comando"),
    "CONTINUA": ("Continue", "comando"),
    "ADICAO": ("Adição", "expressao"),
    "SUBTRACAO": ("Subtração", "expressao"),
    "MULTIPLICACAO": ("Multiplicação", "expressao"),
    "DIVISAO": ("Divisão", "expressao"),
    "DIVISAO_INTEIRA": ("Divisão inteira", "expressao"),
    "RESTO": ("Resto da divisão", "expressao"),
    "POTENCIA": ("Potência", "expressao"),
    "UNARIO": ("Operação unária", "expressao"),
    "COMPARACAO": ("Comparação", "expressao"),
    "OPERACAO_LOGICA": ("Operação lógica", "expressao"),
    "NEGACAO": ("Negação lógica (not)", "expressao"),
    "CHAMADA": ("Chamada de função", "expressao"),
    "INDEXACAO": ("Indexação", "expressao"),
    "ACESSO_ATRIBUTO": ("Acesso a atributo", "expressao"),
    "IDENTIFICADOR": ("Identificador", "literal"),
    "NUMERO_INTEIRO": ("Número inteiro", "literal"),
    "NUMERO_REAL": ("Número real", "literal"),
    "TEXTO": ("Texto (string)", "literal"),
    "LOGICO": ("Valor lógico", "literal"),
    "NULO": ("Nulo (None)", "literal"),
    "LISTA": ("Lista", "literal"),
}

OPERADORES_BINARIOS = {
    "+": "ADICAO",
    "-": "SUBTRACAO",
    "*": "MULTIPLICACAO",
    "/": "DIVISAO",
    "//": "DIVISAO_INTEIRA",
    "%": "RESTO",
    "**": "POTENCIA",
}

OPERADORES_ATRIBUICAO = {"=", "+=", "-=", "*=", "/=", "//=", "%=", "**="}
OPERADORES_RELACIONAIS = {"==", "!=", "<", ">", "<=", ">="}

# Palavras reservadas reconhecidas pelo scanner, mas cujas construções
# estão fora do subconjunto desta etapa.
NAO_SUPORTADAS = {
    "class", "import", "from", "try", "except", "finally", "with", "as",
    "lambda", "global", "nonlocal", "del", "assert", "yield", "raise",
    "async", "await",
}

INICIO_EXPRESSAO_PALAVRAS = {"True", "False", "None", "not"}
LIMITE_PROFUNDIDADE = 600


class ErroSintatico(Exception):
    def __init__(self, dados):
        super().__init__(dados["mensagem"])
        self.dados = dados


def descrever_token(token):
    """Texto amigável para um token nas mensagens de erro."""
    tipo = token["tipo"]
    if tipo == "NOVA_LINHA":
        return "o fim da linha"
    if tipo == "FIM":
        return "o fim do código"
    if tipo == "INDENTA":
        return "um aumento de indentação"
    if tipo == "DEDENTA":
        return "o fim do bloco (redução de indentação)"
    if tipo == "PALAVRA_RESERVADA":
        return f"a palavra reservada '{token['lexema']}'"
    return f"'{token['lexema']}'"


def fim_do_token(token):
    """Linha e coluna do último caractere do token (inclusive)."""
    linha, coluna = token["linha"], token["coluna"]
    lexema = token["lexema"] or " "
    partes = lexema.split("\n")
    if len(partes) == 1:
        return linha, coluna + len(lexema) - 1
    return linha + len(partes) - 1, max(len(partes[-1]), 1)


def _eh_inicio_expressao(token):
    tipo, lexema = token["tipo"], token["lexema"]
    if tipo in ("IDENTIFICADOR", "LITERAL_INTEIRO", "LITERAL_REAL", "LITERAL_STRING"):
        return True
    if tipo == "PALAVRA_RESERVADA":
        return lexema in INICIO_EXPRESSAO_PALAVRAS
    if tipo == "DELIMITADOR":
        return lexema in ("(", "[")
    if tipo == "OPERADOR":
        return lexema in ("+", "-")
    return False


class Parser:
    """Parser descendente recursivo: um método por regra da gramática."""

    def __init__(self, tokens, registrar_detalhes=True):
        self.tokens = tokens
        self.pos = 0
        self.erros = []
        self.registrar_detalhes = registrar_detalhes
        self.proximo_id = 0
        self.ultimo = None  # último token "visível" consumido
        self.pilha_regras = []
        self.passos = []
        self.derivacao = {"regra": "inicio", "filhos": []}
        self.pilha_derivacao = [self.derivacao]
        self.consumidos = []

    # -- utilidades ------------------------------------------------------

    def _atual(self, deslocamento=0):
        indice = min(self.pos + deslocamento, len(self.tokens) - 1)
        return self.tokens[indice]

    def _eh(self, tipo, lexema=None, deslocamento=0):
        token = self._atual(deslocamento)
        return token["tipo"] == tipo and (lexema is None or token["lexema"] == lexema)

    def _eh_palavra(self, *palavras):
        return self._eh("PALAVRA_RESERVADA") and self._atual()["lexema"] in palavras

    def _consumir(self):
        token = self._atual()
        indice = self.pos
        if self.pos < len(self.tokens) - 1 or token["tipo"] == "FIM":
            self.pos += 1
        self.consumidos.append(indice)
        if token["tipo"] not in ("NOVA_LINHA", "INDENTA", "DEDENTA", "FIM"):
            self.ultimo = token
        if self.registrar_detalhes:
            self.passos.append({"acao": "consumir", "token": indice})
            self.pilha_derivacao[-1]["filhos"].append({
                "terminal": token["tipo"],
                "lexema": token["lexema"],
                "linha": token["linha"],
                "coluna": token["coluna"],
                "token": indice,
            })
        return token

    @contextmanager
    def _regra(self, nome):
        if len(self.pilha_regras) >= LIMITE_PROFUNDIDADE:
            token = self._atual()
            raise ErroSintatico(self._montar_erro(
                token, ["uma expressão mais simples"],
                "o código tem estruturas aninhadas demais (por exemplo, muitos parênteses "
                "um dentro do outro) para este analisador",
                nome,
                "Divida a expressão em partes menores usando variáveis auxiliares.",
            ))
        self.pilha_regras.append(nome)
        if self.registrar_detalhes:
            no = {"regra": nome, "filhos": []}
            self.pilha_derivacao[-1]["filhos"].append(no)
            self.pilha_derivacao.append(no)
            self.passos.append({"acao": "entrar", "regra": nome})
        try:
            yield
        finally:
            self.pilha_regras.pop()
            if self.registrar_detalhes:
                self.pilha_derivacao.pop()
                self.passos.append({"acao": "sair", "regra": nome})

    def _renomear_regra(self, nome):
        """Troca o nome do nó atual da derivação (ex.: comando_simples -> atribuição)."""
        if self.registrar_detalhes:
            self.pilha_derivacao[-1]["regra"] = nome

    def _no(self, tipo, regra, inicio, atributos=None, filhos=None):
        """Cria um nó da AST. `inicio` é um token ou nó (tem linha/coluna)."""
        fim = self.ultimo or inicio
        if "linha_fim" in fim:
            linha_fim, coluna_fim = fim["linha_fim"], fim["coluna_fim"]
        else:
            linha_fim, coluna_fim = fim_do_token(fim)
        no = {
            "id": self.proximo_id,
            "tipo": tipo,
            "rotulo": TIPOS_NO[tipo][0],
            "categoria": TIPOS_NO[tipo][1],
            "regra": regra,
            "papel": None,
            "atributos": atributos or {},
            "linha": inicio["linha"],
            "coluna": inicio["coluna"],
            "linha_fim": linha_fim,
            "coluna_fim": coluna_fim,
            "filhos": [f for f in (filhos or []) if f is not None],
        }
        self.proximo_id += 1
        if self.registrar_detalhes:
            self.passos.append({"acao": "criar", "no": no["id"]})
        return no

    @staticmethod
    def _papel(no, papel):
        if no is not None:
            no["papel"] = papel
        return no

    # -- erros -----------------------------------------------------------

    def _montar_erro(self, token, esperado, descricao, regra, dica=""):
        linha, coluna = token["linha"], token["coluna"]
        encontrado = descrever_token(token)
        mensagem = f"Erro sintático na linha {linha}, coluna {coluna}: {descricao}."
        return {
            "tipo": "ERRO_SINTATICO",
            "linha": linha,
            "coluna": coluna,
            "encontrado": token["lexema"] if token["tipo"] not in (
                "NOVA_LINHA", "FIM", "INDENTA", "DEDENTA") else token["tipo"],
            "encontrado_descricao": encontrado,
            "esperado": esperado,
            "mensagem": mensagem,
            "regra": regra,
            "producao": GRAMATICA.get(regra, ""),
            "dica": dica,
        }

    def _erro(self, esperado, descricao, regra, dica="", token=None):
        raise ErroSintatico(self._montar_erro(token or self._atual(), esperado, descricao, regra, dica))

    def _erro_esperado(self, simbolo, contexto, regra, dica=""):
        """Erro padrão: 'era esperado X contexto, mas foi encontrado Y'."""
        token = self._atual()
        encontrado = descrever_token(token)
        esperado = "esperada" if simbolo.startswith("uma ") else "esperado"
        if token["tipo"] == "FIM":
            descricao = f"o código terminou, mas era {esperado} {simbolo} {contexto}"
        elif token["tipo"] == "NOVA_LINHA":
            descricao = f"a linha terminou, mas era {esperado} {simbolo} {contexto}"
        else:
            descricao = f"era {esperado} {simbolo} {contexto}, mas foi encontrado {encontrado}"
        self._erro([simbolo], descricao, regra, dica)

    def _esperar(self, tipo, lexema, contexto, regra, dica=""):
        if self._eh(tipo, lexema):
            return self._consumir()
        simbolo = f"'{lexema}'" if lexema else {
            "IDENTIFICADOR": "um nome (identificador)",
            "NOVA_LINHA": "o fim da linha",
        }.get(tipo, tipo)
        if not dica and lexema == ":":
            dica = "Em Python, o cabeçalho de if, elif, else, while, for e def termina com ':'."
        self._erro_esperado(simbolo, contexto, regra, dica)

    def _esperar_nome(self, contexto, regra):
        token = self._atual()
        if token["tipo"] == "IDENTIFICADOR":
            return self._consumir()
        if token["tipo"] == "PALAVRA_RESERVADA":
            self._erro(
                ["um nome (identificador)"],
                f"era esperado um nome {contexto}, mas foi encontrada a palavra reservada "
                f"'{token['lexema']}'",
                regra,
                "Palavras reservadas têm significado especial em Python e não podem ser "
                "usadas como nomes de variáveis, funções ou parâmetros.",
            )
        self._erro_esperado("um nome (identificador)", contexto, regra)

    def _registrar(self, erro):
        # Evita repetir o mesmo erro na mesma posição.
        if not self.erros or (self.erros[-1]["linha"], self.erros[-1]["coluna"]) != (
                erro.dados["linha"], erro.dados["coluna"]):
            self.erros.append(erro.dados)

    def _pular_bloco(self):
        """Descarta um bloco indentado inteiro (INDENTA ... DEDENTA)."""
        profundidade = 0
        while not self._eh("FIM"):
            token = self._consumir_sem_registro()
            if token["tipo"] == "INDENTA":
                profundidade += 1
            elif token["tipo"] == "DEDENTA":
                profundidade -= 1
                if profundidade <= 0:
                    return

    def _consumir_sem_registro(self):
        token = self._atual()
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return token

    def _sincronizar(self):
        """Modo pânico: avança até o início do próximo comando."""
        while True:
            token = self._atual()
            if token["tipo"] in ("FIM", "DEDENTA"):
                return
            if token["tipo"] == "INDENTA":
                self._pular_bloco()
                return
            self._consumir_sem_registro()
            if token["tipo"] == "NOVA_LINHA":
                if self._eh("INDENTA"):
                    self._pular_bloco()
                return
                  # -- comandos --------------------------------------------------------

    def programa(self):
        with self._regra("programa"):
            inicio = self._atual()
            comandos = []
            while not self._eh("FIM"):
                if self._eh("DEDENTA") or self._eh("NOVA_LINHA"):
                    # Só ocorre após recuperação de erro: descarta.
                    self._consumir_sem_registro()
                    continue
                try:
                    comandos.extend(self.comando())
                except ErroSintatico as erro:
                    self._registrar(erro)
                    self._sincronizar()
            self._consumir()  # FIM
            for comando in comandos:
                self._papel(comando, "comando")
            no = self._no("PROGRAMA", "programa", comandos[0] if comandos else inicio,
                          filhos=comandos)
            if not comandos:
                no["linha"], no["coluna"] = 1, 1
            return no

    def comando(self):
        with self._regra("comando"):
            return self._comando()

    def _comando(self):
        token = self._atual()
        if token["tipo"] == "INDENTA":
            self._erro(
                ["um comando no mesmo nível de indentação"],
                "indentação inesperada: esta linha está mais para a direita, mas nenhum "
                "bloco foi aberto com ':' na linha anterior",
                "bloco",
                "Remova os espaços do início da linha ou termine a linha anterior com ':' "
                "(if, while, for, def) para abrir um bloco.",
            )
        if token["tipo"] == "PALAVRA_RESERVADA":
            palavra = token["lexema"]
            if palavra == "if":
                return [self.se()]
            if palavra == "while":
                return [self.enquanto()]
            if palavra == "for":
                return [self.para()]
            if palavra == "def":
                return [self.funcao()]
            if palavra in ("else", "elif"):
                self._erro(
                    ["um comando"],
                    f"'{palavra}' sem um 'if' correspondente",
                    "se",
                    f"'{palavra}' só pode aparecer logo depois do bloco de um 'if' (ou de um "
                    "'elif'), no mesmo nível de indentação do 'if'.",
                )
        return self.linha_simples()

    def linha_simples(self):
        with self._regra("linha_simples"):
            comandos = [self.comando_simples()]
            while self._eh("DELIMITADOR", ";"):
                self._consumir()
                if self._eh("NOVA_LINHA"):
                    break
                comandos.append(self.comando_simples())
            if not self._eh("NOVA_LINHA"):
                anterior = self.ultimo
                dica = ""
                if _eh_inicio_expressao(self._atual()):
                    dica = ("Parece que faltou um operador (como '+' ou '==') ou uma vírgula "
                            "entre dois valores. Cada linha deve conter um único comando.")
                self._erro_esperado(
                    "o fim da linha",
                    f"depois do comando que termina em '{anterior['lexema']}'" if anterior else "",
                    "linha_simples", dica,
                )
            self._consumir()  # NOVA_LINHA
            return comandos

    def comando_simples(self):
        token = self._atual()
        if token["tipo"] == "PALAVRA_RESERVADA":
            palavra = token["lexema"]
            if palavra == "return":
                return self.retorno()
            if palavra in ("pass", "break", "continue"):
                with self._regra("comando_simples"):
                    self._consumir()
                    tipo = {"pass": "PASSE", "break": "INTERROMPE", "continue": "CONTINUA"}[palavra]
                    return self._no(tipo, "comando_simples", token)
            if palavra in ("if", "while", "for", "def"):
                self._erro(
                    ["um comando simples"],
                    f"o comando '{palavra}' precisa começar em uma linha própria",
                    "linha_simples",
                    "Comandos compostos (if, while, for, def) não podem vir depois de ';' "
                    "nem depois de outro comando na mesma linha.",
                )
            if palavra in ("else", "elif"):
                self._erro(["um comando"], f"'{palavra}' sem um 'if' correspondente", "se",
                           f"'{palavra}' deve ficar no início da linha, alinhado com o 'if'.")
            if palavra in NAO_SUPORTADAS:
                self._erro(
                    ["um comando do subconjunto"],
                    f"a construção '{palavra}' não faz parte do subconjunto de Python desta etapa",
                    "comando",
                    "O scanner reconhece todas as palavras reservadas do Python, mas o parser "
                    "só aceita as construções listadas em docs/GRAMATICA.md.",
                )
        return self.atribuicao_ou_expressao()

    def retorno(self):
        with self._regra("retorno"):
            inicio = self._consumir()
            valor = None
            if not (self._eh("NOVA_LINHA") or self._eh("DELIMITADOR", ";")):
                valor = self._papel(self.expressao("depois de 'return'"), "valor")
            return self._no("RETORNO", "retorno", inicio, filhos=[valor])

    def atribuicao_ou_expressao(self):
        with self._regra("atribuicao_ou_expressao"):
            expressao = self.expressao("no início do comando")
            if self._eh("OPERADOR") and self._atual()["lexema"] in OPERADORES_ATRIBUICAO:
                self._renomear_regra("atribuicao")
                self._validar_alvo(expressao)
                operador = self._consumir()["lexema"]
                valor = self.expressao(f"depois de '{operador}'")
                if self._eh("OPERADOR") and self._atual()["lexema"] in OPERADORES_ATRIBUICAO:
                    self._erro(
                        ["o fim da linha"],
                        "atribuições encadeadas (como a = b = 0) não fazem parte do subconjunto",
                        "atribuicao_ou_expressao",
                        "Faça uma atribuição por linha.",
                    )
                return self._no(
                    "ATRIBUICAO", "atribuicao_ou_expressao", expressao,
                    {"operador": operador,
                     "alvo": expressao["atributos"].get("nome")},
                    [self._papel(expressao, "alvo"), self._papel(valor, "valor")],
                )
            self._renomear_regra("expressao_comando")
            return self._no("COMANDO_EXPRESSAO", "atribuicao_ou_expressao", expressao,
                            filhos=[self._papel(expressao, "expressao")])

    def _validar_alvo(self, alvo):
        if alvo["tipo"] in ("IDENTIFICADOR", "INDEXACAO"):
            return
        operador = self._atual()
        if alvo["tipo"] in ("LOGICO", "NULO"):
            descricao = f"não é possível atribuir um valor a '{alvo['atributos'].get('valor')}'"
            dica = "True, False e None são palavras reservadas que representam valores fixos."
        elif alvo["tipo"] in ("NUMERO_INTEIRO", "NUMERO_REAL", "TEXTO"):
            descricao = "o lado esquerdo de uma atribuição não pode ser um valor literal"
            dica = ("O valor fica à direita do '='. Talvez você quisesse comparar? "
                    "Para comparar, use '=='.")
        else:
            descricao = (f"o lado esquerdo de '{operador['lexema']}' precisa ser um nome de "
                         f"variável ou um item de lista, mas é uma {alvo['rotulo'].lower()}")
            dica = "Para comparar valores, use '==' em vez de '='."
        raise ErroSintatico(self._montar_erro(
            operador, ["um nome de variável antes do operador de atribuição"],
            descricao, "atribuicao_ou_expressao", dica))

    def se(self):
        with self._regra("se"):
            inicio = self._consumir()  # if
            condicao = self._papel(self._condicao("if", inicio), "condicao")
            self._esperar("DELIMITADOR", ":", "ao final da condição do 'if'", "se")
            entao = self._papel(self.bloco(f"do 'if' da linha {inicio['linha']}"), "entao")
            filhos = [condicao, entao]
            while self._eh_palavra("elif"):
                elif_token = self._consumir()
                condicao_elif = self._papel(self._condicao("elif", elif_token), "condicao")
                self._esperar("DELIMITADOR", ":", "ao final da condição do 'elif'", "se")
                bloco_elif = self._papel(
                    self.bloco(f"do 'elif' da linha {elif_token['linha']}"), "entao")
                filhos.append(self._papel(
                    self._no("SENAO_SE", "se", elif_token, filhos=[condicao_elif, bloco_elif]),
                    "senao_se"))
            if self._eh_palavra("else"):
                else_token = self._consumir()
                self._esperar("DELIMITADOR", ":", "logo depois de 'else'", "se",
                              "O 'else' não tem condição: escreva apenas 'else:'.")
                filhos.append(self._papel(
                    self.bloco(f"do 'else' da linha {else_token['linha']}"), "senao"))
            return self._no("SE", "se", inicio, filhos=filhos)

    def _condicao(self, palavra, token):
        if not _eh_inicio_expressao(self._atual()):
            dica = ""
            if self._eh("OPERADOR"):
                dica = (f"'{palavra}' é uma palavra reservada e não pode ser usada como nome "
                        "de variável.")
            elif self._eh("DELIMITADOR", ":"):
                dica = f"Escreva a condição entre '{palavra}' e ':', por exemplo: {palavra} x > 0:"
            self._erro_esperado("uma condição (expressão)", f"depois de '{palavra}'",
                                "se" if palavra in ("if", "elif") else "enquanto", dica)
        return self.expressao(f"na condição do '{palavra}'")

    def enquanto(self):
        with self._regra("enquanto"):
            inicio = self._consumir()
            condicao = self._papel(self._condicao("while", inicio), "condicao")
            self._esperar("DELIMITADOR", ":", "ao final da condição do 'while'", "enquanto")
            corpo = self._papel(self.bloco(f"do 'while' da linha {inicio['linha']}"), "corpo")
            return self._no("ENQUANTO", "enquanto", inicio, filhos=[condicao, corpo])

    def para(self):
        with self._regra("para"):
            inicio = self._consumir()
            variavel_token = self._esperar_nome("depois de 'for'", "para")
            variavel = self._papel(self._no("IDENTIFICADOR", "para", variavel_token,
                                            {"nome": variavel_token["lexema"]}), "variavel")
            self._esperar("PALAVRA_RESERVADA", "in", "depois da variável do 'for'", "para",
                          "O laço for tem a forma: for variavel in sequencia:")
            iteravel = self._papel(self.expressao("depois de 'in'"), "iteravel")
            self._esperar("DELIMITADOR", ":", "ao final do cabeçalho do 'for'", "para")
            corpo = self._papel(self.bloco(f"do 'for' da linha {inicio['linha']}"), "corpo")
            return self._no("PARA", "para", inicio, {"variavel": variavel_token["lexema"]},
                            [variavel, iteravel, corpo])

    def funcao(self):
        with self._regra("funcao"):
            inicio = self._consumir()
            nome = self._esperar_nome("para a função depois de 'def'", "funcao")
            self._esperar("DELIMITADOR", "(", "depois do nome da função", "funcao",
                          "Mesmo sem parâmetros, a função precisa de parênteses: def f():")
            parametros = []
            if not self._eh("DELIMITADOR", ")"):
                parametros = self.parametros()
            self._esperar("DELIMITADOR", ")", "para fechar a lista de parâmetros", "funcao")
            self._esperar("DELIMITADOR", ":", "ao final do cabeçalho da função", "funcao")
            corpo = self._papel(self.bloco(f"da função '{nome['lexema']}'"), "corpo")
            return self._no(
                "FUNCAO", "funcao", inicio,
                {"nome": nome["lexema"], "parametros": [p["atributos"]["nome"] for p in parametros]},
                parametros + [corpo])

    def parametros(self):
        with self._regra("parametros"):
            lista = []
            while True:
                token = self._esperar_nome("de parâmetro", "parametros")
                lista.append(self._papel(
                    self._no("PARAMETRO", "parametros", token, {"nome": token["lexema"]}),
                    "parametro"))
                if not self._eh("DELIMITADOR", ","):
                    return lista
                self._consumir()
                if self._eh("DELIMITADOR", ")"):
                    return lista

    def bloco(self, dono):
        with self._regra("bloco"):
            if not self._eh("NOVA_LINHA"):
                # Bloco na mesma linha: if x: y = 1
                inicio = self._atual()
                comandos = self.linha_simples()
                for comando in comandos:
                    self._papel(comando, "comando")
                return self._no("BLOCO", "bloco", inicio, filhos=comandos)
            self._consumir()  # NOVA_LINHA
            if not self._eh("INDENTA"):
                token = self._atual()
                if token["tipo"] == "FIM":
                    descricao = (f"o código terminou antes de o bloco {dono} receber algum "
                                 "comando")
                else:
                    descricao = (f"era esperado um bloco indentado {dono}, mas foi encontrado "
                                 f"{descrever_token(token)} sem recuo")
                self._erro(
                    ["um bloco indentado"], descricao, "bloco",
                    "Depois de ':' o corpo deve vir nas linhas seguintes, com recuo (por "
                    "exemplo, 4 espaços). Para um bloco vazio, use 'pass'.",
                )
            self._consumir()  # INDENTA
            inicio = self._atual()
            comandos = []
            while not self._eh("DEDENTA") and not self._eh("FIM"):
                try:
                    comandos.extend(self.comando())
                except ErroSintatico as erro:
                    self._registrar(erro)
                    self._sincronizar()
            if self._eh("DEDENTA"):
                self._consumir()
            for comando in comandos:
                self._papel(comando, "comando")
            return self._no("BLOCO", "bloco", comandos[0] if comandos else inicio,
                            filhos=comandos)
              # -- expressões ------------------------------------------------------

    def expressao(self, contexto=""):
        with self._regra("expressao"):
            if not _eh_inicio_expressao(self._atual()):
                self._erro_operando(contexto)
            return self.ou()

    def _binario_logico(self, regra, operador, proxima):
        with self._regra(regra):
            esquerda = proxima()
            while self._eh_palavra(operador):
                self._consumir()
                direita = proxima()
                esquerda = self._no(
                    "OPERACAO_LOGICA", regra, esquerda, {"operador": operador},
                    [self._papel(esquerda, "esquerda"), self._papel(direita, "direita")])
            return esquerda

    def ou(self):
        return self._binario_logico("ou", "or", self.e)

    def e(self):
        return self._binario_logico("e", "and", self.nao)

    def nao(self):
        with self._regra("nao"):
            if self._eh_palavra("not"):
                inicio = self._consumir()
                operando = self._papel(self.nao(), "operando")
                return self._no("NEGACAO", "nao", inicio, {"operador": "not"}, [operando])
            return self.comparacao()

    def _operador_comparacao(self):
        """Retorna o operador relacional atual (sem consumir) ou None."""
        token = self._atual()
        if token["tipo"] == "OPERADOR" and token["lexema"] in OPERADORES_RELACIONAIS:
            return token["lexema"]
        if self._eh_palavra("in"):
            return "in"
        if self._eh_palavra("is"):
            return "is not" if self._eh("PALAVRA_RESERVADA", "not", 1) else "is"
        if self._eh_palavra("not") and self._eh("PALAVRA_RESERVADA", "in", 1):
            return "not in"
        return None

    def comparacao(self):
        with self._regra("comparacao"):
            esquerda = self.soma()
            operador = self._operador_comparacao()
            if operador is None:
                return esquerda
            for _ in operador.split():
                self._consumir()
            direita = self.soma()
            if self._operador_comparacao() is not None:
                self._erro(
                    ["o fim da expressão"],
                    "comparações encadeadas (como a < b < c) não fazem parte do subconjunto",
                    "comparacao",
                    "Separe em duas comparações unidas por 'and': a < b and b < c.",
                )
            return self._no("COMPARACAO", "comparacao", esquerda, {"operador": operador},
                            [self._papel(esquerda, "esquerda"), self._papel(direita, "direita")])

    def _binario_aritmetico(self, regra, operadores, proxima):
        with self._regra(regra):
            esquerda = proxima()
            while self._eh("OPERADOR") and self._atual()["lexema"] in operadores:
                operador = self._consumir()["lexema"]
                direita = proxima()
                esquerda = self._no(
                    OPERADORES_BINARIOS[operador], regra, esquerda, {"operador": operador},
                    [self._papel(esquerda, "esquerda"), self._papel(direita, "direita")])
            return esquerda

    def soma(self):
        return self._binario_aritmetico("soma", ("+", "-"), self.termo)

    def termo(self):
        return self._binario_aritmetico("termo", ("*", "/", "//", "%"), self.unario)

    def unario(self):
        with self._regra("unario"):
            if self._eh("OPERADOR", "+") or self._eh("OPERADOR", "-"):
                inicio = self._consumir()
                operando = self._papel(self.unario(), "operando")
                return self._no("UNARIO", "unario", inicio, {"operador": inicio["lexema"]},
                                [operando])
            return self.potencia()

    def potencia(self):
        with self._regra("potencia"):
            base = self.primario()
            if self._eh("OPERADOR", "**"):
                self._consumir()
                expoente = self.unario()  # associativa à direita: 2 ** 3 ** 2
                return self._no("POTENCIA", "potencia", base, {"operador": "**"},
                                [self._papel(base, "esquerda"), self._papel(expoente, "direita")])
            return base

    def primario(self):
        with self._regra("primario"):
            no = self.atomo()
            while True:
                if self._eh("DELIMITADOR", "("):
                    no = self.chamada(no)
                elif self._eh("DELIMITADOR", "["):
                    no = self.indexacao(no)
                elif self._eh("DELIMITADOR", "."):
                    no = self.atributo(no)
                else:
                    return no

    def chamada(self, funcao):
        with self._regra("chamada"):
            abre = self._consumir()
            argumentos = []
            if not self._eh("DELIMITADOR", ")"):
                argumentos = self.argumentos(abre)
            self._esperar_fechamento(")", abre, "chamada", "da chamada de função")
            nome = funcao["atributos"].get("nome") if funcao["tipo"] == "IDENTIFICADOR" else None
            return self._no(
                "CHAMADA", "chamada", funcao, {"nome": nome, "total_argumentos": len(argumentos)},
                [self._papel(funcao, "funcao")] + [self._papel(a, "argumento") for a in argumentos])

    def argumentos(self, abre):
        with self._regra("argumentos"):
            lista = [self.expressao("como argumento")]
            while self._eh("DELIMITADOR", ","):
                self._consumir()
                if self._eh("DELIMITADOR", ")"):
                    break
                lista.append(self.expressao("depois de ','"))
            return lista

    def indexacao(self, objeto):
        with self._regra("indexacao"):
            abre = self._consumir()
            indice = self.expressao("dentro de '[ ]'")
            self._esperar_fechamento("]", abre, "indexacao", "da indexação")
            return self._no("INDEXACAO", "indexacao", objeto, filhos=[
                self._papel(objeto, "objeto"), self._papel(indice, "indice")])

    def atributo(self, objeto):
        with self._regra("atributo"):
            self._consumir()
            nome = self._esperar_nome("depois de '.'", "atributo")
            return self._no("ACESSO_ATRIBUTO", "atributo", objeto, {"atributo": nome["lexema"]},
                            [self._papel(objeto, "objeto")])

    def _esperar_fechamento(self, fecha, abre, regra, contexto):
        if self._eh("DELIMITADOR", fecha):
            return self._consumir()
        dica = ""
        if _eh_inicio_expressao(self._atual()):
            dica = "Faltou uma vírgula ou um operador entre os dois valores?"
        self._erro_esperado(
            f"'{fecha}'",
            f"para fechar o '{abre['lexema']}' {contexto} aberto na linha {abre['linha']}, "
            f"coluna {abre['coluna']}",
            regra, dica)

    def atomo(self):
        with self._regra("atomo"):
            token = self._atual()
            tipo, lexema = token["tipo"], token["lexema"]
            if tipo == "IDENTIFICADOR":
                self._consumir()
                return self._no("IDENTIFICADOR", "atomo", token, {"nome": lexema})
            if tipo == "LITERAL_INTEIRO":
                self._consumir()
                return self._no("NUMERO_INTEIRO", "atomo", token, {"valor": lexema})
            if tipo == "LITERAL_REAL":
                self._consumir()
                return self._no("NUMERO_REAL", "atomo", token, {"valor": lexema})
            if tipo == "LITERAL_STRING":
                self._consumir()
                return self._no("TEXTO", "atomo", token, {"valor": lexema})
            if tipo == "PALAVRA_RESERVADA" and lexema in ("True", "False"):
                self._consumir()
                return self._no("LOGICO", "atomo", token, {"valor": lexema})
            if tipo == "PALAVRA_RESERVADA" and lexema == "None":
                self._consumir()
                return self._no("NULO", "atomo", token, {"valor": lexema})
            if tipo == "DELIMITADOR" and lexema == "(":
                abre = self._consumir()
                interna = self.expressao("dentro dos parênteses")
                fecha = self._esperar_fechamento(")", abre, "atomo", "")
                # Os parênteses não viram nó: só agrupam. O nó interno passa a
                # cobrir também os parênteses no código.
                interna["linha"], interna["coluna"] = abre["linha"], abre["coluna"]
                interna["linha_fim"], interna["coluna_fim"] = fim_do_token(fecha)
                interna["atributos"]["entre_parenteses"] = True
                return interna
            if tipo == "DELIMITADOR" and lexema == "[":
                return self.lista()
            self._erro_operando("")

    def lista(self):
        with self._regra("lista"):
            abre = self._consumir()
            elementos = []
            if not self._eh("DELIMITADOR", "]"):
                elementos.append(self.expressao("como elemento da lista"))
                while self._eh("DELIMITADOR", ","):
                    self._consumir()
                    if self._eh("DELIMITADOR", "]"):
                        break
                    elementos.append(self.expressao("depois de ','"))
            self._esperar_fechamento("]", abre, "lista", "da lista")
            return self._no("LISTA", "lista", abre, {"total_elementos": len(elementos)},
                            [self._papel(e, "elemento") for e in elementos])

    def _erro_operando(self, contexto):
        """Erro quando era esperado um valor (operando) e veio outra coisa."""
        token = self._atual()
        anterior = self.ultimo
        tipo, lexema = token["tipo"], token["lexema"]
        regra = "atomo"
        esperado = ["uma expressão (nome, número, texto, True/False/None, '(' ou '[')"]
        operador_anterior = (anterior is not None and anterior["tipo"] == "OPERADOR"
                             and self.pos > 0 and self.tokens[self.pos - 1] is anterior)
        atribuicao_anterior = operador_anterior and anterior["lexema"] in OPERADORES_ATRIBUICAO
        if atribuicao_anterior and token["tipo"] in ("NOVA_LINHA", "FIM"):
            descricao = (f"a linha terminou logo depois de '{anterior['lexema']}', sem o valor "
                         "a ser atribuído")
            dica = f"Escreva o valor depois de '{anterior['lexema']}', por exemplo: x = 10."
        elif atribuicao_anterior:
            descricao = (f"era esperado o valor a ser atribuído depois de '{anterior['lexema']}', "
                         f"mas foi encontrado {descrever_token(token)}")
            dica = (f"O operador '{lexema}' precisa de um valor à sua esquerda."
                    if tipo == "OPERADOR" else "Escreva um valor (número, texto, nome...) depois do '='.")
        elif tipo == "OPERADOR" and operador_anterior:
            descricao = (f"operadores consecutivos: depois de '{anterior['lexema']}' veio "
                         f"'{lexema}', mas era esperado um valor")
            dica = "Cada operador precisa de um valor (operando) de cada lado, como em 5 + 3."
        elif token["tipo"] in ("NOVA_LINHA", "FIM") and operador_anterior:
            descricao = (f"a expressão terminou logo depois de '{anterior['lexema']}', sem o "
                         "valor do lado direito")
            dica = "Complete a expressão com um valor depois do operador."
        elif tipo == "PALAVRA_RESERVADA":
            descricao = (f"era esperada uma expressão {contexto}, mas foi encontrada a palavra "
                         f"reservada '{lexema}'").replace("  ", " ")
            dica = ("Palavras reservadas não podem ser usadas como valores nem como nomes de "
                    "variáveis.")
        elif token["tipo"] in ("NOVA_LINHA", "FIM"):
            fim = "a linha" if token["tipo"] == "NOVA_LINHA" else "o código"
            descricao = f"{fim} terminou, mas era esperada uma expressão {contexto}".rstrip()
            dica = "Complete o comando com um valor."
        else:
            descricao = (f"era esperada uma expressão {contexto}, mas foi encontrado "
                         f"{descrever_token(token)}").replace("  ", " ")
            dica = ""
            if tipo == "OPERADOR" and lexema in OPERADORES_ATRIBUICAO:
                dica = "Do lado esquerdo do '=' deve vir o nome da variável."
            elif tipo == "OPERADOR":
                dica = f"O operador '{lexema}' precisa de um valor à sua esquerda."
        self._erro(esperado, descricao, regra, dica)


def contar_nos(no, contagem=None):
    contagem = {} if contagem is None else contagem
    contagem[no["tipo"]] = contagem.get(no["tipo"], 0) + 1
    for filho in no["filhos"]:
        contar_nos(filho, contagem)
    return contagem


def analisar_sintaticamente(tokens, registrar_detalhes=True):
    """Executa o parser sobre os tokens do scanner (sem erros léxicos)."""
    # Cada nível de parênteses atravessa ~12 regras; o limite de recursão do
    # Python precisa comportar LIMITE_PROFUNDIDADE regras aninhadas.
    if sys.getrecursionlimit() < 4 * LIMITE_PROFUNDIDADE:
        sys.setrecursionlimit(4 * LIMITE_PROFUNDIDADE)
    parser = Parser(tokens, registrar_detalhes)
    try:
        ast = parser.programa()
    except ErroSintatico as erro:  # erro fora de qualquer comando (raro)
        parser._registrar(erro)
        ast = None
    erros = sorted(parser.erros, key=lambda e: (e["linha"], e["coluna"]))
    sucesso = not erros and ast is not None
    resultado = {
        "sucesso": sucesso,
        "ast": ast if sucesso else None,
        "erros": erros,
        "derivacao": None,
        "passos": None,
        "resumo": None,
    }
    if sucesso:
        contagem = contar_nos(ast)
        resultado["resumo"] = {"total_nos": sum(contagem.values()), "por_tipo": contagem}
        if registrar_detalhes:
            resultado["derivacao"] = parser.derivacao["filhos"][0]
            resultado["passos"] = parser.passos
    return resultado
          
