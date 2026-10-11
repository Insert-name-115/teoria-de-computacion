import argparse
import sys
from pathlib import Path

from AFDS import AFDS, afd_integrado, dibujar_afd
from determinizacion import ejecutar_determinizacion
from especificacion_prolog import mostrar_especificacion
from lexer import analizar


CARPETA_PROYECTO = Path(__file__).resolve().parent


def generar_automatas():
    carpeta = CARPETA_PROYECTO / "automatas"
    carpeta.mkdir(exist_ok=True)

    for afd in AFDS + [afd_integrado]:
        archivo = carpeta / f"{afd.nombre.lower()}.dot"
        dibujar_afd(afd).save(str(archivo))

    return carpeta


def mostrar_resultado(resultado):
    print("TOKENS")
    if resultado.tokens:
        for token in resultado.tokens:
            print(token)
    else:
        print("(sin tokens)")

    print("\nERRORES")
    if resultado.errores:
        for error in resultado.errores:
            print(error)
    else:
        print("(sin errores)")

    print("\nTABLA DE LEXEMAS")
    if len(resultado.tabla_lexemas) == 0:
        print("(vacia)")
        return

    for entrada in resultado.tabla_lexemas:
        print(f"{entrada.indice}: {entrada.tipo} {entrada.lexema!r}")


def crear_parser():
    parser = argparse.ArgumentParser(
        description="Analizador lexico para un subconjunto de Prolog"
    )
    parser.add_argument("archivo", nargs="?", help="archivo .pl que se quiere analizar")
    parser.add_argument(
        "--especificacion",
        action="store_true",
        help="muestra la especificacion de los tokens",
    )
    parser.add_argument(
        "--generar-automatas",
        action="store_true",
        help="genera los diagramas en formato DOT",
    )
    parser.add_argument(
        "--determinizar",
        action="store_true",
        help="ejecuta la determinizacion y minimizacion",
    )
    return parser


def _salida_tolerante():
    """Evita UnicodeEncodeError en consolas que no admiten todo Unicode (p. ej. cp1252).

    Un caracter que la consola no puede mostrar se reemplaza por ``?`` en vez de
    abortar el programa. No hace nada si la salida no se puede reconfigurar.
    """
    for flujo in (sys.stdout, sys.stderr):
        reconfigurar = getattr(flujo, "reconfigure", None)
        if reconfigurar is not None:
            try:
                reconfigurar(errors="replace")
            except (ValueError, OSError):
                pass


def main(argumentos=None):
    _salida_tolerante()
    parser = crear_parser()
    opciones = parser.parse_args(argumentos)
    hizo_algo = False

    if opciones.especificacion:
        mostrar_especificacion()
        hizo_algo = True

    if opciones.generar_automatas:
        carpeta = generar_automatas()
        print(f"Diagramas guardados en {carpeta}")
        hizo_algo = True

    if opciones.determinizar:
        determinizacion = ejecutar_determinizacion()
        if not determinizacion.coincide_con_integrado:
            print("El AFD minimo no coincide con el AFD integrado")
            return 1
        hizo_algo = True

    if opciones.archivo:
        ruta = Path(opciones.archivo)
        try:
            texto = ruta.read_text(encoding="utf-8")
        except OSError as error:
            parser.error(f"no se pudo leer el archivo: {error}")

        resultado = analizar(texto)
        mostrar_resultado(resultado)
        return 0 if resultado.es_valido else 1

    if not hizo_algo:
        parser.print_help()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
