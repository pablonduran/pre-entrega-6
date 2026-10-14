import json
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from config import obtener_modelo
from state import EstadoOrquestador


@tool
def calcular_proyeccion_costos(
    costo_total_hora: float,
    porcentaje_descuento: float,
    horas_mes: int = 720,
    meses_ano: int = 12,
) -> dict:
    """Calcula el costo mensual y anual de servidores, el ahorro por descuento y el monto final.

    Recibe el costo total por hora en dolares, el porcentaje de descuento a aplicar (ejemplo 15.0),
    las horas estimadas por mes (por defecto 720) y los meses a proyectar (por defecto 12).
    """
    costo_mensual_base = round(costo_total_hora * horas_mes, 2)
    costo_anual_base = round(costo_mensual_base * meses_ano, 2)

    tasa_descuento = porcentaje_descuento / 100.0
    ahorro_anual = round(costo_anual_base * tasa_descuento, 2)
    costo_anual_con_descuento = round(costo_anual_base - ahorro_anual, 2)
    costo_mensual_con_descuento = round(costo_anual_con_descuento / meses_ano, 2)

    return {
        "costo_total_hora_usd": costo_total_hora,
        "costo_mensual_base_usd": costo_mensual_base,
        "costo_anual_base_usd": costo_anual_base,
        "porcentaje_descuento_aplicado": porcentaje_descuento,
        "ahorro_anual_usd": ahorro_anual,
        "costo_anual_final_usd": costo_anual_con_descuento,
        "costo_mensual_final_usd": costo_mensual_con_descuento,
    }


herramientas_analista = [calcular_proyeccion_costos]


async def ejecutar_analista(estado: EstadoOrquestador) -> dict:
    """Nodo especialista de analisis y computo matematico de costos."""
    modelo_simple = obtener_modelo()

    prompt_sistema = SystemMessage(
        content=(
            "Sos el agente especialista en analisis y computo de costos de infraestructura. "
            "Tu tarea es presentar los calculos de costos mensuales, anuales y el ahorro proyectado. "
            "Responde de forma concisa y directa en texto plano, sin asteriscos ni negritas."
        )
    )

    datos_servidores = estado.get("datos_investigacion", {})
    servidores = datos_servidores.get("servidores", [])

    # Calcular costo por hora sumado de los servidores encontrados
    costo_hora_acumulado = sum(s.get("costo_hora_usd", 0.0) for s in servidores)
    if costo_hora_acumulado == 0:
        costo_hora_acumulado = 0.54

    # Ejecutar la herramienta con los datos disponibles
    calculos = calcular_proyeccion_costos.invoke({
        "costo_total_hora": round(costo_hora_acumulado, 2),
        "porcentaje_descuento": 15.0,
        "horas_mes": 720,
        "meses_ano": 12,
    })

    mensaje_instruccion = HumanMessage(
        content=(
            f"Con estos resultados de calculo oficial: {json.dumps(calculos, ensure_ascii=False)}, "
            "redacta un resumen breve en una oracion que indique el costo mensual, el costo anual y el ahorro con 15% de descuento."
        )
    )

    respuesta_llm = await modelo_simple.ainvoke([prompt_sistema, mensaje_instruccion])

    contenido = respuesta_llm.content
    if isinstance(contenido, list):
        contenido = " ".join(
            elem.get("text", "") if isinstance(elem, dict) else str(elem)
            for elem in contenido
        )

    mensaje_agente = AIMessage(
        content=f"[Analista]: Computo finalizado. {contenido}"
    )

    historial = list(estado.get("historial_delegaciones", []))
    historial.append("analista")

    return {
        "messages": [mensaje_agente],
        "analisis_computo": calculos,
        "historial_delegaciones": historial,
        "contador_pasos": estado.get("contador_pasos", 0) + 1,
    }
