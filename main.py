from especificacion_prolog import mostrar_especificacion
from expresiones_regulares import reconocer_er
from AFDS import AFDS, afd_integrado, dibujar_afd

# Punto 1: especificación de tokens
print(" PUNTO 1: Especificación prolog")
mostrar_especificacion()

# Puntos 2 y 3: la ER y el AFD integrado deben elegir el mismo token
print(" PUNTOS 2 y 3: máxima coincidencia y prioridad (ER vs AFD) ")
for texto in ["\\==", "\\=", "=..", ":-", "_", "_X", "is", "isa", "3.14", "3.", "/* c */", "//"]:
    print(f"{texto!r:<10} ER: {reconocer_er(texto)}   AFD: {afd_integrado.reconocer(texto)}")

# Dibujar los autómatas
for afd in AFDS + [afd_integrado]:
    dibujar_afd(afd).save(f"automatas/{afd.nombre.lower()}.dot")
print("Diagramas guardados en la carpeta automatas/")
