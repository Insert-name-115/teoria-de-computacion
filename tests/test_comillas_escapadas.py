"""Comillas escapadas ('' y "") seguidas de un texto sin cierre."""

import unittest

from lexer import analizar


def errores(resultado):
    return [(e.tipo, e.linea, e.columna, e.fragmento) for e in resultado.errores]


def lexemas(resultado):
    return [t.lexema for t in resultado.tokens]


class ComillasEscapadasSinCierre(unittest.TestCase):
    def test_cadena_con_comilla_doble_escapada_sin_cierre(self):
        r = analizar('"a""b')
        self.assertEqual(errores(r), [("CADENA_SIN_CIERRE", 1, 1, '"a""b')])
        self.assertEqual(r.tokens, [])

    def test_atomo_con_comilla_simple_escapada_sin_cierre(self):
        for texto in ["'a''b", "'it''s"]:
            with self.subTest(texto=texto):
                r = analizar(texto)
                self.assertEqual(errores(r), [("ATOMO_SIN_CIERRE", 1, 1, texto)])
                self.assertEqual(r.tokens, [])

    def test_termina_justo_despues_de_la_comilla_escapada(self):
        self.assertEqual(errores(analizar('"a""')), [("CADENA_SIN_CIERRE", 1, 1, '"a""')])
        self.assertEqual(errores(analizar("'a''")), [("ATOMO_SIN_CIERRE", 1, 1, "'a''")])

    def test_se_recupera_en_la_linea_siguiente_con_posiciones_correctas(self):
        r = analizar('x("a""b).\ny.')
        self.assertEqual(errores(r), [("CADENA_SIN_CIERRE", 1, 3, '"a""b).')])
        self.assertEqual(lexemas(r), ["x", "(", "y", "."])
        y = [t for t in r.tokens if t.lexema == "y"][0]
        self.assertEqual((y.linea, y.columna), (2, 1))

    def test_las_cadenas_cerradas_con_comilla_escapada_siguen_siendo_validas(self):
        for texto, esperado in [('"a""b"', '"a""b"'), ("'a''b'", "'a''b'"), ('"a"""', '"a"""')]:
            with self.subTest(texto=texto):
                r = analizar(texto)
                self.assertTrue(r.es_valido)
                self.assertEqual(lexemas(r), [esperado])

    def test_dos_cadenas_separadas_no_se_confunden(self):
        r = analizar('"a" "b"')
        self.assertTrue(r.es_valido)
        self.assertEqual(lexemas(r), ['"a"', '"b"'])


if __name__ == "__main__":
    unittest.main()
