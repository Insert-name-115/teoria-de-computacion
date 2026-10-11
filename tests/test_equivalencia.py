"""Equivalencia entre las expresiones regulares y el AFD integrado.

Para cada entrada valida, reconocer_er() y afd_integrado.reconocer() deben
devolver el mismo tipo de token y el mismo lexema.
"""

import itertools
import unittest

from AFDS import afd_integrado
from especificacion_prolog import OPERADORES
from expresiones_regulares import reconocer_er


class EquivalenciaBase(unittest.TestCase):
    def comparar(self, texto, tipo, lexema=None):
        """Ambos mecanismos deben dar (tipo, lexema) y coincidir con lo esperado."""
        lexema = texto if lexema is None else lexema
        esperado = (tipo, lexema)
        self.assertEqual(reconocer_er(texto), esperado, f"ER con {texto!r}")
        self.assertEqual(afd_integrado.reconocer(texto), esperado, f"AFD con {texto!r}")


class CategoriasValidas(EquivalenciaBase):
    CASOS = [
        ("ATOMO", ["padre", "persona_1", "a", "x9_Z"]),
        ("ATOMO_COMILLAS", ["'Juan Perez'", "':-'", "''", "'it''s'", "'a\\'b'", "'a b'"]),
        ("VARIABLE", ["X", "Persona", "_Temporal", "Z9_", "_1"]),
        ("VARIABLE_ANONIMA", ["_"]),
        ("ENTERO", ["0", "25", "007"]),
        ("REAL", ["3.14", "0.5", "10.001"]),
        ("CADENA", ['"hola"', '"di \\"si\\""', '""', '"a ""b"""']),
        ("COMENTARIO_LINEA", ["% Hechos", "%", "% a 'b' \"c\""]),
        ("COMENTARIO_BLOQUE", ["/* hola */", "/**/", "/* a * b */", "/***/", "/* x\ny */"]),
        ("ESPACIO", [" ", "\t", "\n", " \t\r\n "]),
    ]

    def test_todas_las_categorias(self):
        for tipo, ejemplos in self.CASOS:
            for texto in ejemplos:
                with self.subTest(tipo=tipo, texto=texto):
                    self.comparar(texto, tipo)


class Operadores(EquivalenciaBase):
    def test_todos_los_operadores_definidos(self):
        for lexema, tipo in OPERADORES.items():
            with self.subTest(operador=lexema):
                self.comparar(lexema, tipo)

    def test_operador_seguido_de_otro_caracter_toma_el_lexema_completo(self):
        for lexema, tipo in OPERADORES.items():
            with self.subTest(operador=lexema):
                self.comparar(lexema + " x", tipo, lexema)


class AtomosOperadores(EquivalenciaBase):
    def test_is_y_mod_son_operadores(self):
        self.comparar("is", "OP_IS")
        self.comparar("mod", "OP_MOD")

    def test_isa_y_modulo_son_atomos(self):
        self.comparar("isa", "ATOMO")
        self.comparar("modulo", "ATOMO")

    def test_is_dentro_de_un_atomo_mas_largo(self):
        self.comparar("is_x", "ATOMO")
        self.comparar("mod2", "ATOMO")
        self.comparar("Is", "VARIABLE")


class Variables(EquivalenciaBase):
    def test_guion_bajo_solo_es_anonima(self):
        self.comparar("_", "VARIABLE_ANONIMA")

    def test_guion_bajo_con_letra_es_variable(self):
        self.comparar("_X", "VARIABLE")

    def test_doble_guion_bajo_es_variable(self):
        self.comparar("__", "VARIABLE")


class Numeros(EquivalenciaBase):
    def test_enteros_y_reales_validos(self):
        for texto in ["0", "7", "123", "0.0", "3.14", "100.25"]:
            with self.subTest(texto=texto):
                self.comparar(texto, "REAL" if "." in texto else "ENTERO")

    def test_punto_final_no_forma_parte_del_numero(self):
        self.comparar("3.", "ENTERO", "3")
        self.comparar("3.a", "ENTERO", "3")

    def test_real_toma_el_lexema_mas_largo(self):
        self.comparar("3.14.", "REAL", "3.14")
        self.comparar("3.14.5", "REAL", "3.14")


class ComentariosYTextos(EquivalenciaBase):
    def test_comentario_de_bloque_se_cierra_en_el_primer_cierre(self):
        self.comparar("/* a */ b */", "COMENTARIO_BLOQUE", "/* a */")

    def test_comentario_de_linea_termina_antes_del_salto(self):
        self.comparar("% hola\nx", "COMENTARIO_LINEA", "% hola")

    def test_atomo_y_cadena_con_escape_no_se_cortan(self):
        self.comparar("'a\\'b' c", "ATOMO_COMILLAS", "'a\\'b'")
        self.comparar('"a\\"b" c', "CADENA", '"a\\"b"')

    def test_comilla_duplicada_sigue_dentro_del_texto(self):
        self.comparar("'a''b' c", "ATOMO_COMILLAS", "'a''b'")


class PrioridadYMaximaCoincidencia(EquivalenciaBase):
    def test_no_identico_frente_a_no_unifica(self):
        self.comparar("\\==", "OP_NO_IDENTICO")
        self.comparar("\\=", "OP_NO_UNIFICA")
        self.comparar("\\=x", "OP_NO_UNIFICA", "\\=")

    def test_univ_frente_a_unifica(self):
        self.comparar("=..", "OP_UNIV")
        self.comparar("=", "OP_UNIFICA")
        self.comparar("=.a", "OP_UNIFICA", "=")

    def test_dcg_frente_a_resta(self):
        self.comparar("-->", "OP_DCG")
        self.comparar("-", "OP_RESTA")
        self.comparar("--", "OP_RESTA", "-")

    def test_division_potencia_y_comentario(self):
        self.comparar("//", "OP_DIV_ENTERA")
        self.comparar("**", "OP_POTENCIA")
        self.comparar("/", "OP_DIV")
        self.comparar("/ *", "OP_DIV", "/")
        self.comparar("/* x */", "COMENTARIO_BLOQUE")

    def test_comparaciones_de_uno_o_dos_caracteres(self):
        self.comparar("=<", "OP_MENOR_IGUAL")
        self.comparar(">=", "OP_MAYOR_IGUAL")
        self.comparar("<", "OP_MENOR")
        self.comparar(">", "OP_MAYOR")
        self.comparar("==", "OP_IDENTICO")


class EquivalenciaExhaustiva(unittest.TestCase):
    """Compara ambos mecanismos con todas las cadenas cortas de un alfabeto mixto."""

    ALFABETO = ["a", "X", "_", "5", ".", "'", '"', "/", "*", "%", "\n", " ", "\\", "=", "-", ":"]

    def test_todas_las_cadenas_de_hasta_tres_caracteres(self):
        for largo in range(1, 4):
            for combinacion in itertools.product(self.ALFABETO, repeat=largo):
                texto = "".join(combinacion)
                self.assertEqual(
                    reconocer_er(texto), afd_integrado.reconocer(texto), f"entrada {texto!r}"
                )


if __name__ == "__main__":
    unittest.main()
