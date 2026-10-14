import asyncio
import json
from pathlib import Path
from langchain_core.messages import HumanMessage
from graph import construir_grafo_orquestador

RUTA_TRAZA = Path("traza_ejecucion.json")


def formatear_texto(contenido) -> str:
    if isinstance(contenido, str):
        return contenido
    if isinstance(contenido, list):
        return " ".join(
            elem.get("text", "") if isinstance(elem, dict) else str(elem)
            for elem in contenido
        )
    return str(contenido)


async def main():
    app = construir_grafo_orquestador()

    consulta_usuario = (
        "Necesito analizar la infraestructura de servidores cloud de ana.gomez@hotmail.com, "
        "calcular su costo mensual total y determinar cuanto ahorraria anualmente si le aplicamos "
        "un 15% de descuento por contrato anual."
    )

    print("\nConsulta del usuario:")
    print(consulta_usuario)
    print("\nIniciando orquestacion multi-agente...\n")

    estado_inicial = {
        "messages": [HumanMessage(content=consulta_usuario)],
        "siguiente_paso": "investigador",
        "datos_investigacion": {},
        "analisis_computo": {},
        "validacion": {},
        "tarea_completada": False,
        "contador_pasos": 0,
        "historial_delegaciones": [],
    }

    # Configuracion de ejecucion con limite de recursion
    configuracion = {"recursion_limit": 15}

    traza_pasos = []

    # Ejecucion mediante astream para observar cada paso del orquestador
    async for evento in app.astream(estado_inicial, configuracion):
        for nombre_nodo, salida_nodo in evento.items():
            print(f"[Paso {salida_nodo.get('contador_pasos', '-')}] Nodo activo: {nombre_nodo}")

            ultimos_mensajes = salida_nodo.get("messages", [])
            if ultimos_mensajes:
                texto_mensaje = formatear_texto(ultimos_mensajes[-1].content)
                print(f"  Mensaje: {texto_mensaje}\n")

            traza_pasos.append({
                "nodo": nombre_nodo,
                "contador_pasos": salida_nodo.get("contador_pasos"),
                "siguiente_paso": salida_nodo.get("siguiente_paso"),
                "tarea_completada": salida_nodo.get("tarea_completada"),
                "mensaje": texto_mensaje if ultimos_mensajes else "",
                "datos_investigacion": salida_nodo.get("datos_investigacion"),
                "analisis_computo": salida_nodo.get("analisis_computo"),
                "validacion": salida_nodo.get("validacion"),
            })

            if salida_nodo.get("tarea_completada"):
                print("Respuesta final del Orquestador:")
                print(texto_mensaje)
                print("\nFlujo completado exitosamente.")

    # Guardar traza estructurada
    with open(RUTA_TRAZA, "w", encoding="utf-8") as f:
        json.dump(traza_pasos, f, indent=2, ensure_ascii=False)

    print(f"\nTraza guardada en '{RUTA_TRAZA}'.")


if __name__ == "__main__":
    asyncio.run(main())
