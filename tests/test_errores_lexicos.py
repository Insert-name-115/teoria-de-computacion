import unittest
from pathlib import Path

from lexer import analizar
from main import main

CORPUS = Path(__file__).resolve().parents[1] / "corpus"
ARCHIVO_VALIDO = CORPUS / "programa_valido.pl"
ARCHIVO_INVALIDO = CORPUS / "programa_con_errores.pl"


def errores(resultado):
    # Retorna Errores como lista de (tipo, linea, columna, fragmento).
    return [(e.tipo, e.linea, e.columna, e.fragmento) for e in resultado.errores]


def lexemas(resultado):
    # Retorna los lexemas de los tokens validos que se conservaron
    return [t.lexema for t in resultado.tokens]


class ErroresIndividuales(unittest.TestCase):
    # (nombre, texto, error esperado, tokens que tienen que quedar)
    CASOS = [
        ("atomo sin cierre", "dato('sin cierre",
         ("ATOMO_SIN_CIERRE", 1, 6, "'sin cierre"), ["dato", "("]),
        ("cadena sin cierre", 'msg("hola mundo',
         ("CADENA_SIN_CIERRE", 1, 5, '"hola mundo'), ["msg", "("]),
        ("comentario sin cierre", "a. /* sin cierre\nsigue",
         ("COMENTARIO_BLOQUE_SIN_CIERRE", 1, 4, "/* sin cierre"), ["a", "."]),
        ("caracter @", "x @ y",
         ("CARACTER_NO_ADMITIDO", 1, 3, "@"), ["x", "y"]),
        ("otro caracter en otra linea", "a.\nb $ c.",
         ("CARACTER_NO_ADMITIDO", 2, 3, "$"), ["a", ".", "b", "c", "."]),
        ("numero unido a letras", "edad(123abc).",
         ("NUMERO_MAL_FORMADO", 1, 6, "123abc"), ["edad", "(", ")", "."]),
        ("real sin parte entera", "x = .5.",
         ("NUMERO_MAL_FORMADO", 1, 5, ".5"), ["x", "=", "."]),
        ("mas de un punto", "v(12.3.4).",
         ("NUMERO_MAL_FORMADO", 1, 3, "12.3.4"), ["v", "(", ")", "."]),
    ]

    def test_un_solo_error_y_tokens_validos_se_conservan(self):
        for nombre, texto, error, tokens in self.CASOS:
            with self.subTest(caso=nombre):
                resultado = analizar(texto)
                self.assertEqual(errores(resultado), [error])
                self.assertEqual(lexemas(resultado), tokens)
                self.assertFalse(resultado.es_valido)


class Recuperacion(unittest.TestCase):
    def test_atomo_sin_cierre_se_recupera_en_la_linea_siguiente(self):
        resultado = analizar("a('x\nb.")
        self.assertEqual(errores(resultado), [("ATOMO_SIN_CIERRE", 1, 3, "'x")])
        posiciones = [(t.lexema, t.linea, t.columna) for t in resultado.tokens]
        self.assertEqual(posiciones, [("a", 1, 1), ("(", 1, 2), ("b", 2, 1), (".", 2, 2)])

    def test_comentario_sin_cierre_consume_hasta_el_final(self):
        resultado = analizar("a.\n/* abierto\nb.\nc.\n")
        self.assertEqual(errores(resultado),
                         [("COMENTARIO_BLOQUE_SIN_CIERRE", 2, 1, "/* abierto")])
        self.assertEqual(lexemas(resultado), ["a", "."])

    def test_caracter_no_admitido_consume_solo_ese_caracter(self):
        resultado = analizar("a @@ b")
        self.assertEqual(len(resultado.errores), 2)
        self.assertEqual(lexemas(resultado), ["a", "b"])

    def test_errores_salen_en_orden(self):
        resultado = analizar("@ 'x\n12ab ?\n")
        self.assertEqual([e.tipo for e in resultado.errores],
                         ["CARACTER_NO_ADMITIDO", "ATOMO_SIN_CIERRE",
                          "NUMERO_MAL_FORMADO", "CARACTER_NO_ADMITIDO"])

    def test_siempre_termina_con_entradas_invalidas(self):
        for texto in ["'" * 501, '"' * 501, "/*" * 500, "@" * 500, "1a" * 500, ".5" * 500]:
            resultado = analizar(texto)
            self.assertTrue(resultado.errores)


class ConvencionNumerica(unittest.TestCase):
    # un punto es PUNTO (fin de clausula) salvo que quede pegado a un digito.

    def test_numeros_mal_formados(self):
        for texto in ["123abc", "2a", "3.14x", "12.3.4", ".5"]:
            with self.subTest(texto=texto):
                resultado = analizar(texto)
                self.assertEqual(errores(resultado), [("NUMERO_MAL_FORMADO", 1, 1, texto)])
                self.assertEqual(resultado.tokens, [])

    def test_doble_punto(self):
        resultado = analizar("3..4")
        self.assertEqual(lexemas(resultado), ["3", "."])
        self.assertEqual(errores(resultado), [("NUMERO_MAL_FORMADO", 1, 3, ".4")])

    def test_punto_final_de_clausula_no_es_error(self):
        self.assertEqual(lexemas(analizar("3.")), ["3", "."])
        self.assertEqual(lexemas(analizar("valor(3).")), ["valor", "(", "3", ")", "."])
        self.assertTrue(analizar("X = 3.14.").es_valido)


class ArchivoConErrores(unittest.TestCase):
    ESPERADOS = [
        ("NUMERO_MAL_FORMADO", 3, 11, "123abc"),
        ("ATOMO_SIN_CIERRE", 4, 18, "'Juan Perez."),
        ("CADENA_SIN_CIERRE", 5, 8, '"hola mundo).'),
        ("NUMERO_MAL_FORMADO", 6, 18, ".5"),
        ("NUMERO_MAL_FORMADO", 7, 17, "12.3.4"),
        ("CARACTER_NO_ADMITIDO", 8, 16, "@"),
        ("CARACTER_NO_ADMITIDO", 9, 18, "#"),
        ("COMENTARIO_BLOQUE_SIN_CIERRE", 10, 1, "/* comentario que nunca se cierra"),
    ]

    @classmethod
    def setUpClass(cls):
        cls.resultado = analizar(ARCHIVO_INVALIDO.read_text(encoding="utf-8"))

    def test_informa_exactamente_los_errores_esperados(self):
        self.assertEqual(errores(self.resultado), self.ESPERADOS)

    def test_conserva_tokens_validos_despues_de_cada_error(self):
        validos = lexemas(self.resultado)
        for lexema in ["valido", "listo", "ok", "fin"]:
            self.assertIn(lexema, validos)

    def test_nada_se_reconoce_despues_del_comentario_sin_cierre(self):
        self.assertTrue(all(t.linea < 10 for t in self.resultado.tokens))


class SalidaDeMain(unittest.TestCase):
    def test_codigo_de_salida(self):
        self.assertEqual(main([str(ARCHIVO_INVALIDO)]), 1)
        self.assertEqual(main([str(ARCHIVO_VALIDO)]), 0)


if __name__ == "__main__":
    unittest.main()
