import graphviz
from AFDS import AFD, afd_integrado, dibujar_afd, LETRA_DIGITO

ALF = LETRA_DIGITO
EPS = "ε"

# AFN con transiciones ε:  (estado, símbolo) -> lista de estados
#   q1-q2: ATOMO   q3-q4: _   q5-q6-q7: _L+   q8-q9: [A-Z]L*
afn = {("q0", EPS): ["q1", "q3", "q5", "q8"]}
afn[("q1", "minuscula")] = ["q2"]
afn[("q3", "guion_bajo")] = ["q4"]
afn[("q5", "guion_bajo")] = ["q6"]
afn[("q8", "mayuscula")] = ["q9"]
for s in ALF:
    afn[("q2", s)] = ["q2"]
    afn[("q6", s)] = ["q7"]
    afn[("q7", s)] = ["q7"]
    afn[("q9", s)] = ["q9"]
afn_aceptacion = {"q2": "ATOMO", "q4": "VARIABLE_ANONIMA", "q7": "VARIABLE", "q9": "VARIABLE"}


def clausura(estados):
    """Estados alcanzables con transiciones ε (incluye los propios)."""
    resultado = list(estados)
    for q in resultado:                       
        for t in afn.get((q, EPS), []):
            if t not in resultado:
                resultado.append(t)
    return tuple(sorted(resultado, key=lambda q: int(q[1:])))


def mover(conjunto, simbolo):
    return [t for q in conjunto for t in afn.get((q, simbolo), [])]


def token_de(conjunto):
    for q in conjunto:
        if q in afn_aceptacion:
            return afn_aceptacion[q]
    return None


# Construcción de subconjuntos 
inicial = clausura(["q0"])
subconjuntos = [inicial]                      # cada subconjunto será un estado A0, A1, ...
trans_sub = {}                                # (subconjunto, símbolo) -> subconjunto
for sub in subconjuntos:                      # también crece mientras se recorre
    for s in ALF:
        destino = mover(sub, s)
        if destino:
            nuevo = clausura(destino)
            trans_sub[(sub, s)] = nuevo
            if nuevo not in subconjuntos:
                subconjuntos.append(nuevo)

nombre = {sub: "A" + str(i) for i, sub in enumerate(subconjuntos)}
afd_sub = AFD("AFD_SUBCONJUNTOS",
              {(nombre[a], s): nombre[b] for (a, s), b in trans_sub.items()},
              {nombre[sub]: token_de(sub) for sub in subconjuntos if token_de(sub)},
              inicial=nombre[inicial])

print("Clausura-ε(q0) =", inicial)
print("\nTabla de subconjuntos")
for sub in subconjuntos:
    print(nombre[sub], sub, token_de(sub))
    for s in ALF:
        if (sub, s) in trans_sub:
            print("    ", s, "->", nombre[trans_sub[(sub, s)]])

# Minimización 
# Se empieza agrupando los estados por token. Luego se separan los que,
# con algún símbolo, van a bloques distintos. Se repite hasta que no cambie nada.
estados = list(nombre.values())                      # A0, A1, A2, A3, A4
tokens = []                                          # un bloque por cada token distinto
for e in estados:
    if afd_sub.aceptacion.get(e) not in tokens:
        tokens.append(afd_sub.aceptacion.get(e))
bloque = {e: tokens.index(afd_sub.aceptacion.get(e)) for e in estados}
print("\nPartición inicial (bloque de cada estado):", bloque)

while True:
    firmas = {}
    nuevo_bloque = {}
    for e in estados:
        firma = (bloque[e],) + tuple(bloque.get(afd_sub.transiciones.get((e, s))) for s in ALF)
        firmas.setdefault(firma, len(firmas))
        nuevo_bloque[e] = firmas[firma]
    if len(firmas) == len(set(bloque.values())):
        break                                 
    bloque = nuevo_bloque

grupos = {}
for e in estados:
    grupos.setdefault(bloque[e], []).append(e)
print("Estados equivalentes:", list(grupos.values()))

# AFD mínimo: un estado "M#" por cada bloque
mmin = {e: "M" + str(bloque[e]) for e in estados}
afd_min = AFD("AFD_MINIMO",
              {(mmin[a], s): mmin[b] for (a, s), b in afd_sub.transiciones.items()},
              {mmin[e]: t for e, t in afd_sub.aceptacion.items()},
              inicial=mmin[afd_sub.inicial])

# El AFD mínimo debe reconocer lo mismo que el AFD integrado
for texto in ["padre", "persona_1", "X", "Persona", "_Temporal", "_", "_X", "__", "isa", "Z9_"]:
    print(f"{texto!r:<12} mínimo: {afd_min.reconocer(texto)}   integrado: {afd_integrado.reconocer(texto)}")


# Dibujos 
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


dibujar_afn("AFN", afn, afn_aceptacion, "q0").save("automatas/afn_ejemplo.dot")
for a in [afd_sub, afd_min]:
    dibujar_afd(a).save(f"automatas/{a.nombre.lower()}.dot")
print("Diagramas guardados en automatas/")
