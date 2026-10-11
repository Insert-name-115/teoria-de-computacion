# Analizador lexico de Prolog - INFO1148

Este repositorio contiene un analizador lexico para el subconjunto de Prolog
definido en la tarea de Teoria de la Computacion. El programa reconoce los
tokens con un AFD integrado, conserva la linea y columna de cada lexema y
mantiene una tabla sin elementos repetidos.

## Requisitos

- Python 3.10 o superior.
- Paquete `graphviz` para generar los archivos DOT.

Las dependencias se instalan con:

```powershell
pip install -r requirements.txt
```

## Uso

Para analizar el programa de ejemplo:

```powershell
python main.py corpus/programa_valido.pl
```

La salida se divide en tokens, errores y tabla de lexemas. Los tokens usan el
siguiente formato:

```text
<TIPO, 'lexema', linea, columna, atributo=valor>
```

Las lineas y columnas comienzan en 1. Los espacios y comentarios no aparecen
como tokens, pero se consideran al calcular las posiciones.

## Errores lexicos y recuperacion

Cuando el analizador encuentra algo que no pertenece al subconjunto, informa un
solo error con su tipo, mensaje, linea, columna y fragmento, salta lo
problematico y continua con el resto de la entrada. Los errores quedan en
`resultado.errores`, en el orden en que aparecen, y `analizar()` no lanza
excepciones por entradas invalidas.

| Tipo de error | Cuando ocurre | Recuperacion |
|---|---|---|
| `ATOMO_SIN_CIERRE` | Comilla simple sin cierre en su linea | Se salta hasta el final de la linea |
| `CADENA_SIN_CIERRE` | Comilla doble sin cierre en su linea | Se salta hasta el final de la linea |
| `COMENTARIO_BLOQUE_SIN_CIERRE` | `/*` sin `*/` | Se salta hasta el final del archivo |
| `NUMERO_MAL_FORMADO` | Numero que no es `ENTERO` ni `REAL` | Se salta el fragmento numerico completo |
| `CARACTER_NO_ADMITIDO` | Caracter que no inicia ningun token | Se salta solo ese caracter |

El fragmento informado es la primera linea del texto descartado, recortada a 40
caracteres. Los atomos y cadenas no cruzan lineas, igual que en sus AFD. El
analizador siempre avanza al menos un caracter, asi que no puede quedarse en un
ciclo, y los tokens que siguen a un error conservan su linea y columna.

### Convencion para numeros mal formados

Un numero es valido solo si es un `ENTERO` (`25`) o un `REAL` (`3.14`). Se
informa `NUMERO_MAL_FORMADO` en estos casos:

| Entrada | Resultado | Motivo |
|---|---|---|
| `123abc`, `2a`, `1_000` | Un error para todo el fragmento | Numero seguido de letra o `_` |
| `3.14x` | Un error para todo el fragmento | Real seguido de letra |
| `12.3.4` | Un error para todo el fragmento | Mas de un punto decimal |
| `.5` | Un error para `.5` | Real sin parte entera |
| `3..4` | `ENTERO 3`, `PUNTO` y un error para `.4` | El `.4` queda sin parte entera |
| `3.` | `ENTERO 3` y `PUNTO` | Sin error: el punto es el final de la clausula |
| `valor(3).` | Sin error | Mismo caso |

La regla de contexto es: un punto es el delimitador final (`PUNTO`) salvo que
quede pegado a un digito. Un punto que sigue a un digito y esta seguido de otro
digito forma parte del real (`3.14`). Un punto seguido de un digito sin digito
antes (`.5`) o despues de un real (`12.3.4`) se considera numero mal formado.
Los numeros no llevan signo: `-5` son los tokens `OP_RESTA` y `ENTERO`.

Los saltos de linea LF, CR y CRLF cuentan como un solo salto al calcular la
linea y la columna, incluso si el CR y el LF quedan en lexemas distintos.

## Otras opciones

Mostrar la especificacion de tokens:

```powershell
python main.py --especificacion
```

Generar los diagramas de los automatas:

```powershell
python main.py --generar-automatas
```

Ejecutar la determinizacion y minimizacion representativa:

```powershell
python main.py --determinizar
```

Los archivos se guardan en la carpeta `automatas/`. Si la carpeta no existe,
el programa la crea automaticamente.

## Pruebas

Para ejecutar todas las pruebas:

```powershell
python -m unittest discover -s tests -v
```

Las pruebas actuales revisan el recorrido completo, las posiciones, la maxima
coincidencia, las prioridades, la tabla de lexemas y las categorias validas.

## Estructura del proyecto

| Archivo o carpeta | Contenido |
|---|---|
| `especificacion_prolog.py` | Catalogo de tokens y operadores |
| `expresiones_regulares.py` | Expresiones regulares y prioridades |
| `AFDS.py` | AFD individuales, AFD integrado y diagramas |
| `determinizacion.py` | Determinizacion y minimizacion representativa |
| `modelos.py` | Modelos de tokens, errores y resultado |
| `tabla_lexemas.py` | Tabla de lexemas sin duplicados |
| `lexer.py` | Recorrido completo de la entrada |
| `main.py` | Interfaz para ejecutar el analizador |
| `corpus/` | Archivos de entrada para las pruebas |
| `tests/` | Pruebas automatizadas |
