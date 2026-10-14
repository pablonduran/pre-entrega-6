from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from config import obtener_modelo
from state import EstadoOrquestador, DestinoRuta


class DecisionDelegacion(BaseModel):
    siguiente_paso: DestinoRuta = Field(
        description="Agente al cual derivar la tarea ('investigador', 'analista', 'validador') o 'FIN' si esta lista para responder al usuario."
    )
    motivo: str = Field(description="Explicacion breve y directa del motivo de la eleccion.")


async def ejecutar_supervisor(estado: EstadoOrquestador) -> dict:
    """Nodo Supervisor central que orquesta el flujo y delega dinamicamente."""
    contador = estado.get("contador_pasos", 0)

    # Limite estricto de pasos para evitar bucles infinitos
    if contador >= 7:
        mensaje_cierre = AIMessage(
            content="[Supervisor]: Se alcanzo el limite de pasos de seguridad. Procediendo al cierre del flujo."
        )
        return {
            "messages": [mensaje_cierre],
            "siguiente_paso": "FIN",
            "tarea_completada": True,
        }

    datos_inv = estado.get("datos_investigacion", {})
    analisis = estado.get("analisis_computo", {})
    val = estado.get("validacion", {})

    modelo = obtener_modelo()

    prompt_supervisor = SystemMessage(
        content=(
            "Sos el Supervisor del sistema multi-agente de analisis e infraestructura. "
            "Tu tarea es evaluar el estado de la conversacion y decidir quien debe intervenir ahora: "
            "1. 'investigador': si aun no se han buscado los servidores o infraestructura del cliente. "
            "2. 'analista': si ya tenemos los datos de infraestructura pero falta calcular los costos y ahorros. "
            "3. 'validador': si ya tenemos investigacion y calculos, pero aun no fueron auditados. "
            "4. 'FIN': si la validacion fue aprobada y es momento de dar la respuesta final al usuario. "
            "Responde estrictamente utilizando la estructura requerida."
        )
    )

    # Resumen del contexto empaquetado en un mensaje de usuario para evitar prefilling en proveedores estrictos
    historial_texto = []
    for m in estado["messages"]:
        rol = "Usuario" if getattr(m, "type", "") == "human" else "Agente"
        historial_texto.append(f"{rol}: {m.content}")

    texto_resumen = (
        "Historial reciente:\n"
        + "\n".join(historial_texto[-4:])
        + f"\n\nEstado de datos actual:\n"
        + f"- Investigacion completada: {bool(datos_inv.get('servidores'))}\n"
        + f"- Computo de costos completado: {bool(analisis.get('costo_mensual_base_usd'))}\n"
        + f"- Validacion aprobada: {bool(val.get('aprobado'))}\n\n"
        + "¿A que agente corresponde delegar ahora o corresponde FIN?"
    )
    mensaje_evaluacion = HumanMessage(content=texto_resumen)

    modelo_estructurado = modelo.with_structured_output(DecisionDelegacion)
    decision = await modelo_estructurado.ainvoke([prompt_supervisor, mensaje_evaluacion])

    destino: DestinoRuta = decision.siguiente_paso

    # Salvaguarda logica determinista
    if not datos_inv.get("servidores"):
        destino = "investigador"
    elif not analisis.get("costo_mensual_base_usd"):
        destino = "analista"
    elif not val.get("aprobado"):
        destino = "validador"
    else:
        destino = "FIN"

    historial = list(estado.get("historial_delegaciones", []))
    historial.append(f"supervisor->{destino}")

    # Si el flujo finaliza, el supervisor sintetiza la respuesta final
    if destino == "FIN":
        cliente_nombre = datos_inv.get("cliente", "el cliente")
        cliente_email = datos_inv.get("email", "")
        plan = datos_inv.get("plan", "Standard")
        servidores = datos_inv.get("servidores", [])
        detalle_servidores = ", ".join(f"{s['nombre']} ({s['tipo']})" for s in servidores)

        costo_mensual = analisis.get("costo_mensual_base_usd", 0.0)
        costo_anual = analisis.get("costo_anual_base_usd", 0.0)
        descuento = analisis.get("porcentaje_descuento_aplicado", 0.0)
        ahorro = analisis.get("ahorro_anual_usd", 0.0)
        costo_final = analisis.get("costo_anual_final_usd", 0.0)

        respuesta_sintetizada = (
            f"Informe tecnico y financiero para {cliente_nombre} ({cliente_email}), con plan {plan}. "
            f"Infraestructura activa: {detalle_servidores}. "
            f"El costo operativo base es de USD {costo_mensual} mensuales, lo que equivale a USD {costo_anual} al ano. "
            f"Al aplicar un descuento del {descuento}% por compromiso anual, el ahorro total es de USD {ahorro} al ano, "
            f"dejando un costo anual final de USD {costo_final}."
        )

        mensaje_final = AIMessage(content=respuesta_sintetizada)
        return {
            "messages": [mensaje_final],
            "siguiente_paso": "FIN",
            "tarea_completada": True,
            "contador_pasos": contador + 1,
            "historial_delegaciones": historial,
        }

    mensaje_delegacion = AIMessage(
        content=f"[Supervisor]: Delegando siguiente tarea al agente '{destino}'. Motivo: {decision.motivo}"
    )

    return {
        "messages": [mensaje_delegacion],
        "siguiente_paso": destino,
        "tarea_completada": False,
        "contador_pasos": contador + 1,
        "historial_delegaciones": historial,
    }
