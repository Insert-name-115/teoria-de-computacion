# Analizador léxico de Prolog — INFO1148 Teoría de la Computación

| Archivo | Contenido |
|---|---|
| `especificacion_prolog.py` | Punto 1: tokens, patrón, ejemplos válidos/inválidos y atributo |
| `expresiones_regulares.py` | Punto 2: una expresión regular por token, máxima coincidencia y prioridad |
| `AFDS.py` | Punto 3: AFD de cada categoría, AFD integrado y dibujo con Graphviz |
| `main.py` | Ejecuta los tres puntos y guarda los diagramas en `automatas/` |

## Ejecución

```bash
pip install -r requirements.txt
python main.py
```

Los diagramas se guardan como `.dot` en `automatas/`. Se pueden ver en
https://dreampuf.github.io/GraphvizOnline
