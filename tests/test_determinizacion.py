import itertools
import io
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

import determinizacion
from AFDS import afd_integrado
from determinizacion import (
    EPS,
    calcular_determinizacion,
    clausura,
    construir_afn,
    ejecutar_determinizacion,
)
from main import main

CARPETA_PROYECTO = Path(__file__).resolve().parents[1]


class AfnTests(unittest.TestCase):
    def setUp(self):
        self.afn, self.aceptacion = construir_afn()

    def test_clausura_epsilon_del_estado_inicial(self):
        self.assertEqual(clausura(self.afn, ["q0"]), ("q0", "q1", "q3", "q5", "q8"))

    def test_clausura_de_un_estado_sin_epsilon_es_el_mismo(self):
        self.assertEqual(clausura(self.afn, ["q2"]), ("q2",))

    def test_el_afn_tiene_transiciones_epsilon_y_cuatro_estados_de_aceptacion(self):
        self.assertIn(("q0", EPS), self.afn)
        self.assertEqual(
            self.aceptacion,
            {"q2": "ATOMO", "q4": "VARIABLE_ANONIMA", "q7": "VARIABLE", "q9": "VARIABLE"},
        )

    def test_construir_afn_devuelve_copias_independientes(self):
        otro, _ = construir_afn()
        otro[("q0", EPS)].append("q99")
        self.assertNotIn("q99", self.afn[("q0", EPS)])


class SubconjuntosTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = calcular_determinizacion()

    def test_subconjuntos_descubiertos(self):
        # El orden depende de los simbolos (minuscula, mayuscula, digito, guion_bajo)
        self.assertEqual(self.r.subconjuntos[0], ("q0", "q1", "q3", "q5", "q8"))
        self.assertEqual(
            set(self.r.subconjuntos),
            {("q0", "q1", "q3", "q5", "q8"), ("q2",), ("q4", "q6"), ("q9",), ("q7",)},
        )
        self.assertEqual(len(self.r.subconjuntos), 5)

    def test_el_afd_es_determinista_y_sin_epsilon(self):
        for (_, simbolo), destino in self.r.afd_subconjuntos.transiciones.items():
            self.assertNotEqual(simbolo, EPS)
            self.assertIsInstance(destino, str)  # un unico destino por transicion

    def test_estados_de_aceptacion_del_afd_por_subconjuntos(self):
        nombres = self.r.nombre_subconjunto
        aceptacion = self.r.afd_subconjuntos.aceptacion
        self.assertEqual(aceptacion[nombres[("q2",)]], "ATOMO")
        self.assertEqual(aceptacion[nombres[("q4", "q6")]], "VARIABLE_ANONIMA")
        self.assertEqual(aceptacion[nombres[("q9",)]], "VARIABLE")
        self.assertEqual(aceptacion[nombres[("q7",)]], "VARIABLE")
        self.assertNotIn(nombres[("q0", "q1", "q3", "q5", "q8")], aceptacion)


class MinimizacionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = calcular_determinizacion()

    def test_los_dos_estados_variable_son_equivalentes(self):
        nombres = self.r.nombre_subconjunto
        gemelos = sorted([nombres[("q9",)], nombres[("q7",)]])
        grupos = [sorted(g) for g in self.r.grupos_equivalentes]
        self.assertIn(gemelos, grupos)

    def test_el_resto_de_los_estados_no_se_une(self):
        self.assertEqual(sorted(len(g) for g in self.r.grupos_equivalentes), [1, 1, 1, 2])

    def test_el_minimo_tiene_un_estado_menos(self):
        def contar(afd):
            return len({afd.inicial} | {e for e, _ in afd.transiciones} | set(afd.transiciones.values()))

        self.assertEqual(contar(self.r.afd_subconjuntos), 5)
        self.assertEqual(contar(self.r.afd_minimo), 4)

    def test_el_minimo_conserva_los_tres_tokens(self):
        self.assertEqual(
            set(self.r.afd_minimo.aceptacion.values()),
            {"ATOMO", "VARIABLE", "VARIABLE_ANONIMA"},
        )

    def test_dos_estados_con_distinto_token_no_se_unen(self):
        # el estado de la variable anonima (_) y el de una variable normal acepta distinto token
        nombres = self.r.nombre_subconjunto
        grupos = self.r.grupos_equivalentes
        for grupo in grupos:
            self.assertFalse({nombres[("q4", "q6")], nombres[("q2",)]} <= set(grupo))

    def test_sin_transicion_se_trata_como_estado_trampa(self):
        # '1' no sale del estado inicial: el minimo lo rechaza igual que el AFD por subconjuntos
        self.assertEqual(self.r.afd_minimo.reconocer("1abc"), (None, ""))
        self.assertEqual(self.r.afd_subconjuntos.reconocer("1abc"), (None, ""))


class CoincidenciaConIntegradoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = calcular_determinizacion()

    def test_las_comparaciones_del_resultado_coinciden(self):
        self.assertTrue(self.r.coincide_con_integrado)
        self.assertGreaterEqual(len(self.r.comparaciones), 10)

    def test_atomos_variables_y_anonima(self):
        casos = {
            "padre": "ATOMO",
            "persona_1": "ATOMO",
            "X": "VARIABLE",
            "Persona": "VARIABLE",
            "_Temporal": "VARIABLE",
            "_X": "VARIABLE",
            "__": "VARIABLE",
            "_": "VARIABLE_ANONIMA",
            "is": "OP_IS",
            "mod": "OP_MOD",
            "isa": "ATOMO",
        }
        for texto, tipo in casos.items():
            with self.subTest(texto=texto):
                minimo = self.r.afd_minimo.reconocer(texto)
                self.assertEqual(minimo, afd_integrado.reconocer(texto))
                self.assertEqual(minimo, (tipo, texto))

    def test_todas_las_cadenas_cortas_que_empiezan_como_atomo_o_variable(self):
        alfabeto = ["a", "Z", "_", "7", "."]
        for largo in range(1, 6):
            for combinacion in itertools.product(alfabeto, repeat=largo):
                texto = "".join(combinacion)
                if texto[0] == "7" or texto[0] == ".":
                    continue  # ENTERO/PUNTO no pertenecen al AFN representativo
                self.assertEqual(
                    self.r.afd_minimo.reconocer(texto), afd_integrado.reconocer(texto), texto
                )


class EjecucionTests(unittest.TestCase):
    def test_importar_no_imprime_ni_crea_archivos(self):
        with tempfile.TemporaryDirectory() as temporal:
            proceso = subprocess.run(
                [sys.executable, "-c", f"import sys; sys.path.insert(0, {str(CARPETA_PROYECTO)!r}); import determinizacion"],
                cwd=temporal, capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(proceso.returncode, 0, proceso.stderr)
            self.assertEqual(proceso.stdout, "")
            self.assertEqual(list(Path(temporal).iterdir()), [])

    def test_la_carpeta_por_defecto_sale_del_proyecto_y_no_del_directorio_actual(self):
        with tempfile.TemporaryDirectory() as temporal:
            codigo = (
                f"import sys; sys.path.insert(0, {str(CARPETA_PROYECTO)!r}); "
                "import determinizacion; print(determinizacion.CARPETA_AUTOMATAS)"
            )
            proceso = subprocess.run(
                [sys.executable, "-c", codigo], cwd=temporal, capture_output=True, text=True, timeout=30
            )
            self.assertEqual(Path(proceso.stdout.strip()), CARPETA_PROYECTO / "automatas")

    def test_ejecutar_crea_la_carpeta_y_guarda_los_tres_diagramas(self):
        with tempfile.TemporaryDirectory() as temporal:
            carpeta = Path(temporal) / "no" / "existe" / "automatas"
            resultado = ejecutar_determinizacion(carpeta, imprimir=False)

            nombres = sorted(ruta.name for ruta in carpeta.iterdir())
            self.assertEqual(nombres, ["afd_minimo.dot", "afd_subconjuntos.dot", "afn_ejemplo.dot"])
            self.assertEqual(len(resultado.archivos), 3)

    def test_ejecutar_sin_guardar_no_escribe_nada(self):
        with tempfile.TemporaryDirectory() as temporal:
            carpeta = Path(temporal) / "automatas"
            ejecutar_determinizacion(carpeta, imprimir=False, guardar=False)
            self.assertFalse(carpeta.exists())

    def test_ejecutar_con_imprimir_muestra_las_tablas(self):
        salida = io.StringIO()
        with redirect_stdout(salida):
            ejecutar_determinizacion(imprimir=True, guardar=False)
        texto = salida.getvalue()
        for esperado in ("Tabla de subconjuntos", "Estados equivalentes", "mínimo:", "integrado:"):
            self.assertIn(esperado, texto)

    def test_main_determinizar_sigue_funcionando(self):
        with tempfile.TemporaryDirectory() as temporal:
            carpeta = Path(temporal) / "automatas"
            with mock.patch.object(determinizacion, "CARPETA_AUTOMATAS", carpeta):
                with redirect_stdout(io.StringIO()) as salida:
                    codigo = main(["--determinizar"])

            self.assertEqual(codigo, 0)
            self.assertIn("Tabla de subconjuntos", salida.getvalue())
            self.assertTrue((carpeta / "afd_minimo.dot").exists())


if __name__ == "__main__":
    unittest.main()
