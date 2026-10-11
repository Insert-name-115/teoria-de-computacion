"""Determinizacion (subconjuntos) y minimizacion de un AFN representativo.

El AFN reconoce ATOMO, VARIABLE_ANONIMA y VARIABLE con transiciones epsilon.
Importar este modulo solo define funciones y constantes: no imprime nada ni
crea archivos. Todo el trabajo ocurre en ``ejecutar_determinizacion()``.

AFD parcial (sin estado trampa)
-------------------------------
Los AFD de este proyecto son parciales: una transicion que no existe significa
"rechazar" y equivale a ir a un estado trampa implicito que no se dibuja.
La minimizacion respeta esa lectura: al comparar dos estados, una transicion
ausente cuenta como un destino propio (``None``) distinto de cualquier bloque.
Asi dos estados solo se unen si aceptan el mismo token y, para cada simbolo,
van a bloques equivalentes o ambos rechazan. El resultado es el mismo AFD minimo
que se obtendria agregando la trampa y quitandola despues.
"""

from dataclasses import dataclass, field
from pathlib import Path

import graphviz

from AFDS import AFD, LETRA_DIGITO, afd_integrado, dibujar_afd

# Las rutas se calculan desde este archivo, no desde el directorio actual.
CARPETA_PROYECTO = Path(__file__).resolve().parent
CARPETA_AUTOMATAS = CARPETA_PROYECTO / "automatas"

EPS = "ε"

# Alfabeto del AFN: solo estos simbolos tienen transiciones.
ALFABETO_AFN = tuple(LETRA_DIGITO)

# Cadenas con las que se comprueba que el AFD minimo coincide con el integrado:
# atomos, variables y variable anonima.
CADENAS_COMPARACION = (
    "padre", "a", "persona_1", "x9_", "isa", "modulo",
    "X", "Persona", "A_1", "_Temporal", "Z9_",
    "_", "_X", "__", "_1",
)


def construir_afn():
    """Devuelve ``(transiciones, aceptacion)`` del AFN, siempre como objetos nuevos.

    transiciones: (estado, simbolo) -> lista de estados.
    aceptacion:   estado -> token.

    q1-q2: ATOMO   q3-q4: _   q5-q6-q7: _L+   q8-q9: [A-Z]L*
    """
    transiciones = {("q0", EPS): ["q1", "q3", "q5", "q8"]}
    transiciones[("q1", "minuscula")] = ["q2"]
    transiciones[("q3", "guion_bajo")] = ["q4"]
    transiciones[("q5", "guion_bajo")] = ["q6"]
    transiciones[("q8", "mayuscula")] = ["q9"]
    for simbolo in ALFABETO_AFN:
        transiciones[("q2", simbolo)] = ["q2"]
        transiciones[("q6", simbolo)] = ["q7"]
        transiciones[("q7", simbolo)] = ["q7"]
        transiciones[("q9", simbolo)] = ["q9"]
    aceptacion = {"q2": "ATOMO", "q4": "VARIABLE_ANONIMA", "q7": "VARIABLE", "q9": "VARIABLE"}
    return transiciones, aceptacion


def clausura(transiciones, estados):
    """Estados alcanzables con transiciones epsilon (incluye los propios)."""
    resultado = list(estados)
    for q in resultado:  # la lista crece mientras se recorre
        for t in transiciones.get((q, EPS), []):
            if t not in resultado:
                resultado.append(t)
    return tuple(sorted(resultado, key=lambda q: int(q[1:])))


def mover(transiciones, conjunto, simbolo):
    return [t for q in conjunto for t in transiciones.get((q, simbolo), [])]


def token_de(aceptacion, conjunto):
    """Token que acepta un subconjunto, o None si ninguno de sus estados acepta."""
    for q in conjunto:
        if q in aceptacion:
            return aceptacion[q]
    return None


