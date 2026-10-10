import re
from especificacion_prolog import OPERADORES

# El orden del diccionario es la prioridad: is y mod van antes que ATOMO
EXPRESIONES = {
    "OP_IS": r"is",
    "OP_MOD": r"mod",
    "ATOMO": r"[a-z][a-zA-Z0-9_]*",
    "ATOMO_COMILLAS": r"'([^'\\\n]|\\[^\n]|'')*'",
    "VARIABLE": r"_[a-zA-Z0-9_]+|[A-Z][a-zA-Z0-9_]*",
    "VARIABLE_ANONIMA": r"_",
    "ENTERO": r"[0-9]+",
    "REAL": r"[0-9]+\.[0-9]+",
    "CADENA": r'"([^"\\\n]|\\[^\n]|"")*"',
    "COMENTARIO_LINEA": r"%[^\n]*",
    "COMENTARIO_BLOQUE": r"/\*[^*]*\*+([^*/][^*]*\*+)*/",
    "ESPACIO": r"[ \t\r\n]+",
}

# Operadores: la ER es el lexema con los símbolos especiales escapados
for lexema, token in OPERADORES.items():
    EXPRESIONES[token] = re.escape(lexema)


def reconocer_er(texto, inicio=0):
    token_elegido, lexema_elegido = None, ""
    for token, er in EXPRESIONES.items():
        m = re.compile(er).match(texto, inicio)
        # '>' estricto: si empatan, se queda la que apareció primero
        if m and len(m.group()) > len(lexema_elegido):
            token_elegido, lexema_elegido = token, m.group()
    return token_elegido, lexema_elegido
