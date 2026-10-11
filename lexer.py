"""Lexer completo basado en el AFD integrado del proyecto."""

from AFDS import afd_integrado, clase_de
from modelos import ErrorLexico, ResultadoLexico, Token
from tabla_lexemas import TablaLexemas

TIPOS_IGNORADOS = {"ESPACIO", "COMENTARIO_LINEA", "COMENTARIO_BLOQUE"}
TIPOS_CON_INDICE = {"ATOMO", "ATOMO_COMILLAS", "VARIABLE", "CADENA"}

# Tipos de error lexico que produce el analizador
ATOMO_SIN_CIERRE = "ATOMO_SIN_CIERRE"
CADENA_SIN_CIERRE = "CADENA_SIN_CIERRE"
COMENTARIO_SIN_CIERRE = "COMENTARIO_BLOQUE_SIN_CIERRE"
NUMERO_MAL_FORMADO = "NUMERO_MAL_FORMADO"
CARACTER_NO_ADMITIDO = "CARACTER_NO_ADMITIDO"

MENSAJES = {
    ATOMO_SIN_CIERRE: "Atomo entre comillas simples sin cierre; se descarta hasta el final de la linea.",
    CADENA_SIN_CIERRE: "Cadena entre comillas dobles sin cierre; se descarta hasta el final de la linea.",
    COMENTARIO_SIN_CIERRE: "Comentario de bloque sin cierre; se descarta hasta el final del archivo.",
    NUMERO_MAL_FORMADO: "Numero mal formado; se descarta el fragmento numerico completo.",
    CARACTER_NO_ADMITIDO: "El caracter no pertenece al subconjunto lexico definido.",
}

MAXIMO_FRAGMENTO = 40

def _avanzar_posicion(texto, inicio, fin, linea, columna):
    """Actualiza la posicion despues de consumir texto[inicio:fin].

    LF, CR y CRLF cuentan como un solo salto de linea. El salto de CRLF se cuenta
    en el LF, asi no importa si CR y LF quedaron en lexemas distintos (por ejemplo,
    un comentario de linea termina justo antes del LF pero incluye el CR).
    """
    for j in range(inicio, fin):
        caracter = texto[j]
        if caracter == "\n":
            linea += 1
            columna = 1
        elif caracter == "\r" and not (j + 1 < len(texto) and texto[j + 1] == "\n"):
            linea += 1
            columna = 1
        else:
            columna += 1
    return linea, columna


def _atributo_para(tipo, lexema, tabla):
    if tipo in TIPOS_CON_INDICE:
        return tabla.registrar(tipo, lexema)
    if tipo == "ENTERO":
        return int(lexema)
    if tipo == "REAL":
        return float(lexema)
    return None

def _resumir(fragmento):
    """Fragmento que se informa: solo la primera linea y, si es muy larga, recortada."""
    primera = fragmento.splitlines()[0] if fragmento.splitlines() else fragmento
    if len(primera) > MAXIMO_FRAGMENTO:
        return primera[:MAXIMO_FRAGMENTO] + "..."
    return primera


def _fin_de_linea(texto, posicion):
    """Indice del primer salto de linea (LF o CR) desde posicion, o el final del texto."""
    for i in range(posicion, len(texto)):
        if texto[i] in "\r\n":
            return i
    return len(texto)


def _es_digito(texto, i):
    return i < len(texto) and clase_de(texto[i]) == "digito"


def _es_letra_o_guion_bajo(texto, i):
    return i < len(texto) and clase_de(texto[i]) in ("minuscula", "mayuscula", "guion_bajo")


def _fin_fragmento_numerico(texto, i):
    """Desde i, avanza sobre letras, digitos, _ y puntos seguidos de digito.

    Sirve para consumir completo un numero mal formado como 123abc o 12.3.4.
    """
    while i < len(texto):
        if _es_letra_o_guion_bajo(texto, i) or _es_digito(texto, i):
            i += 1
        elif texto[i] == "." and _es_digito(texto, i + 1):
            i += 1
        else:
            break
    return i


def _diagnosticar(texto, posicion, tipo, lexema):
    """Decide si lo reconocido en posicion es un error.

    Devuelve None si el token es valido, o (tipo_de_error, cuantos_caracteres_saltar).
    Siempre salta al menos un caracter, asi el analisis nunca se queda en el mismo lugar.
    """
    # Comentario de bloque: el AFD solo lo acepta si esta cerrado
    if texto.startswith("/*", posicion) and tipo != "COMENTARIO_BLOQUE":
        return COMENTARIO_SIN_CIERRE, len(texto) - posicion

    # El AFD no pudo avanzar
    if tipo is None or not lexema:
        caracter = texto[posicion]
        if caracter == "'":
            return ATOMO_SIN_CIERRE, _fin_de_linea(texto, posicion) - posicion
        if caracter == '"':
            return CADENA_SIN_CIERRE, _fin_de_linea(texto, posicion) - posicion
        return CARACTER_NO_ADMITIDO, 1

    # Numero valido seguido de letra, _ o de otro .digito (25abc, 2a, 12.3.4)
    if tipo in ("ENTERO", "REAL"):
        fin = posicion + len(lexema)
        if _es_letra_o_guion_bajo(texto, fin) or (
            fin < len(texto) and texto[fin] == "." and _es_digito(texto, fin + 1)
        ):
            return NUMERO_MAL_FORMADO, _fin_fragmento_numerico(texto, fin) - posicion

    # Punto pegado a un digito sin parte entera antes (.5)
    if tipo == "PUNTO" and _es_digito(texto, posicion + 1):
        return NUMERO_MAL_FORMADO, _fin_fragmento_numerico(texto, posicion + 1) - posicion

    return None


def analizar(texto):
    """Recorre ``texto`` completo y devuelve sus tokens y errores en orden.

    Los espacios y comentarios no se incluyen en la salida, pero actualizan la
    posicion. Cuando hay un error lexico se informa una sola vez, se salta el
    fragmento problematico y el analisis continua con lo que sigue:

    - atomo o cadena sin cierre: se salta hasta el final de la linea;
    - comentario de bloque sin cierre: se salta hasta el final del archivo;
    - numero mal formado: se salta el fragmento numerico completo;
    - caracter no admitido: se salta solo ese caracter.
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

        diagnostico = _diagnosticar(texto, posicion, tipo, lexema)
        if diagnostico is not None:
            tipo_error, longitud = diagnostico
            longitud = max(1, longitud)
            fragmento = texto[posicion:posicion + longitud]
            resultado.errores.append(
                ErrorLexico(
                    tipo=tipo_error,
                    mensaje=MENSAJES[tipo_error],
                    linea=linea_inicio,
                    columna=columna_inicio,
                    fragmento=_resumir(fragmento),
                )
            )
            linea, columna = _avanzar_posicion(texto, posicion, posicion + longitud, linea, columna)
            posicion += longitud
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

        linea, columna = _avanzar_posicion(texto, posicion, posicion + len(lexema), linea, columna)
        posicion += len(lexema)

    return resultado