def dibujar_afn(nombre_afn, transiciones, aceptacion, ini):
    dot = graphviz.Digraph(nombre_afn)
    dot.attr(rankdir="LR")
    dot.node("", shape="point")
    estados_afn = {ini} | {e for e, _ in transiciones} | {d for ds in transiciones.values() for d in ds}
    for q in sorted(estados_afn):
        if q in aceptacion:
            dot.node(q, q + "\\n" + aceptacion[q], shape="doublecircle")
        else:
            dot.node(q, shape="circle")
    dot.edge("", ini)
    etiquetas = {}
    for (src, sym), destinos in transiciones.items():
        for dst in destinos:
            etiquetas.setdefault((src, dst), []).append(sym)
    for (src, dst), syms in etiquetas.items():
        dot.edge(src, dst, label=", ".join(sorted(syms)))
    return dot


def determinizar(transiciones, aceptacion, inicial="q0"):
    """Construccion de subconjuntos. Devuelve (subconjuntos, trans_sub, nombres, afd)."""
    q_inicial = clausura(transiciones, [inicial])
    subconjuntos = [q_inicial]  # cada subconjunto sera un estado A0, A1, ...
    trans_sub = {}  # (subconjunto, simbolo) -> subconjunto
    for sub in subconjuntos:  # tambien crece mientras se recorre
        for s in ALFABETO_AFN:
            destino = mover(transiciones, sub, s)
            if destino:
                nuevo = clausura(transiciones, destino)
                trans_sub[(sub, s)] = nuevo
                if nuevo not in subconjuntos:
                    subconjuntos.append(nuevo)

    nombres = {sub: "A" + str(i) for i, sub in enumerate(subconjuntos)}
    afd = AFD(
        "AFD_SUBCONJUNTOS",
        {(nombres[a], s): nombres[b] for (a, s), b in trans_sub.items()},
        {nombres[sub]: token_de(aceptacion, sub) for sub in subconjuntos if token_de(aceptacion, sub)},
        inicial=nombres[q_inicial],
    )
    return subconjuntos, trans_sub, nombres, afd


def minimizar(afd):
    """Minimiza un AFD parcial. Devuelve (afd_minimo, grupos, particiones).

    Se empieza agrupando los estados por token (los que no aceptan forman un
    bloque aparte). Luego se separan los que, con algun simbolo, van a bloques
    distintos; una transicion ausente cuenta como destino ``None``. Se repite
    hasta que la particion no cambia. ``particiones`` guarda cada ronda como
    lista de grupos, para poder mostrarla en el informe.
    """
    estados = sorted({afd.inicial} | {e for e, _ in afd.transiciones} | set(afd.transiciones.values()),
                     key=lambda e: int(e[1:]))
    tokens = []  # un bloque por cada token distinto
    for e in estados:
        if afd.aceptacion.get(e) not in tokens:
            tokens.append(afd.aceptacion.get(e))
    bloque = {e: tokens.index(afd.aceptacion.get(e)) for e in estados}

    def agrupar(asignacion):
        grupos = {}
        for e in estados:
            grupos.setdefault(asignacion[e], []).append(e)
        return list(grupos.values())

    particiones = [agrupar(bloque)]
    while True:
        firmas = {}
        nuevo_bloque = {}
        for e in estados:
            firma = (bloque[e],) + tuple(bloque.get(afd.transiciones.get((e, s))) for s in ALFABETO_AFN)
            firmas.setdefault(firma, len(firmas))
            nuevo_bloque[e] = firmas[firma]
        if len(firmas) == len(set(bloque.values())):
            break  # ya no se separo ningun estado
        bloque = nuevo_bloque
        particiones.append(agrupar(bloque))

    grupos = agrupar(bloque)
    minimo = {e: "M" + str(bloque[e]) for e in estados}
    afd_minimo = AFD(
        "AFD_MINIMO",
        {(minimo[a], s): minimo[b] for (a, s), b in afd.transiciones.items()},
        {minimo[e]: t for e, t in afd.aceptacion.items()},
        inicial=minimo[afd.inicial],
    )
    return afd_minimo, grupos, particiones


def comparar_con_integrado(afd_minimo, cadenas=CADENAS_COMPARACION):
    """Lista de (texto, resultado_minimo, resultado_integrado)."""
    return [(t, afd_minimo.reconocer(t), afd_integrado.reconocer(t)) for t in cadenas]


