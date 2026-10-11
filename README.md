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

Para analizar el corpus valido (no debe producir errores):

```powershell
python main.py corpus/programa_valido.pl
```

Para analizar el corpus invalido (informa ocho errores y sigue analizando):

```powershell
python main.py corpus/programa_con_errores.pl
```

La salida se divide en tokens, errores y tabla de lexemas. Los tokens usan el
siguiente formato:

```text
<TIPO, 'lexema', linea, columna, atributo=valor>
```

Las lineas y columnas comienzan en 1. Los espacios y comentarios no aparecen
como tokens, pero se consideran al calcular las posiciones.

### Codigo de salida

| Codigo | Significado |
|---|---|
| `0` | El analisis termino sin errores lexicos (o solo se uso otra opcion) |
| `1` | Hubo al menos un error lexico, o el AFD minimo no coincidio con el integrado en `--determinizar` |
| `2` | Uso incorrecto: argumento invalido o archivo que no se pudo leer |

## Errores lexicos y recuperacion

Cuando el analizador encuentra algo que no pertenece al subconjunto, informa un
solo error con su tipo, mensaje, linea, columna y fragmento, salta lo
problematico y continua con el resto de la entrada. Los errores quedan en
`resultado.errores`, en el orden en que aparecen, y `analizar()` no lanza
excepciones por entradas invalidas.

| Tipo de error | Cuando ocurre | Recuperacion |
|---|---|---|
| `ATOMO_SIN_CIERRE` | Comilla simple sin cierre en su linea (incluye `'a''b`) | Se salta hasta el final de la linea |
| `CADENA_SIN_CIERRE` | Comilla doble sin cierre en su linea (incluye `"a""b`) | Se salta hasta el final de la linea |
| `COMENTARIO_BLOQUE_SIN_CIERRE` | `/*` sin `*/` | Se salta hasta el final del archivo |
| `NUMERO_MAL_FORMADO` | Numero que no es `ENTERO` ni `REAL` | Se salta el fragmento numerico completo |
| `CARACTER_NO_ADMITIDO` | Caracter que no inicia ningun token | Se salta solo ese caracter |

Dentro de un texto entre comillas, `''` y `""` son una comilla escapada. Por eso
`"a""b` es una sola cadena sin cierre (fragmento `"a""b`) y no la cadena `"a"`
seguida de un error; en cambio `"a""b"` es una cadena valida.

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

Si la consola no admite algun caracter (por ejemplo cp1252 en Windows), se
muestra como `?` en vez de abortar el programa.

Mostrar la especificacion de tokens:

```powershell
python main.py --especificacion
```

## Generacion de diagramas

```powershell
python main.py --generar-automatas
```

Guarda en `automatas/` un archivo DOT por cada AFD individual (`atomo.dot`,
`variable.dot`, `numero.dot`, `atomo_comillas.dot`, `cadena.dot`,
`comentario_linea.dot`, `comentario_bloque.dot`, `espacio.dot`,
`operadores.dot`) y el AFD integrado (`integrado.dot`). Solo hace falta el
paquete Python `graphviz`; para convertir un DOT a imagen se necesita ademas el
programa Graphviz instalado:

```powershell
dot -Tpng automatas/afd_minimo.dot -o afd_minimo.png
```

La carpeta `automatas/` se **versiona**: los DOT finales son evidencia del
informe y el repositorio queda reproducible. Los archivos se generan siempre
de forma ordenada, asi que volver a ejecutar los comandos no cambia nada si el
codigo no cambio. Las rutas se calculan desde la carpeta del proyecto, por lo
que los comandos funcionan desde cualquier directorio, y la carpeta se crea si
no existe.

## Determinizacion y minimizacion

```powershell
python main.py --determinizar
```

Trabaja sobre un AFN representativo con transiciones epsilon que reconoce
`ATOMO`, `VARIABLE_ANONIMA` y `VARIABLE`:

1. **AFN** (`automatas/afn_ejemplo.dot`): estados `q0`-`q9`.
2. **AFD por subconjuntos** (`automatas/afd_subconjuntos.dot`): construccion de
   subconjuntos con clausura epsilon; produce los estados `A0`-`A4`.
3. **AFD minimo** (`automatas/afd_minimo.dot`): se parte de los estados
   agrupados por token y se separan los que van a bloques distintos hasta que
   la particion no cambia. `A2` y `A4` (ambos `VARIABLE`) se unen.

La salida muestra la tabla de subconjuntos, cada ronda de la particion, los
estados equivalentes y una comparacion del AFD minimo con el AFD integrado para
atomos, variables y variable anonima. Si no coinciden, el comando termina con
codigo `1`.

**AFD parcial.** No se agrega estado trampa: los AFD del proyecto son parciales
y una transicion ausente significa rechazar (trampa implicita, no dibujada). En
la minimizacion una transicion ausente cuenta como un destino propio, distinto
de cualquier bloque, asi que el resultado es el mismo que con trampa explicita.

`calcular_determinizacion()` hace todo el calculo sin imprimir ni escribir
archivos, y `ejecutar_determinizacion(carpeta_salida=None, imprimir=True,
guardar=True)` lo muestra y guarda los DOT. Ambas devuelven un
`ResultadoDeterminizacion` (subconjuntos, particiones, AFD, comparaciones y
archivos guardados) y no dependen de variables globales modificables. Importar
`determinizacion.py` no imprime ni genera archivos.

## Pruebas

Para ejecutar todas las pruebas:

```powershell
python -m unittest discover -s tests -v
```

| Archivo | Que comprueba |
|---|---|
| `test_lexer_base.py` | Modelos, tabla de lexemas, posiciones, maxima coincidencia y prioridades |
| `test_corpus_valido.py` | Categorias validas y el corpus valido sin errores |
| `test_errores_lexicos.py` | Los cinco tipos de error, recuperacion, corpus invalido y codigo de salida |
| `test_equivalencia.py` | `reconocer_er()` y `afd_integrado.reconocer()` dan el mismo tipo y lexema en entradas validas |
| `test_salida_consola.py` | La salida no falla con consolas cp1252 (Windows) |
| `test_determinizacion.py` | Subconjuntos, minimizacion, rutas, carpeta `automatas/` y coincidencia del AFD minimo con el integrado |

## Validacion completa

```powershell
pip install -r requirements.txt
python -m unittest discover -s tests -v
python main.py corpus/programa_valido.pl
python main.py corpus/programa_con_errores.pl
python main.py --especificacion
python main.py --generar-automatas
python main.py --determinizar
git status
```

## Estructura del proyecto

| Archivo o carpeta | Contenido |
|---|---|
| `especificacion_prolog.py` | Catalogo de tokens y operadores |
| `expresiones_regulares.py` | Expresiones regulares y prioridades |
| `AFDS.py` | AFD individuales, AFD integrado y diagramas |
| `determinizacion.py` | AFN, subconjuntos, minimizacion y comparacion con el AFD integrado |
| `modelos.py` | Modelos de tokens, errores y resultado |
| `tabla_lexemas.py` | Tabla de lexemas sin duplicados |
| `lexer.py` | Recorrido completo de la entrada |
| `main.py` | Interfaz para ejecutar el analizador |
| `corpus/` | `programa_valido.pl` y `programa_con_errores.pl` |
| `automatas/` | Diagramas DOT (versionados como evidencia) |
| `tests/` | Pruebas automatizadas |
