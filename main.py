# -*- coding: utf-8 -*-
"""
Interfaz de consola para Alex.

Uso:
    python main.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from alex import Alex


AYUDA = """
Comandos disponibles:
  /salir                -> termina el programa
  /borrar_memoria       -> borra toda la memoria de Alex (con confirmación)
  /exportar <ruta.json> -> exporta la conversación actual a un archivo JSON
  /stats                -> muestra estadísticas de aprendizaje
  /bien                 -> la última respuesta fue útil
  /mal                  -> la última respuesta no fue útil
  /ayuda                -> muestra esta ayuda
""".strip()


def imprimir_historial(alex: Alex):
    print("\n--- Historial de esta sesión ---")
    for m in alex.conversacion.mensajes:
        quien = "Tú" if m["rol"] == "usuario" else "Alex"
        print(f"[{m['timestamp']}] {quien}: {m['texto']}")
    print("--- Fin del historial ---\n")


def main():
    print("=" * 60)
    print(" Alex — IA local en castellano (sin APIs externas de IA)")
    print("=" * 60)
    print("Escribe '/ayuda' para ver los comandos disponibles.\n")

    alex = Alex()
    print(f"Alex: {alex.generador.saludo()}\n")

    while True:
        try:
            entrada = input("Tú: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAlex: ¡Hasta pronto!")
            break

        if not entrada:
            continue

        if entrada == "/salir":
            print("Alex: ¡Hasta pronto! He guardado todo lo aprendido.")
            break
        elif entrada == "/ayuda":
            print(AYUDA)
            continue
        elif entrada == "/stats":
            stats = alex.estadisticas()
            n_palabras = len(alex.memoria.datos["diccionario"])
            n_temas = len(alex.memoria.datos["conocimiento"])
            print(f"Conversaciones totales: {stats.get('conversaciones_totales', 0)}")
            print(f"Mensajes totales: {stats.get('mensajes_totales', 0)}")
            print(f"Palabras en el diccionario: {n_palabras}")
            print(f"Temas de conocimiento guardados: {n_temas}")
            continue
        elif entrada == "/historial":
            imprimir_historial(alex)
            continue
        elif entrada == "/borrar_memoria":
            confirmar = input("¿Seguro que quieres borrar TODA la memoria de Alex? (si/no): ").strip().lower()
            if confirmar == "si":
                alex.borrar_memoria()
                print("Alex: Memoria borrada por completo.")
            else:
                print("Alex: Operación cancelada.")
            continue
        elif entrada.startswith("/exportar"):
            partes = entrada.split(maxsplit=1)
            ruta_destino = partes[1] if len(partes) > 1 else "conversacion_exportada.json"
            alex.exportar_conversacion(ruta_destino)
            print(f"Alex: Conversación exportada a '{ruta_destino}'.")
            continue
        elif entrada == "/bien":
            alex.retroalimentacion(True)
            print("Alex: ¡Gracias! Reforzaré ese tipo de respuestas.")
            continue
        elif entrada == "/mal":
            alex.retroalimentacion(False)
            print("Alex: Entendido, ajustaré mis criterios.")
            continue

        respuesta = alex.responder(entrada)
        print(f"Alex: {respuesta}\n")


if __name__ == "__main__":
    main()
