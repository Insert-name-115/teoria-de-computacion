import unittest

from lexer import analizar
from modelos import ErrorLexico, ResultadoLexico, Token
from tabla_lexemas import TablaLexemas


class ModelosYTablaTests(unittest.TestCase):
    def test_token_usa_formato_solicitado(self):
        token = Token("ATOMO", "padre", 2, 1, 0)
        self.assertEqual(str(token), "<ATOMO, 'padre', 2, 1, atributo=0>")

    def test_resultado_informa_si_es_valido(self):
        resultado = ResultadoLexico(TablaLexemas())
        self.assertTrue(resultado.es_valido)

        resultado.errores.append(ErrorLexico("CARACTER", "No admitido", 1, 1, "@"))
        self.assertFalse(resultado.es_valido)

    def test_tabla_reutiliza_el_indice_de_un_duplicado(self):
        tabla = TablaLexemas()
        primero = tabla.registrar("ATOMO", "padre")
        repetido = tabla.registrar("ATOMO", "padre")

        self.assertEqual(primero, repetido)
        self.assertEqual(len(tabla), 1)

    def test_tabla_distingue_tipos(self):
        tabla = TablaLexemas()
        atomo = tabla.registrar("ATOMO", "dato")
        cadena = tabla.registrar("CADENA", "dato")

        self.assertNotEqual(atomo, cadena)
        self.assertEqual(len(tabla), 2)


class LexerBaseTests(unittest.TestCase):
    def test_analiza_clausula_completa_con_posiciones(self):
        resultado = analizar("padre(X, ana).")

        self.assertTrue(resultado.es_valido)
        self.assertEqual(
            [token.tipo for token in resultado.tokens],
            [
                "ATOMO",
                "PARENTESIS_IZQ",
                "VARIABLE",
                "COMA",
                "ATOMO",
                "PARENTESIS_DER",
                "PUNTO",
            ],
        )
        self.assertEqual(
            [(token.linea, token.columna) for token in resultado.tokens],
            [(1, 1), (1, 6), (1, 7), (1, 8), (1, 10), (1, 13), (1, 14)],
        )

    def test_ignora_comentario_linea_y_actualiza_posicion(self):
        resultado = analizar("% comentario\npadre.")

        self.assertEqual([token.lexema for token in resultado.tokens], ["padre", "."])
        self.assertEqual(
            (resultado.tokens[0].linea, resultado.tokens[0].columna), (2, 1)
        )

    def test_ignora_comentario_bloque_multilinea(self):
        resultado = analizar("a /* uno\n dos */ b")

        self.assertEqual([token.lexema for token in resultado.tokens], ["a", "b"])
        self.assertEqual(
            (resultado.tokens[1].linea, resultado.tokens[1].columna), (2, 9)
        )

    def test_prioridad_de_palabras_reservadas(self):
        resultado = analizar("is isa mod modulo")

        self.assertEqual(
            [token.tipo for token in resultado.tokens],
            ["OP_IS", "ATOMO", "OP_MOD", "ATOMO"],
        )

    def test_variable_anonima_y_variable_normal(self):
        resultado = analizar("_ _Temporal __")

        self.assertEqual(
            [token.tipo for token in resultado.tokens],
            ["VARIABLE_ANONIMA", "VARIABLE", "VARIABLE"],
        )
        self.assertIsNone(resultado.tokens[0].atributo)

    def test_aplica_maxima_coincidencia_en_operadores(self):
        resultado = analizar("\\== \\= == =.. = :- ?- --> // ** \\+")

        self.assertEqual(
            [token.tipo for token in resultado.tokens],
            [
                "OP_NO_IDENTICO",
                "OP_NO_UNIFICA",
                "OP_IDENTICO",
                "OP_UNIV",
                "OP_UNIFICA",
                "OP_REGLA",
                "OP_CONSULTA",
                "OP_DCG",
                "OP_DIV_ENTERA",
                "OP_POTENCIA",
                "OP_NEGACION",
            ],
        )

    def test_asigna_valores_a_numeros(self):
        resultado = analizar("25 3.14")

        self.assertEqual(resultado.tokens[0].atributo, 25)
        self.assertEqual(resultado.tokens[1].atributo, 3.14)

    def test_reutiliza_indices_de_atom_y_variable(self):
        resultado = analizar("padre(padre, X, X).")
        atomos = [token for token in resultado.tokens if token.lexema == "padre"]
        variables = [token for token in resultado.tokens if token.lexema == "X"]

        self.assertEqual(atomos[0].atributo, atomos[1].atributo)
        self.assertEqual(variables[0].atributo, variables[1].atributo)
        self.assertEqual(len(resultado.tabla_lexemas), 2)

    def test_registra_atom_y_cadena_entre_comillas(self):
        resultado = analizar("'Juan Perez' \"hola\"")

        self.assertEqual(
            [token.tipo for token in resultado.tokens],
            ["ATOMO_COMILLAS", "CADENA"],
        )
        self.assertEqual(len(resultado.tabla_lexemas), 2)

    def test_caracter_desconocido_genera_error_y_continua(self):
        resultado = analizar("a @ b")

        self.assertEqual([token.lexema for token in resultado.tokens], ["a", "b"])
        self.assertEqual(len(resultado.errores), 1)
        self.assertEqual(resultado.errores[0].fragmento, "@")
        self.assertEqual(
            (resultado.errores[0].linea, resultado.errores[0].columna), (1, 3)
        )

    def test_crlf_cuenta_como_un_salto_de_linea(self):
        resultado = analizar("a\r\nb")

        self.assertEqual(
            [(token.linea, token.columna) for token in resultado.tokens],
            [(1, 1), (2, 1)],
        )


if __name__ == "__main__":
    unittest.main()
