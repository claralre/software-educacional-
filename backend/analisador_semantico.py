
import difflib

DESCONHECIDO = "desconhecido"
NUMERICOS = {"int", "float", "bool"}
NAO_ITERAVEIS = {"int", "float", "bool", "None", "função"}
SEQUENCIAS = {"str", "list", "range"}

# Funções embutidas reconhecidas: tipo do resultado e número de argumentos.
EMBUTIDAS = {
    "print": {"retorno": "None", "min": 0, "max": None},
    "input": {"retorno": "str", "min": 0, "max": 1},
    "len": {"retorno": "int", "min": 1, "max": 1},
    "range": {"retorno": "range", "min": 1, "max": 3},
    "int": {"retorno": "int", "min": 0, "max": 2},
    "float": {"retorno": "float", "min": 0, "max": 1},
    "str": {"retorno": "str", "min": 0, "max": 1},
    "bool": {"retorno": "bool", "min": 0, "max": 1},
    "list": {"retorno": "list", "min": 0, "max": 1},
    "abs": {"retorno": DESCONHECIDO, "min": 1, "max": 1},
    "min": {"retorno": DESCONHECIDO, "min": 1, "max": None},
    "max": {"retorno": DESCONHECIDO, "min": 1, "max": None},
    "sum": {"retorno": DESCONHECIDO, "min": 1, "max": 2},
    "round": {"retorno": DESCONHECIDO, "min": 1, "max": 2},
    "sorted": {"retorno": "list", "min": 1, "max": 1},
    "type": {"retorno": DESCONHECIDO, "min": 1, "max": 1},
    "isinstance": {"retorno": "bool", "min": 2, "max": 2},
}

