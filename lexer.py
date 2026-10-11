"""Lexer completo basado en el AFD integrado del proyecto."""

from AFDS import afd_integrado
from modelos import ErrorLexico, ResultadoLexico, Token
from tabla_lexemas import TablaLexemas


TIPOS_IGNORADOS = {"ESPACIO", "COMENTARIO_LINEA", "COMENTARIO_BLOQUE"}
TIPOS_CON_INDICE = {"ATOMO", "ATOMO_COMILLAS", "VARIABLE", "CADENA"}


def _avanzar_posicion(fragmento, linea, columna):
    """Actualiza una posicion considerando LF, CR y CRLF como saltos."""
    i = 0
    while i < len(fragmento):
        caracter = fragmento[i]
        if caracter == "\r":
            if i + 1 < len(fragmento) and fragmento[i + 1] == "\n":
                i += 1
            linea += 1
            columna = 1
        elif caracter == "\n":
            linea += 1
            columna = 1
        else:
            columna += 1
        i += 1
    return linea, columna


def _atributo_para(tipo, lexema, tabla):
    if tipo in TIPOS_CON_INDICE:
        return tabla.registrar(tipo, lexema)
    if tipo == "ENTERO":
        return int(lexema)
    if tipo == "REAL":
        return float(lexema)
    return None


def analizar(texto):
    """Recorre ``texto`` completo y devuelve sus tokens en orden.

    Los espacios y comentarios no se incluyen en la salida, pero actualizan la
    posicion. En esta etapa base, una posicion no reconocida genera un error
    ``CARACTER_NO_ADMITIDO`` de un caracter y el recorrido continua. Los
    diagnosticos especializados quedan para la siguiente etapa del proyecto.
    """
    tabla = TablaLexemas()
    resultado = ResultadoLexico(tabla)
    posicion = 0
    linea = 1
    columna = 1

    while posicion < len(texto):
        linea_inicio = linea
        columna_inicio = columna
        tipo, lexema = afd_integrado.reconocer(texto, posicion)

        if tipo is None or not lexema:
            fragmento = texto[posicion]
            resultado.errores.append(
                ErrorLexico(
                    tipo="CARACTER_NO_ADMITIDO",
                    mensaje="El caracter no pertenece al subconjunto lexico definido.",
                    linea=linea_inicio,
                    columna=columna_inicio,
                    fragmento=fragmento,
                )
            )
            posicion += 1
            linea, columna = _avanzar_posicion(fragmento, linea, columna)
            continue

        if tipo not in TIPOS_IGNORADOS:
            atributo = _atributo_para(tipo, lexema, tabla)
            resultado.tokens.append(
                Token(
                    tipo=tipo,
                    lexema=lexema,
                    linea=linea_inicio,
                    columna=columna_inicio,
                    atributo=atributo,
                )
            )

        posicion += len(lexema)
        linea, columna = _avanzar_posicion(lexema, linea, columna)

    return resultado
