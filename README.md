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

## Otras opciones

Mostrar la especificacion de tokens:

```powershell
python main.py --especificacion
```

Generar los diagramas de los automatas:

```powershell
python main.py --generar-automatas
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