# Cada regra: título, explicação em linguagem acessível, gravidade e o erro
# que o Python mostraria ao executar o programa.
REGRAS = {
    "IDENTIFICADOR_NAO_DEFINIDO": {
        "titulo": "Nome usado sem ter recebido valor",
        "gravidade": "erro",
        "erro_python": "NameError",
        "explicacao": "Em Python, uma variável só passa a existir quando recebe um valor "
                      "(por exemplo, total = 0). Usar um nome antes disso, ou que nunca recebeu "
                      "valor, é um erro: o programa não sabe a que o nome se refere.",
    },
    "ATRIBUICAO_COMPOSTA_SEM_VALOR": {
        "titulo": "Atribuição composta sem valor anterior",
        "gravidade": "erro",
        "erro_python": "NameError",
        "explicacao": "Uma atribuição composta como x += 1 significa x = x + 1: ela lê o valor "
                      "atual de x. Por isso x precisa ter recebido um valor antes.",
    },
    "VARIAVEL_LOCAL_SEM_VALOR": {
        "titulo": "Variável local usada antes de receber valor",
        "gravidade": "erro",
        "erro_python": "UnboundLocalError",
        "explicacao": "Se um nome recebe valor em algum ponto de uma função, o Python o trata como "
                      "variável LOCAL da função inteira, mesmo antes dessa atribuição. Lê-lo antes "
                      "de a função lhe dar um valor é um erro, ainda que exista uma variável global "
                      "com o mesmo nome.",
    },
    "TIPOS_INCOMPATIVEIS": {
        "titulo": "Operação entre tipos incompatíveis",
        "gravidade": "erro",
        "erro_python": "TypeError",
        "explicacao": "Cada operador aceita certos tipos. '+' soma números, junta dois textos ou "
                      "junta duas listas; '-', '/' e '**' só funcionam com números; '*' multiplica "
                      "números ou repete um texto ou lista por um inteiro. Misturar, por exemplo, "
                      "texto e número em uma soma é um erro.",
    },
    "OPERANDO_INVALIDO": {
        "titulo": "Sinal aplicado a um valor que não é número",
        "gravidade": "erro",
        "erro_python": "TypeError",
        "explicacao": "Os operadores de um operando, como -x e +x, só funcionam com números.",
    },
    "COMPARACAO_INVALIDA": {
        "titulo": "Comparação de ordem entre tipos diferentes",
        "gravidade": "erro",
        "erro_python": "TypeError",
        "explicacao": "Os operadores <, >, <= e >= comparam números com números, textos com textos "
                      "ou listas com listas. Comparar a ordem de um texto com um número é um erro. "
                      "(== e != podem comparar quaisquer valores.)",
    },
    "NAO_ITERAVEL": {
        "titulo": "Valor que não pode ser percorrido",
        "gravidade": "erro",
        "erro_python": "TypeError",
        "explicacao": "O for e o operador in percorrem coleções: textos, listas e range(...). "
                      "Um número, um valor lógico ou None não podem ser percorridos.",
    },
    "NAO_INDEXAVEL": {
        "titulo": "Indexação em valor que não tem itens",
        "gravidade": "erro",
        "erro_python": "TypeError",
        "explicacao": "Só textos, listas e range(...) têm itens acessíveis por índice, como v[0]. "
                      "Um número ou None não têm itens.",
    },
    "INDICE_INVALIDO": {
        "titulo": "Índice que não é inteiro",
        "gravidade": "erro",
        "erro_python": "TypeError",
        "explicacao": "O índice de um texto ou de uma lista indica uma posição e precisa ser um "
                      "número inteiro, como v[0] ou v[i].",
    },
    "ITEM_IMUTAVEL": {
        "titulo": "Alteração de um item de texto",
        "gravidade": "erro",
        "erro_python": "TypeError",
        "explicacao": "Textos (str) são imutáveis: não é possível trocar uma letra com t[0] = 'a'. "
                      "Para mudar um texto, crie um novo texto.",
    },
    "NAO_CHAMAVEL": {
        "titulo": "Chamada de algo que não é função",
        "gravidade": "erro",
        "erro_python": "TypeError",
        "explicacao": "Só funções podem ser chamadas com parênteses, como f(1). Um número, texto "
                      "ou lista não pode ser chamado.",
    },
    "ARGUMENTOS_INCORRETOS": {
        "titulo": "Número errado de argumentos",
        "gravidade": "erro",
        "erro_python": "TypeError",
        "explicacao": "Uma chamada deve passar um argumento para cada parâmetro da função. Neste "
                      "subconjunto não há parâmetros com valor padrão, então o número precisa ser "
                      "exatamente igual. As funções embutidas aceitam uma quantidade definida.",
    },
    "ARGUMENTO_INVALIDO": {
        "titulo": "Argumento de tipo inadequado",
        "gravidade": "erro",
        "erro_python": "TypeError",
        "explicacao": "Algumas funções embutidas exigem um tipo de argumento: len() precisa de um "
                      "texto ou lista, e range() precisa de números inteiros.",
    },
    "PARAMETRO_DUPLICADO": {
        "titulo": "Parâmetro repetido",
        "gravidade": "erro",
        "erro_python": "SyntaxError",
        "explicacao": "Cada parâmetro de uma função precisa ter um nome diferente; senão não haveria "
                      "como saber qual valor cada nome representa.",
    },
    "RETORNO_FORA_DE_FUNCAO": {
        "titulo": "return fora de função",
        "gravidade": "erro",
        "erro_python": "SyntaxError",
        "explicacao": "O return encerra uma função e devolve um valor para quem a chamou. Fora de "
                      "uma função não há para onde voltar. A gramática aceita o comando em qualquer "
                      "lugar; é a análise do contexto que detecta o problema.",
    },
    "FORA_DE_LACO": {
        "titulo": "break ou continue fora de laço",
        "gravidade": "erro",
        "erro_python": "SyntaxError",
        "explicacao": "break interrompe e continue pula para a próxima repetição de um laço (while "
                      "ou for). Fora de um laço eles não têm significado. Uma função dentro de um "
                      "laço começa um contexto novo, sem laço.",
    },
    "POSSIVELMENTE_NAO_DEFINIDA": {
        "titulo": "Variável que pode não ter recebido valor",
        "gravidade": "aviso",
        "erro_python": "NameError (em alguns casos)",
        "explicacao": "O nome só recebe valor dentro de um if, de um laço ou mais adiante no mesmo "
                      "laço. Se esse trecho não for executado, o nome ainda não terá valor quando "
                      "for usado. Não é um erro certo, por isso aparece como aviso.",
    },
    "MUDANCA_DE_TIPO": {
        "titulo": "Variável que muda de tipo",
        "gravidade": "aviso",
        "erro_python": "nenhum (é permitido)",
        "explicacao": "Python permite que uma variável receba valores de tipos diferentes ao longo "
                      "do programa (tipagem dinâmica). Isso não é erro, mas costuma confundir e "
                      "seria proibido em linguagens como C e Java.",
    },
    "SOMBREIA_EMBUTIDA": {
        "titulo": "Nome de função embutida reaproveitado",
        "gravidade": "aviso",
        "erro_python": "nenhum (é permitido)",
        "explicacao": "Dar valor a um nome como list, print ou len esconde a função embutida do "
                      "Python com o mesmo nome dali em diante. É permitido, mas costuma causar "
                      "erros mais tarde.",
    },
}

ORDEM_REGRAS = list(REGRAS)

OPERADORES_ARITMETICOS = {
    "ADICAO": "+", "SUBTRACAO": "-", "MULTIPLICACAO": "*", "DIVISAO": "/",
    "DIVISAO_INTEIRA": "//", "RESTO": "%", "POTENCIA": "**",
}

TIPOS_LITERAIS = {
    "NUMERO_INTEIRO": "int", "NUMERO_REAL": "float", "TEXTO": "str",
    "LOGICO": "bool", "NULO": "None",
}


def _nome_tipo(tipo):
    return {"None": "None", "função": "função"}.get(tipo, tipo)


class _Escopo:
    def __init__(self, nome, rotulo, tipo, pai, no, atribuidos, assinaturas):
        self.nome = nome
        self.rotulo = rotulo
        self.tipo = tipo            # "global", "funcao" ou "embutido"
        self.pai = pai
        self.no = no
        self.atribuidos = atribuidos    # nome -> (linha, coluna) da 1ª atribuição no texto
        self.assinaturas = assinaturas  # nome da função -> lista de parâmetros
        self.simbolos = {}
        self.certos = set()             # nomes que, com certeza, já têm valor
        self.talvez = set()             # nomes que talvez tenham valor
        self.retornos = []

    def cadeia(self):
        escopo = self
        while escopo:
            yield escopo
            escopo = escopo.pai


def _filhos(no, papel):
    return [f for f in no["filhos"] if f.get("papel") == papel]


def _filho(no, papel):
    lista = _filhos(no, papel)
    return lista[0] if lista else None


