TOKENS = [
    ("ATOMO", "minúscula + letras, dígitos o _", ["padre", "persona_1"], ["Padre", "1abc"], "índice tabla de lexemas"),
    ("ATOMO_COMILLAS", "texto entre comillas simples", ["'Juan Pérez'", "':-'"], ["'sin cierre"], "índice tabla de lexemas"),
    ("VARIABLE", "mayúscula, o _ + al menos un carácter", ["X", "Persona", "_Temporal"], ["persona", "1X"], "índice tabla de lexemas"),
    ("VARIABLE_ANONIMA", "solo el guion bajo", ["_"], ["__"], "-"),
    ("ENTERO", "uno o más dígitos", ["25", "0"], ["-5", "2a"], "valor (int)"),
    ("REAL", "dígitos . dígitos", ["3.14", "0.5"], ["3.", ".5"], "valor (float)"),
    ("CADENA", "texto entre comillas dobles", ['"hola"', '"di \\"si\\""'], ['"sin cierre'], "índice tabla de lexemas"),
    ("COMENTARIO_LINEA", "% hasta fin de línea (se ignora)", ["% Hechos"], ["Hechos %"], "-"),
    ("COMENTARIO_BLOQUE", "/* hasta el primer */ (se ignora)", ["/* hola */"], ["/* sin cierre"], "-"),
    ("ESPACIO", "espacios, tabs y saltos (se ignora)", [" ", "\t", "\n"], ["x"], "-"),
    # Categorías de operadores (el token exacto de cada lexema está en OPERADORES)
    ("OP_IS, OP_MOD", "is  mod", ["is", "mod"], ["IS", "isa"], "-"),
    ("OP_CLAUSULA", ":-  ?-  -->", [":-", "?-", "-->"], [":", "?", "--"], "-"),
    ("OP_COMPARACION", "=  \\=  ==  \\==  =..  <  =<  >  >=", ["\\==", "=..", "=<"], ["=.", "<>"], "-"),
    ("OP_ARITMETICO", "+  -  *  /  //  **", ["+", "//", "**"], ["***"], "-"),
    ("OP_CONTROL", "\\+  !  ;  ,", ["\\+", "!", ";", ","], ["\\"], "-"),
    ("DELIMITADOR", "(  )  [  ]  {  }  |  .", ["(", "]", "."], ["..", "()"], "-"),
]

# Átomos que funcionan como operadores (misma forma que ATOMO)
PALABRAS_RESERVADAS = {"is": "OP_IS", "mod": "OP_MOD"}

# Operadores y delimitadores: el patrón es el mismo lexema
OPERADORES = {
    ":-": "OP_REGLA", "?-": "OP_CONSULTA", "-->": "OP_DCG",
    "=": "OP_UNIFICA", "\\=": "OP_NO_UNIFICA", "==": "OP_IDENTICO", "\\==": "OP_NO_IDENTICO",
    "=..": "OP_UNIV", "<": "OP_MENOR", "=<": "OP_MENOR_IGUAL", ">": "OP_MAYOR", ">=": "OP_MAYOR_IGUAL",
    "+": "OP_SUMA", "-": "OP_RESTA", "*": "OP_MULT", "/": "OP_DIV", "//": "OP_DIV_ENTERA", "**": "OP_POTENCIA",
    "\\+": "OP_NEGACION", "!": "CORTE", ";": "PUNTO_Y_COMA", ",": "COMA",
    "(": "PARENTESIS_IZQ", ")": "PARENTESIS_DER", "[": "CORCHETE_IZQ", "]": "CORCHETE_DER",
    "{": "LLAVE_IZQ", "}": "LLAVE_DER", "|": "BARRA", ".": "PUNTO",
}


def mostrar_especificacion():
    print(f"{'Token':<18} {'Patrón':<38} {'Válidos':<28} {'Inválidos':<22} Atributo")
    for token, patron, validos, invalidos, atributo in TOKENS:
        validos = ", ".join(repr(v) if v.isspace() else v for v in validos)  # repr muestra ' ', '\t', '\n'
        print(f"{token:<18} {patron:<38} {validos:<28} {', '.join(invalidos):<22} {atributo}")

    # Palabras reservadas y operadores (lexemas fijos)
    for lexema, token in {**PALABRAS_RESERVADAS, **OPERADORES}.items():
        print(f"{token:<18} {lexema}")
