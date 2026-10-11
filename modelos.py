"""Modelos de datos usados por el analizador lexico."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Token:
    """Token reconocido junto con su posicion inicial, contada desde 1."""

    tipo: str
    lexema: str
    linea: int
    columna: int
    atributo: object = None

    def __str__(self):
        partes = [self.tipo, repr(self.lexema), str(self.linea), str(self.columna)]
        if self.atributo is not None:
            partes.append(f"atributo={self.atributo!r}")
        return "<" + ", ".join(partes) + ">"


@dataclass(frozen=True)
class ErrorLexico:
    """Error localizado que permite continuar recorriendo la entrada."""

    tipo: str
    mensaje: str
    linea: int
    columna: int
    fragmento: str

    def __str__(self):
        return (
            f"<{self.tipo}, linea={self.linea}, columna={self.columna}, "
            f"fragmento={self.fragmento!r}: {self.mensaje}>"
        )


@dataclass
class ResultadoLexico:
    """Tokens, errores y tabla producidos durante un analisis completo."""

    tabla_lexemas: object
    tokens: list = field(default_factory=list)
    errores: list = field(default_factory=list)

    @property
    def es_valido(self):
        return not self.errores
