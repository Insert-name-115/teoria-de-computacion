from dataclasses import dataclass
import graphviz
from especificacion_prolog import OPERADORES, PALABRAS_RESERVADAS

ESPECIALES = {"_": "guion_bajo", " ": "espacio", "\t": "espacio", "\r": "espacio", "\n": "salto",
              "'": "comilla_simple", '"': "comilla_doble", "\\": "barra_inv", "%": "porcentaje"}
SIMBOLOS = set(":?->=.<+*/!;,()[]{}|")
ALFABETO = {"minuscula", "mayuscula", "digito", "otro"} | set(ESPECIALES.values()) | SIMBOLOS
LETRA_DIGITO = ["minuscula", "mayuscula", "digito", "guion_bajo"]


def clase_de(c):
    """Traduce un carácter a su símbolo del alfabeto."""
    if c.isascii() and c.isalpha():
        return "minuscula" if c.islower() else "mayuscula"
    if c.isascii() and c.isdigit():
        return "digito"
    return ESPECIALES.get(c, c if c in SIMBOLOS else "otro")  # otro = @, #, é, ñ, ...


def todos_menos(*simbolos):
    return ALFABETO - set(simbolos)


@dataclass
class AFD:
    nombre: str
    transiciones: dict
    aceptacion: dict
    inicial: str = "Inicio"

    def reconocer(self, texto, inicio=0):
        """Máxima coincidencia: guarda el último estado de aceptación visto."""
        actual, token, fin = self.inicial, None, inicio
        for i in range(inicio, len(texto)):
            actual = self.transiciones.get((actual, clase_de(texto[i])))
            if actual is None:
                break
            if actual in self.aceptacion:
                token, fin = self.aceptacion[actual], i + 1
        lexema = texto[inicio:fin]
        # Palabras reservadas: se reconocen como ATOMO y luego se buscan en la tabla
        if token == "ATOMO" and lexema in PALABRAS_RESERVADAS:
            token = PALABRAS_RESERVADAS[lexema]
        return token, lexema


# AFD ATOMO:  Inicio --minuscula--> Atomo --letra|digito|_--> Atomo
afd_atomo = AFD("ATOMO", {
    ("Inicio", "minuscula"): "Atomo",
    **{("Atomo", s): "Atomo" for s in LETRA_DIGITO},
}, {"Atomo": "ATOMO"})

# AFD VARIABLE:  Inicio --_--> Anonima --letra|digito|_--> Variable;  Inicio --mayuscula--> Variable
afd_variable = AFD("VARIABLE", {
    ("Inicio", "guion_bajo"): "Anonima",
    ("Inicio", "mayuscula"): "Variable",
    **{("Anonima", s): "Variable" for s in LETRA_DIGITO},
    **{("Variable", s): "Variable" for s in LETRA_DIGITO},
}, {"Anonima": "VARIABLE_ANONIMA", "Variable": "VARIABLE"})

# AFD NUMERO:  Inicio --digito--> Entero --.--> EnteroPunto --digito--> Real
afd_numero = AFD("NUMERO", {
    ("Inicio", "digito"): "Entero",
    ("Entero", "digito"): "Entero",
    ("Entero", "."): "EnteroPunto",
    ("EnteroPunto", "digito"): "Real",
    ("Real", "digito"): "Real",
}, {"Entero": "ENTERO", "Real": "REAL"})


# AFD con comillas (sirve para ATOMO_COMILLAS y CADENA):
#   Inicio --C--> Abierto --C--> Cerrado (acepta) --C--> Abierto ('' dentro del texto)
#   Abierto --\--> Escape --cualquiera--> Abierto
def afd_comillas(nombre, comilla, p):
    return AFD(nombre, {
        ("Inicio", comilla): p + "Abierto",
        **{(p + "Abierto", s): p + "Abierto" for s in todos_menos(comilla, "barra_inv", "salto")},
        (p + "Abierto", "barra_inv"): p + "Escape",
        **{(p + "Escape", s): p + "Abierto" for s in todos_menos("salto")},
        (p + "Abierto", comilla): p + "Cerrado",
        (p + "Cerrado", comilla): p + "Abierto",
    }, {p + "Cerrado": nombre})


afd_atomo_comillas = afd_comillas("ATOMO_COMILLAS", "comilla_simple", "AC_")
afd_cadena = afd_comillas("CADENA", "comilla_doble", "CAD_")