def _posicao(no):
    return {"linha": no["linha"], "coluna": no["coluna"],
            "linha_fim": no.get("linha_fim", no["linha"]),
            "coluna_fim": no.get("coluna_fim", no["coluna"])}


def _coletar(comandos, atribuidos, assinaturas):
    """Pré-coleta: nomes que recebem valor e funções definidas neste escopo."""
    for no in comandos:
        tipo = no["tipo"]
        if tipo == "ATRIBUICAO":
            alvo = _filho(no, "alvo")
            if alvo is not None and alvo["tipo"] == "IDENTIFICADOR":
                atribuidos.setdefault(alvo["atributos"]["nome"], (alvo["linha"], alvo["coluna"]))
        elif tipo == "FUNCAO":
            nome = no["atributos"]["nome"]
            atribuidos.setdefault(nome, (no["linha"], no["coluna"]))
            assinaturas.setdefault(nome, list(no["atributos"]["parametros"]))
        elif tipo == "PARA":
            variavel = _filho(no, "variavel")
            atribuidos.setdefault(variavel["atributos"]["nome"], (variavel["linha"], variavel["coluna"]))
            _coletar(_filho(no, "corpo")["filhos"], atribuidos, assinaturas)
        elif tipo in ("SE", "SENAO_SE", "ENQUANTO"):
            for filho in no["filhos"]:
                if filho["tipo"] in ("BLOCO", "SENAO_SE"):
                    _coletar(filho["filhos"] if filho["tipo"] == "BLOCO" else [filho],
                             atribuidos, assinaturas)


