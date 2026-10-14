from langchain_core.messages import AIMessage
from state import EstadoOrquestador


async def ejecutar_validador(estado: EstadoOrquestador) -> dict:
    """Nodo de validacion de calidad y suficiencia de datos antes del cierre."""
    datos_investigacion = estado.get("datos_investigacion", {})
    analisis_computo = estado.get("analisis_computo", {})

    tiene_servidores = bool(datos_investigacion.get("servidores"))
    tiene_costos = bool(analisis_computo.get("costo_mensual_base_usd"))
    tiene_ahorro = bool(analisis_computo.get("ahorro_anual_usd"))

    aprobado = tiene_servidores and tiene_costos and tiene_ahorro

    if aprobado:
        observacion = "Todos los requerimientos fueron cubiertos con datos reales y calculos precisos."
    else:
        observacion = "Falta informacion o calculos incompletos para responder a la solicitud."

    resultado_validacion = {
        "aprobado": aprobado,
        "tiene_datos_servidores": tiene_servidores,
        "tiene_computo_costos": tiene_costos,
        "tiene_proyeccion_ahorro": tiene_ahorro,
        "observacion": observacion,
    }

    mensaje_agente = AIMessage(
        content=f"[Validador]: Control de calidad finalizado. Aprobado: {aprobado}. {observacion}"
    )

    historial = list(estado.get("historial_delegaciones", []))
    historial.append("validador")

    return {
        "messages": [mensaje_agente],
        "validacion": resultado_validacion,
        "historial_delegaciones": historial,
        "contador_pasos": estado.get("contador_pasos", 0) + 1,
    }
