"""La salida no debe fallar en consolas que no admiten todo Unicode (cp1252 en Windows)."""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


def ejecutar(*argumentos):
    entorno = {**os.environ, "PYTHONIOENCODING": "cp1252", "PYTHONUTF8": "0"}
    return subprocess.run(
        [sys.executable, str(RAIZ / "main.py"), *argumentos],
        capture_output=True, timeout=60, env=entorno,
    )


class SalidaCp1252(unittest.TestCase):
    def test_determinizar_no_falla_con_cp1252(self):
        proceso = ejecutar("--determinizar")
        self.assertEqual(proceso.returncode, 0, proceso.stderr.decode("cp1252", "replace"))
        self.assertNotIn(b"UnicodeEncodeError", proceso.stderr)

    def test_especificacion_no_falla_con_cp1252(self):
        proceso = ejecutar("--especificacion")
        self.assertEqual(proceso.returncode, 0, proceso.stderr.decode("cp1252", "replace"))

    def test_un_caracter_fuera_de_cp1252_en_la_entrada_no_aborta(self):
        with tempfile.TemporaryDirectory() as temporal:
            archivo = Path(temporal) / "euro.pl"
            archivo.write_text("a(1).\n\u20ac \u03b5 b(2).\n", encoding="utf-8")
            proceso = ejecutar(str(archivo))
        self.assertEqual(proceso.returncode, 1, proceso.stderr.decode("cp1252", "replace"))
        self.assertNotIn(b"UnicodeEncodeError", proceso.stderr)
        self.assertIn(b"CARACTER_NO_ADMITIDO", proceso.stdout)


if __name__ == "__main__":
    unittest.main()