@dataclass
class ResultadoDeterminizacion:
    """Todo lo que produce la determinizacion y la minimizacion."""

    afn: tuple  # (transiciones, aceptacion)
    subconjuntos: list
    nombre_subconjunto: dict  # subconjunto -> "A0", "A1", ...
    transiciones_subconjuntos: dict
    afd_subconjuntos: AFD
    afd_minimo: AFD
    grupos_equivalentes: list
    particiones: list
    comparaciones: list  # (texto, resultado_minimo, resultado_integrado)
    coincide_con_integrado: bool
    archivos: list = field(default_factory=list)  # rutas de los DOT guardados


def calcular_determinizacion():
    """Determiniza, minimiza y compara con el AFD integrado. No imprime ni escribe archivos.

    El AFN se construye en cada llamada, asi que no hay variables globales modificables.
    """
    transiciones, aceptacion = construir_afn()
    subconjuntos, trans_sub, nombres, afd_sub = determinizar(transiciones, aceptacion)
    afd_min, grupos, particiones = minimizar(afd_sub)
    comparaciones = comparar_con_integrado(afd_min)
    return ResultadoDeterminizacion(
        afn=(transiciones, aceptacion),
        subconjuntos=subconjuntos,
        nombre_subconjunto=nombres,
        transiciones_subconjuntos=trans_sub,
        afd_subconjuntos=afd_sub,
        afd_minimo=afd_min,
        grupos_equivalentes=grupos,
        particiones=particiones,
        comparaciones=comparaciones,
        coincide_con_integrado=all(minimo == integrado for _, minimo, integrado in comparaciones),
    )


def mostrar_determinizacion(r):
    """Imprime la tabla de subconjuntos, las particiones y la comparacion."""
    transiciones, aceptacion = r.afn
    print("Clausura-epsilon(q0) =", r.subconjuntos[0])
    print("\nTabla de subconjuntos")
    for sub in r.subconjuntos:
        print(r.nombre_subconjunto[sub], sub, token_de(aceptacion, sub))
        for s in ALFABETO_AFN:
            if (sub, s) in r.transiciones_subconjuntos:
                print("    ", s, "->", r.nombre_subconjunto[r.transiciones_subconjuntos[(sub, s)]])
    print("\nParticiones de la minimización")
    for i, particion in enumerate(r.particiones):
        print(f"  ronda {i}:", particion)
    print("Estados equivalentes:", r.grupos_equivalentes)
    print("\nAFD parcial: una transición ausente rechaza (estado trampa implícito).")
    print("\nComparación del AFD mínimo con el AFD integrado")
    for texto, minimo, integrado in r.comparaciones:
        print(f"{texto!r:<12} mínimo: {minimo}   integrado: {integrado}")
    print("Coinciden:", "sí" if r.coincide_con_integrado else "NO")


def ejecutar_determinizacion(carpeta_salida=None, imprimir=True, guardar=True):
    """Calcula la determinizacion, la muestra y guarda los tres diagramas DOT.

    carpeta_salida: donde guardar (por defecto ``CARPETA_AUTOMATAS``, que se lee en
                    cada llamada; la carpeta se crea si no existe).
    imprimir:       muestra las tablas por pantalla.
    guardar:        escribe los archivos DOT.

    Devuelve un ``ResultadoDeterminizacion``; ``archivos`` lista los DOT guardados.
    """
    r = calcular_determinizacion()
    if imprimir:
        mostrar_determinizacion(r)

    if guardar:
        carpeta = Path(carpeta_salida) if carpeta_salida is not None else CARPETA_AUTOMATAS
        carpeta.mkdir(parents=True, exist_ok=True)
        transiciones, aceptacion = r.afn
        destinos = [(dibujar_afn("AFN", transiciones, aceptacion, "q0"), "afn_ejemplo.dot")]
        destinos += [(dibujar_afd(a), f"{a.nombre.lower()}.dot") for a in (r.afd_subconjuntos, r.afd_minimo)]
        for dot, nombre in destinos:
            ruta = carpeta / nombre
            dot.save(str(ruta))
            r.archivos.append(ruta)
        if imprimir:
            print(f"Diagramas guardados en {carpeta}")
    return r