# AFD COMENTARIO_LINEA:  Inicio --%--> ComLinea --todo menos salto--> ComLinea
afd_comentario_linea = AFD("COMENTARIO_LINEA", {
    ("Inicio", "porcentaje"): "ComLinea",
    **{("ComLinea", s): "ComLinea" for s in todos_menos("salto")},
}, {"ComLinea": "COMENTARIO_LINEA"})

# AFD COMENTARIO_BLOQUE:  Inicio --/--> / --*--> Dentro --*--> Asterisco --/--> Cerrado
# (el estado "/" lo comparte con el AFD de operadores, donde acepta OP_DIV)
afd_comentario_bloque = AFD("COMENTARIO_BLOQUE", {
    ("Inicio", "/"): "/",
    ("/", "*"): "CB_Dentro",
    **{("CB_Dentro", s): "CB_Dentro" for s in todos_menos("*")},
    ("CB_Dentro", "*"): "CB_Asterisco",
    ("CB_Asterisco", "*"): "CB_Asterisco",
    **{("CB_Asterisco", s): "CB_Dentro" for s in todos_menos("*", "/")},
    ("CB_Asterisco", "/"): "CB_Cerrado",
}, {"CB_Cerrado": "COMENTARIO_BLOQUE"})

# AFD ESPACIO:  Inicio --espacio|salto--> Espacio --espacio|salto--> Espacio
afd_espacio = AFD("ESPACIO", {
    ("Inicio", "espacio"): "Espacio", ("Inicio", "salto"): "Espacio",
    ("Espacio", "espacio"): "Espacio", ("Espacio", "salto"): "Espacio",
}, {"Espacio": "ESPACIO"})

# AFD OPERADORES: árbol de prefijos generado desde OPERADORES.
# Cada estado se llama como lo leído hasta ahora ("=", "=.", "=..").
# Acepta si lo leído es un operador completo; ":", "?", "--", "=." y "\\" no aceptan.
transiciones_operadores = {}
for lexema in OPERADORES:
    for i, c in enumerate(lexema):
        transiciones_operadores[(lexema[:i] or "Inicio", clase_de(c))] = lexema[:i + 1]
afd_operadores = AFD("OPERADORES", transiciones_operadores, dict(OPERADORES))

AFDS = [afd_atomo, afd_variable, afd_numero, afd_atomo_comillas, afd_cadena,
        afd_comentario_linea, afd_comentario_bloque, afd_espacio, afd_operadores]

# AFD INTEGRADO: todos comparten el estado "Inicio" y salen de él con símbolos
# distintos (salvo '/', que lleva al estado compartido "/"), así que basta
# con juntar sus tablas para obtener un solo AFD.
afd_integrado = AFD("INTEGRADO", {k: v for a in AFDS for k, v in a.transiciones.items()},
                    {k: v for a in AFDS for k, v in a.aceptacion.items()})


# -------------------------------------------------------------------
# Función para visualizar: 'dibujar_afd' dibuja el grafo del AFD con Graphviz.
# -------------------------------------------------------------------
def dibujar_afd(afd):
    dot = graphviz.Digraph(afd.nombre)
    dot.attr(rankdir="LR")
    dot.node("", shape="point")  # nodo invisible para flecha inicial

    # Dibujar estados (doble círculo si es de aceptación)
    estados = {afd.inicial} | {e for e, _ in afd.transiciones} | set(afd.transiciones.values())
    for s in sorted(estados):  # ordenados: el .dot sale igual en cada ejecución
        e = graphviz.escape(s)  # escapa la barra invertida de estados como "\="
        if s in afd.aceptacion:
            dot.node(e, e + "\\n" + afd.aceptacion[s], shape="doublecircle")
        else:
            dot.node(e, shape="circle")

    # Flecha al estado inicial
    dot.edge("", afd.inicial)

    # Agrupar símbolos por (origen, destino)
    etiquetas = {}
    for (src, sym), dst in afd.transiciones.items():
        etiquetas.setdefault((src, dst), []).append(sym)

    for (src, dst), syms in etiquetas.items():
        # Si son casi todos los símbolos, se escribe "todo menos ..." para acortar
        if len(syms) > 8:
            label = "todo menos " + ", ".join(sorted(ALFABETO - set(syms)))
        else:
            label = ", ".join(sorted(syms))
        dot.edge(graphviz.escape(src), graphviz.escape(dst), label=label)

    return dot