class AnalisadorSemantico:
    def __init__(self, ast, tokens=None):
        self.ast = ast
        self.tokens = tokens or []
        self.erros = []
        self.avisos = []
        self.escopos = []
        self.ordem_simbolos = []
        self.ja_avisado = set()
        self.pendentes = {}   # (escopo, nome) -> usos lidos antes de o símbolo existir
        self.embutido = _Escopo("embutido", "Funções embutidas do Python", "embutido",
                                None, None, {}, {})

    # -- Diagnósticos ---------------------------------------------------------

    def _diagnostico(self, regra, no, mensagem, sugestao="", chave=None):
        if chave is not None:
            if chave in self.ja_avisado:
                return
            self.ja_avisado.add(chave)
        info = REGRAS[regra]
        erro = info["gravidade"] == "erro"
        item = {
            "tipo": "ERRO_SEMANTICO" if erro else "AVISO_SEMANTICO",
            "regra": regra,
            "titulo": info["titulo"],
            **_posicao(no),
            "mensagem": ("Erro semântico" if erro else "Aviso") +
                        f" na linha {no['linha']}, coluna {no['coluna']}: {mensagem}",
            "explicacao": info["explicacao"],
            "sugestao": sugestao,
            "erro_python": info["erro_python"],
            "no_id": no["id"],
        }
        (self.erros if erro else self.avisos).append(item)

    # -- Símbolos -------------------------------------------------------------

    def _novo_simbolo(self, escopo, nome, categoria, tipo, no_posicao, no_id):
        simbolo = {
            "nome": nome,
            "categoria": categoria,
            "tipo": tipo,
            "tipos": [tipo] if tipo != DESCONHECIDO else [],
            "escopo": escopo.nome,
            "escopo_rotulo": escopo.rotulo,
            **(_posicao(no_posicao) if no_posicao else
               {"linha": None, "coluna": None, "linha_fim": None, "coluna_fim": None}),
            "no_id": no_id,
            "inicializado": escopo.tipo != "embutido",
            "usado": False,
            "usos": [],
            "atribuicoes": 0 if escopo.tipo == "embutido" else 1,
        }
        if categoria in ("funcao", "embutida"):
            simbolo["parametros"] = []
            simbolo["retorno"] = DESCONHECIDO
        if escopo.tipo == "funcao":
            for externo in escopo.pai.cadeia():
                if externo.tipo == "embutido":
                    break
                if nome in externo.simbolos or nome in externo.atribuidos:
                    simbolo["sombreia"] = f"{nome} do {externo.rotulo.lower()}"
                    break
        escopo.simbolos[nome] = simbolo
        self.ordem_simbolos.append(simbolo)
        for no in self.pendentes.pop((id(escopo), nome), []):
            self._registrar_uso(simbolo, no)
        return simbolo

    def _definir(self, escopo, nome, tipo, no_nome, no_id, categoria="variavel", no_valor=None):
        simbolo = escopo.simbolos.get(nome)
        if simbolo is None:
            simbolo = self._novo_simbolo(escopo, nome, categoria, tipo, no_nome, no_id)
            if nome in EMBUTIDAS and categoria != "parametro":
                self._diagnostico(
                    "SOMBREIA_EMBUTIDA", no_nome,
                    f"'{nome}' é o nome de uma função embutida do Python; a partir daqui, "
                    f"'{nome}' passa a ser esta {('função' if categoria == 'funcao' else 'variável')}.",
                    f"Use outro nome, como '{nome}_valor' ou 'minha_{nome}'.",
                    chave=("sombra", escopo.nome, nome))
        else:
            simbolo["atribuicoes"] += 1
            anterior = simbolo["tipo"]
            if (tipo != DESCONHECIDO and anterior != DESCONHECIDO and tipo != anterior
                    and not ({tipo, anterior} <= NUMERICOS and "bool" not in {tipo, anterior})):
                self._diagnostico(
                    "MUDANCA_DE_TIPO", no_valor or no_nome,
                    f"'{nome}' era {_nome_tipo(anterior)} e agora recebe um valor do tipo "
                    f"{_nome_tipo(tipo)}.",
                    "Se a mudança não for intencional, use outro nome para o novo valor.",
                    chave=("tipo", escopo.nome, nome, anterior, tipo))
            simbolo["tipo"] = tipo
            if categoria == "funcao":
                simbolo["categoria"] = "funcao"
                simbolo.setdefault("parametros", [])
                simbolo.setdefault("retorno", DESCONHECIDO)
        if tipo != DESCONHECIDO and tipo not in simbolo["tipos"]:
            simbolo["tipos"].append(tipo)
        escopo.certos.add(nome)
        escopo.talvez.discard(nome)
        return simbolo

    def _registrar_uso(self, simbolo, no):
        simbolo["usado"] = True
        simbolo["usos"].append({**_posicao(no), "no_id": no["id"]})

    def _simbolo_embutido(self, nome):
        simbolo = self.embutido.simbolos.get(nome)
        if simbolo is None:
            simbolo = self._novo_simbolo(self.embutido, nome, "embutida", "função", None, None)
            info = EMBUTIDAS[nome]
            simbolo["retorno"] = info["retorno"]
            simbolo["argumentos"] = (f"{info['min']} ou mais" if info["max"] is None else
                                     str(info["min"]) if info["min"] == info["max"] else
                                     f"{info['min']} a {info['max']}")
        return simbolo

    def _nomes_visiveis(self, escopo):
        nomes = set(EMBUTIDAS)
        for e in escopo.cadeia():
            nomes |= set(e.simbolos) | set(e.atribuidos)
        return nomes

    def _sugestao_nome(self, nome, escopo):
        parecidos = difflib.get_close_matches(nome, sorted(self._nomes_visiveis(escopo) - {nome}),
                                              n=1, cutoff=0.7)
        if parecidos:
            return f"Você quis dizer '{parecidos[0]}'?"
        return f"Dê um valor a '{nome}' antes de usá-lo, por exemplo: {nome} = 0."

    # -- Resolução de nomes ---------------------------------------------------

    def _resolver(self, no, ctx):
        """Uso (leitura) de um nome. Devolve o tipo inferido."""
        nome = no["atributos"]["nome"]
        escopo = ctx["escopo"]

        if nome in escopo.atribuidos:
            simbolo = escopo.simbolos.get(nome)
            if nome in escopo.certos:
                pass
            elif nome in escopo.talvez or nome in ctx["nomes_laco"]:
                linha = escopo.atribuidos[nome][0]
                self._diagnostico(
                    "POSSIVELMENTE_NAO_DEFINIDA", no,
                    f"'{nome}' pode não ter valor aqui: ele só recebe valor dentro de um if, de um "
                    f"laço ou mais adiante no laço (linha {linha}).",
                    f"Dê um valor inicial a '{nome}' antes do if ou do laço, por exemplo: {nome} = 0.",
                    chave=("talvez", escopo.nome, nome))
            elif escopo.tipo == "funcao":
                linha = escopo.atribuidos[nome][0]
                global_tambem = any(nome in e.atribuidos for e in escopo.pai.cadeia())
                extra = (f" Por isso o '{nome}' de fora da função não é usado aqui."
                         if global_tambem else "")
                self._diagnostico(
                    "VARIAVEL_LOCAL_SEM_VALOR", no,
                    f"'{nome}' é uma variável local da função '{escopo.nome}' (recebe valor na linha "
                    f"{linha}), mas foi lida antes de receber valor.{extra}",
                    f"Dê um valor a '{nome}' antes de lê-lo dentro da função, ou use outro nome "
                    "para a variável local.",
                    chave=("local", escopo.nome, nome))
                return DESCONHECIDO
            else:
                linha = escopo.atribuidos[nome][0]
                if nome in escopo.assinaturas:
                    texto = (f"a função '{nome}' foi usada, mas só é definida (def) na linha {linha}, "
                             "depois deste uso.")
                    dica = f"Mova a definição de '{nome}' para antes desta linha."
                else:
                    texto = f"'{nome}' foi usado, mas só recebe valor na linha {linha}, depois deste uso."
                    dica = f"Mova a atribuição de '{nome}' para antes desta linha."
                self._diagnostico("IDENTIFICADOR_NAO_DEFINIDO", no, texto, dica,
                                  chave=("nd", escopo.nome, nome))
                return DESCONHECIDO
            if simbolo is not None:
                self._registrar_uso(simbolo, no)
                return simbolo["tipo"]
            return DESCONHECIDO

        # Escopos externos (funções que envolvem esta e o global): o valor é
        # lido quando a função for chamada, então basta existir.
        for externo in escopo.pai.cadeia() if escopo.pai else []:
            if externo.tipo == "embutido":
                break
            if nome in externo.atribuidos:
                simbolo = externo.simbolos.get(nome)
                if simbolo is not None:
                    self._registrar_uso(simbolo, no)
                    return simbolo["tipo"]
                # Definido mais adiante (ex.: função chamada dentro de outra
                # função): o uso é anotado quando o símbolo for criado.
                self.pendentes.setdefault((id(externo), nome), []).append(no)
                return DESCONHECIDO

        if nome in EMBUTIDAS:
            self._registrar_uso(self._simbolo_embutido(nome), no)
            return "função"

        onde = (f"nem na função '{escopo.nome}' nem fora dela" if escopo.tipo == "funcao"
                else "em nenhum ponto do programa")
        self._diagnostico(
            "IDENTIFICADOR_NAO_DEFINIDO", no,
            f"'{nome}' foi usado, mas não recebe valor {onde}.",
            self._sugestao_nome(nome, escopo),
            chave=("nd", escopo.nome, nome))
        return DESCONHECIDO

    def _assinatura(self, nome, escopo):
        for e in escopo.cadeia():
            if e.tipo == "embutido":
                break
            if nome in e.assinaturas:
                return e.assinaturas[nome], e
            if nome in e.atribuidos:
                return None, e
        return None, None

    # -- Expressões -----------------------------------------------------------

    def _expressao(self, no, ctx):
        tipo = no["tipo"]
        if tipo in TIPOS_LITERAIS:
            return TIPOS_LITERAIS[tipo]
        if tipo == "LISTA":
            for f in no["filhos"]:
                self._expressao(f, ctx)
            return "list"
        if tipo == "IDENTIFICADOR":
            return self._resolver(no, ctx)
        if tipo in OPERADORES_ARITMETICOS:
            esquerda = self._expressao(_filho(no, "esquerda"), ctx)
            direita = self._expressao(_filho(no, "direita"), ctx)
            return self._binaria(OPERADORES_ARITMETICOS[tipo], esquerda, direita, no)
        if tipo == "UNARIO":
            operando = self._expressao(_filho(no, "operando"), ctx)
            if operando == DESCONHECIDO:
                return DESCONHECIDO
            if operando not in NUMERICOS:
                op = no["atributos"]["operador"]
                self._diagnostico(
                    "OPERANDO_INVALIDO", no,
                    f"o sinal '{op}' foi aplicado a um valor do tipo {_nome_tipo(operando)}, "
                    "mas só funciona com números.",
                    "Use o sinal apenas com números, ou converta o valor com int(...) ou float(...).")
                return DESCONHECIDO
            return "int" if operando == "bool" else operando
        if tipo == "COMPARACAO":
            return self._comparacao(no, ctx)
        if tipo == "OPERACAO_LOGICA":
            esquerda = self._expressao(_filho(no, "esquerda"), ctx)
            direita = self._expressao(_filho(no, "direita"), ctx)
            return esquerda if esquerda == direita else DESCONHECIDO
        if tipo == "NEGACAO":
            self._expressao(_filho(no, "operando"), ctx)
            return "bool"
        if tipo == "CHAMADA":
            return self._chamada(no, ctx)
        if tipo == "INDEXACAO":
            return self._indexacao(no, ctx)
        if tipo == "ACESSO_ATRIBUTO":
            self._expressao(_filho(no, "objeto"), ctx)
            return DESCONHECIDO
        for f in no["filhos"]:
            self._expressao(f, ctx)
        return DESCONHECIDO

    def _binaria(self, op, esquerda, direita, no):
        if DESCONHECIDO in (esquerda, direita):
            return DESCONHECIDO
        par = {esquerda, direita}
        numericos = esquerda in NUMERICOS and direita in NUMERICOS
        resultado_num = "float" if "float" in par else "int"
        resultado = None
        if numericos:
            resultado = "float" if op == "/" else resultado_num
        elif op == "+" and esquerda == direita and esquerda in ("str", "list"):
            resultado = esquerda
        elif op == "*" and (esquerda in ("str", "list") and direita in ("int", "bool")):
            resultado = esquerda
        elif op == "*" and (direita in ("str", "list") and esquerda in ("int", "bool")):
            resultado = direita
        elif op == "%" and esquerda == "str":
            resultado = "str"
        if resultado is not None:
            return resultado

        e, d = _nome_tipo(esquerda), _nome_tipo(direita)
        if op == "+" and "str" in par and par & NUMERICOS:
            sugestao = ("Para juntar texto e número, converta o número com str(...); para somar, "
                        "converta o texto com int(...) ou float(...).")
        elif op == "*" and "str" in par:
            sugestao = "Um texto só pode ser repetido por um número inteiro, como 'ab' * 3."
        else:
            sugestao = f"Verifique os valores usados com '{op}' e converta-os para tipos compatíveis."
        self._diagnostico(
            "TIPOS_INCOMPATIVEIS", no,
            f"o operador '{op}' não pode ser usado entre {e} e {d}.", sugestao)
        return DESCONHECIDO

    def _comparacao(self, no, ctx):
        op = no["atributos"]["operador"]
        esquerda = self._expressao(_filho(no, "esquerda"), ctx)
        direita = self._expressao(_filho(no, "direita"), ctx)
        if DESCONHECIDO in (esquerda, direita) or op in ("==", "!=", "is", "is not"):
            return "bool"
        if op in ("<", ">", "<=", ">="):
            compativeis = ((esquerda in NUMERICOS and direita in NUMERICOS)
                           or (esquerda == direita and esquerda in ("str", "list")))
            if not compativeis:
                self._diagnostico(
                    "COMPARACAO_INVALIDA", no,
                    f"o operador '{op}' não compara {_nome_tipo(esquerda)} com {_nome_tipo(direita)}.",
                    "Converta os valores para o mesmo tipo antes de comparar, por exemplo "
                    "int(texto) > 10.")
        elif op in ("in", "not in"):
            if direita not in SEQUENCIAS:
                self._diagnostico(
                    "NAO_ITERAVEL", no,
                    f"o operador '{op}' procura um valor dentro de uma coleção, mas o lado direito "
                    f"é do tipo {_nome_tipo(direita)}.",
                    "Use 'in' com um texto, uma lista ou range(...).")
            elif direita == "str" and esquerda != "str":
                self._diagnostico(
                    "TIPOS_INCOMPATIVEIS", no,
                    f"'{op}' com um texto à direita procura um pedaço de texto, mas o lado esquerdo "
                    f"é do tipo {_nome_tipo(esquerda)}.",
                    "Converta o valor da esquerda com str(...).")
        return "bool"

    def _indexacao(self, no, ctx, atribuicao=False):
        objeto = self._expressao(_filho(no, "objeto"), ctx)
        indice = self._expressao(_filho(no, "indice"), ctx)
        if objeto == DESCONHECIDO:
            return DESCONHECIDO
        if objeto not in SEQUENCIAS:
            self._diagnostico(
                "NAO_INDEXAVEL", no,
                f"o valor indexado é do tipo {_nome_tipo(objeto)}, que não tem itens para acessar "
                "com [ ].",
                "Use [ ] apenas com textos, listas ou range(...).")
            return DESCONHECIDO
        if indice not in (DESCONHECIDO, "int", "bool"):
            self._diagnostico(
                "INDICE_INVALIDO", no,
                f"o índice entre [ ] é do tipo {_nome_tipo(indice)}, mas precisa ser um inteiro.",
                "Use um número inteiro como índice, por exemplo v[0], ou converta com int(...).")
        if atribuicao and objeto in ("str", "range"):
            self._diagnostico(
                "ITEM_IMUTAVEL", no,
                f"não é possível alterar um item de um valor do tipo {_nome_tipo(objeto)}.",
                "Monte um novo texto, por exemplo com fatias e +, ou use uma lista.")
        return {"str": "str", "range": "int"}.get(objeto, DESCONHECIDO)

    def _chamada(self, no, ctx):
        alvo = _filho(no, "funcao")
        argumentos = _filhos(no, "argumento")
        tipos_args = [self._expressao(a, ctx) for a in argumentos]
        if alvo is None:
            return DESCONHECIDO
        if alvo["tipo"] != "IDENTIFICADOR":
            self._expressao(alvo, ctx)
            return DESCONHECIDO

        nome = alvo["atributos"]["nome"]
        tipo_alvo = self._resolver(alvo, ctx)
        parametros, escopo_def = self._assinatura(nome, ctx["escopo"])
        total = len(argumentos)

        if parametros is not None:
            if total != len(parametros):
                lista = ", ".join(parametros) or "nenhum"
                self._diagnostico(
                    "ARGUMENTOS_INCORRETOS", no,
                    f"a função '{nome}' espera {len(parametros)} argumento(s) ({lista}), "
                    f"mas recebeu {total}.",
                    f"Passe exatamente {len(parametros)} valor(es) na chamada de '{nome}'.")
            simbolo = escopo_def.simbolos.get(nome)
            return simbolo.get("retorno", DESCONHECIDO) if simbolo else DESCONHECIDO

        if escopo_def is None and nome in EMBUTIDAS:
            info = EMBUTIDAS[nome]
            if total < info["min"] or (info["max"] is not None and total > info["max"]):
                if info["max"] is None:
                    faixa = f"pelo menos {info['min']}"
                elif info["min"] == info["max"]:
                    faixa = f"exatamente {info['min']}"
                else:
                    faixa = f"de {info['min']} a {info['max']}"
                self._diagnostico(
                    "ARGUMENTOS_INCORRETOS", no,
                    f"a função embutida '{nome}' aceita {faixa} argumento(s), mas recebeu {total}.",
                    f"Confira quantos valores '{nome}(...)' precisa.")
            elif nome == "len" and tipos_args and tipos_args[0] in NAO_ITERAVEIS:
                self._diagnostico(
                    "ARGUMENTO_INVALIDO", no,
                    f"len() conta os itens de um texto ou lista, mas recebeu um valor do tipo "
                    f"{_nome_tipo(tipos_args[0])}.",
                    "Passe um texto ou uma lista para len().")
            elif nome == "range":
                for tipo in tipos_args:
                    if tipo not in (DESCONHECIDO, "int", "bool"):
                        self._diagnostico(
                            "ARGUMENTO_INVALIDO", no,
                            f"range() precisa de números inteiros, mas recebeu um valor do tipo "
                            f"{_nome_tipo(tipo)}.",
                            "Converta o valor com int(...).")
                        break
            return info["retorno"]

        if tipo_alvo not in (DESCONHECIDO, "função"):
            self._diagnostico(
                "NAO_CHAMAVEL", no,
                f"'{nome}' é um valor do tipo {_nome_tipo(tipo_alvo)} e não pode ser chamado com "
                "( ) como uma função.",
                f"Verifique se '{nome}' deveria ser uma função, ou retire os parênteses.")
        return DESCONHECIDO

    # -- Comandos -------------------------------------------------------------

    def _bloco(self, bloco, ctx):
        for comando in bloco["filhos"]:
            self._comando(comando, ctx)

    def _nomes_atribuidos(self, comandos):
        atribuidos = {}
        _coletar(comandos, atribuidos, {})
        return set(atribuidos)

    def _comando(self, no, ctx):
        tipo = no["tipo"]
        escopo = ctx["escopo"]

        if tipo == "ATRIBUICAO":
            self._atribuicao(no, ctx)
        elif tipo == "COMANDO_EXPRESSAO":
            for f in no["filhos"]:
                self._expressao(f, ctx)
        elif tipo == "SE":
            self._se(no, ctx)
        elif tipo == "ENQUANTO":
            self._expressao(_filho(no, "condicao"), ctx)
            self._laco(_filho(no, "corpo"), ctx)
        elif tipo == "PARA":
            iteravel = self._expressao(_filho(no, "iteravel"), ctx)
            variavel = _filho(no, "variavel")
            nome = variavel["atributos"]["nome"]
            if iteravel in NAO_ITERAVEIS:
                self._diagnostico(
                    "NAO_ITERAVEL", _filho(no, "iteravel"),
                    f"o for percorre os itens de uma coleção, mas recebeu um valor do tipo "
                    f"{_nome_tipo(iteravel)}.",
                    "Para repetir um número de vezes, use range(...), por exemplo: "
                    "for i in range(10):")
            tipo_var = {"str": "str", "range": "int"}.get(iteravel, DESCONHECIDO)
            self._laco(_filho(no, "corpo"), ctx, variavel=(nome, tipo_var, variavel))
        elif tipo == "FUNCAO":
            self._funcao(no, ctx)
        elif tipo == "RETORNO":
            valor = _filho(no, "valor")
            tipo_valor = self._expressao(valor, ctx) if valor is not None else "None"
            if escopo.tipo != "funcao":
                self._diagnostico(
                    "RETORNO_FORA_DE_FUNCAO", no,
                    "o comando return aparece fora de uma função.",
                    "Coloque o return dentro de uma função (def), ou retire-o.")
            else:
                escopo.retornos.append(tipo_valor)
        elif tipo in ("INTERROMPE", "CONTINUA"):
            if ctx["laco"] == 0:
                palavra = "break" if tipo == "INTERROMPE" else "continue"
                self._diagnostico(
                    "FORA_DE_LACO", no,
                    f"o comando {palavra} aparece fora de um laço while ou for.",
                    f"Use {palavra} apenas dentro do corpo de um while ou de um for.")
        elif tipo == "BLOCO":
            self._bloco(no, ctx)

    def _atribuicao(self, no, ctx):
        escopo = ctx["escopo"]
        alvo = _filho(no, "alvo")
        valor = _filho(no, "valor")
        op = no["atributos"]["operador"]
        tipo_valor = self._expressao(valor, ctx)

        if alvo["tipo"] == "INDEXACAO":
            self._indexacao(alvo, ctx, atribuicao=True)
            return

        nome = alvo["atributos"]["nome"]
        if op != "=":
            ja_tem = (nome in escopo.certos or nome in escopo.talvez or nome in ctx["nomes_laco"]
                      or (nome not in escopo.atribuidos and self._visivel_fora(nome, escopo)))
            if not ja_tem and escopo.tipo == "funcao" and self._visivel_fora(nome, escopo):
                self._resolver(alvo, ctx)   # variável local lida antes de receber valor
                tipo_valor = DESCONHECIDO
            elif not ja_tem:
                self._diagnostico(
                    "ATRIBUICAO_COMPOSTA_SEM_VALOR", alvo,
                    f"'{nome} {op} ...' lê o valor atual de '{nome}', mas '{nome}' ainda não "
                    "recebeu valor.",
                    f"Dê um valor inicial antes, por exemplo: {nome} = 0.",
                    chave=("nd", escopo.nome, nome))
                tipo_valor = DESCONHECIDO
            else:
                tipo_atual = self._resolver(alvo, ctx)
                tipo_valor = self._binaria(op[:-1], tipo_atual, tipo_valor, no)
        self._definir(escopo, nome, tipo_valor, alvo, alvo["id"], no_valor=valor)

    def _visivel_fora(self, nome, escopo):
        if nome in EMBUTIDAS:
            return True
        return any(nome in e.atribuidos for e in (escopo.pai.cadeia() if escopo.pai else []))

    def _se(self, no, ctx):
        escopo = ctx["escopo"]
        antes = set(escopo.certos)
        resultados = []

        self._expressao(_filho(no, "condicao"), ctx)
        ramos = [_filho(no, "entao")]
        for senao_se in _filhos(no, "senao_se"):
            ramos.append(senao_se)
        senao = _filho(no, "senao")
        if senao is not None:
            ramos.append(senao)

        for ramo in ramos:
            escopo.certos = set(antes)
            if ramo["tipo"] == "SENAO_SE":
                self._expressao(_filho(ramo, "condicao"), ctx)
                self._bloco(_filho(ramo, "entao"), ctx)
            else:
                self._bloco(ramo, ctx)
            resultados.append(set(escopo.certos))

        uniao = set().union(*resultados)
        if senao is not None:
            escopo.certos = set.intersection(*resultados) | antes
        else:
            escopo.certos = set(antes)
        escopo.talvez |= uniao - escopo.certos

    def _laco(self, corpo, ctx, variavel=None):
        escopo = ctx["escopo"]
        antes = set(escopo.certos)
        nomes = self._nomes_atribuidos(corpo["filhos"])
        interno = dict(ctx, laco=ctx["laco"] + 1, nomes_laco=ctx["nomes_laco"] | nomes)
        if variavel is not None:
            nome, tipo, no_var = variavel
            self._definir(escopo, nome, tipo, no_var, no_var["id"])
        self._bloco(corpo, interno)
        depois = set(escopo.certos)
        escopo.certos = antes
        escopo.talvez |= depois - antes

    def _funcao(self, no, ctx):
        escopo = ctx["escopo"]
        nome = no["atributos"]["nome"]
        posicao_nome = self._posicao_nome_funcao(no)
        simbolo = self._definir(escopo, nome, "função", posicao_nome, no["id"], categoria="funcao")
        parametros = _filhos(no, "parametro")
        simbolo["parametros"] = [p["atributos"]["nome"] for p in parametros]

        corpo = _filho(no, "corpo")
        atribuidos = {}
        assinaturas = {}
        for p in parametros:
            atribuidos.setdefault(p["atributos"]["nome"], (p["linha"], p["coluna"]))
        _coletar(corpo["filhos"], atribuidos, assinaturas)
        novo = _Escopo(nome, f"Função {nome}", "funcao", escopo, no, atribuidos, assinaturas)
        self.escopos.append(novo)

        vistos = set()
        for p in parametros:
            nome_p = p["atributos"]["nome"]
            if nome_p in vistos:
                self._diagnostico(
                    "PARAMETRO_DUPLICADO", p,
                    f"o parâmetro '{nome_p}' aparece mais de uma vez na função '{nome}'.",
                    "Dê um nome diferente a cada parâmetro.")
                continue
            vistos.add(nome_p)
            self._definir(novo, nome_p, DESCONHECIDO, p, p["id"], categoria="parametro")

        self._bloco(corpo, {"escopo": novo, "laco": 0, "nomes_laco": frozenset()})

        tipos = set(novo.retornos) or {"None"}
        simbolo["retorno"] = tipos.pop() if len(tipos) == 1 else DESCONHECIDO

    def _posicao_nome_funcao(self, no):
        """Posição do nome da função (o nó FUNCAO começa no 'def')."""
        nome = no["atributos"]["nome"]
        viu_def = False
        for t in self.tokens:
            if (t["linha"], t["coluna"]) < (no["linha"], no["coluna"]):
                continue
            if t["tipo"] == "PALAVRA_RESERVADA" and t["lexema"] == "def":
                viu_def = True
            elif viu_def and t["tipo"] == "IDENTIFICADOR" and t["lexema"] == nome:
                return {"linha": t["linha"], "coluna": t["coluna"], "linha_fim": t["linha"],
                        "coluna_fim": t["coluna"] + len(nome) - 1, "id": no["id"]}
            if viu_def and t["linha"] > no["linha"]:
                break
        return {"linha": no["linha"], "coluna": no["coluna"], "linha_fim": no["linha"],
                "coluna_fim": no["coluna"] + 2, "id": no["id"]}

    # -- Entrada --------------------------------------------------------------

    def analisar(self):
        atribuidos, assinaturas = {}, {}
        _coletar(self.ast["filhos"], atribuidos, assinaturas)
        global_ = _Escopo("global", "Escopo global", "global", self.embutido, self.ast,
                          atribuidos, assinaturas)
        self.escopos.append(global_)
        self._bloco(self.ast, {"escopo": global_, "laco": 0, "nomes_laco": frozenset()})
        if self.embutido.simbolos:
            self.escopos.append(self.embutido)

        ordem_escopo = {e.nome: i for i, e in enumerate(self.escopos)}
        tabela = sorted(self.ordem_simbolos,
                        key=lambda s: (ordem_escopo.get(s["escopo"], 99), s["linha"] or 0, s["coluna"] or 0))
        chave = lambda d: (d["linha"], d["coluna"])
        self.erros.sort(key=chave)
        self.avisos.sort(key=chave)

        escopos = [{
            "nome": e.nome,
            "rotulo": e.rotulo,
            "tipo": e.tipo,
            "pai": e.pai.nome if e.pai and e.tipo != "global" else None,
            "linha": e.no["linha"] if e.no else None,
            "coluna": e.no["coluna"] if e.no else None,
            "no_id": e.no["id"] if e.no else None,
            "total_simbolos": len(e.simbolos),
        } for e in self.escopos]

        return {
            "sucesso": not self.erros,
            "tabela_simbolos": tabela,
            "escopos": escopos,
            "erros": self.erros,
            "avisos": self.avisos,
            "resumo": {
                "total_simbolos": len(tabela),
                "total_erros": len(self.erros),
                "total_avisos": len(self.avisos),
                "por_categoria": {c: sum(1 for s in tabela if s["categoria"] == c)
                                  for c in ("variavel", "funcao", "parametro", "embutida")},
            },
        }


def analisar_semanticamente(ast, tokens=None):
    """Percorre a AST e devolve a tabela de símbolos, os erros e os avisos."""
    return AnalisadorSemantico(ast, tokens).analisar()
