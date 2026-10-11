"""Tabla de lexemas sin duplicados y con indices estables."""

from dataclasses import dataclass


@dataclass(frozen=True)
class EntradaLexema:
    indice: int
    tipo: str
    lexema: str
    valor: object = None


class TablaLexemas:
    """Asigna un indice a cada pareja unica de tipo y lexema."""

    def __init__(self):
        self._entradas = []
        self._indices = {}

    def registrar(self, tipo, lexema, valor=None):
        clave = (tipo, lexema)
        indice_existente = self._indices.get(clave)
        if indice_existente is not None:
            return indice_existente

        indice = len(self._entradas)
        self._indices[clave] = indice
        self._entradas.append(EntradaLexema(indice, tipo, lexema, valor))
        return indice

    def buscar(self, tipo, lexema):
        return self._indices.get((tipo, lexema))

    def obtener(self, indice):
        return self._entradas[indice]

    def como_lista(self):
        return list(self._entradas)

    def __len__(self):
        return len(self._entradas)

    def __iter__(self):
        return iter(self._entradas)
