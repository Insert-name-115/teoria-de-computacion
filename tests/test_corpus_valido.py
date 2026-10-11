import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from lexer import analizar
from main import main


CARPETA_PROYECTO = Path(__file__).resolve().parents[1]
ARCHIVO_VALIDO = CARPETA_PROYECTO / "corpus" / "programa_valido.pl"


class CasosValidosTests(unittest.TestCase):
    def test_categorias_validas(self):
        casos = [
            ("padre", "ATOMO"),
            ("persona_1", "ATOMO"),
            ("'Juan Perez'", "ATOMO_COMILLAS"),
            ("':-'", "ATOMO_COMILLAS"),
            ("X", "VARIABLE"),
            ("_Temporal", "VARIABLE"),
            ("_", "VARIABLE_ANONIMA"),
            ("25", "ENTERO"),
            ("3.14", "REAL"),
            ('"hola"', "CADENA"),
            (":-", "OP_REGLA"),
            ("?-", "OP_CONSULTA"),
            ("-->", "OP_DCG"),
            ("\\==", "OP_NO_IDENTICO"),
            ("=..", "OP_UNIV"),
            ("//", "OP_DIV_ENTERA"),
            ("**", "OP_POTENCIA"),
            ("\\+", "OP_NEGACION"),
            ("[dato|Resto]", "CORCHETE_IZQ"),
            ("{dato}", "LLAVE_IZQ"),
        ]

        for texto, tipo_esperado in casos:
            with self.subTest(texto=texto):
                resultado = analizar(texto)
                self.assertTrue(resultado.es_valido)
                self.assertTrue(resultado.tokens)
                self.assertEqual(resultado.tokens[0].tipo, tipo_esperado)

    def test_archivo_completo_no_tiene_errores(self):
        texto = ARCHIVO_VALIDO.read_text(encoding="utf-8")
        resultado = analizar(texto)

        self.assertTrue(resultado.es_valido, resultado.errores)
        self.assertGreater(len(resultado.tokens), 60)

        tipos = {token.tipo for token in resultado.tokens}
        tipos_necesarios = {
            "ATOMO",
            "ATOMO_COMILLAS",
            "VARIABLE",
            "VARIABLE_ANONIMA",
            "ENTERO",
            "REAL",
            "CADENA",
            "OP_REGLA",
            "OP_CONSULTA",
            "OP_DCG",
            "OP_UNIV",
            "OP_NEGACION",
            "PARENTESIS_IZQ",
            "CORCHETE_IZQ",
            "LLAVE_IZQ",
            "BARRA",
            "PUNTO",
        }
        self.assertTrue(tipos_necesarios.issubset(tipos), tipos_necesarios - tipos)

    def test_main_muestra_las_tres_secciones(self):
        salida = io.StringIO()
        with redirect_stdout(salida):
            codigo = main([str(ARCHIVO_VALIDO)])

        self.assertEqual(codigo, 0)
        self.assertIn("TOKENS", salida.getvalue())
        self.assertIn("ERRORES", salida.getvalue())
        self.assertIn("TABLA DE LEXEMAS", salida.getvalue())


if __name__ == "__main__":
    unittest.main()
