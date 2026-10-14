import json
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from config import obtener_modelo
from state import EstadoOrquestador

# Base de datos tecnica de infraestructura cloud
CATALOGO_SERVIDORES = {
    "ana.gomez@hotmail.com": {
        "cliente": "Ana Gomez",
        "email": "ana.gomez@hotmail.com",
        "plan": "Enterprise Cloud",
        "servidores": [
            {
                "id_servidor": "srv-prod-db",
                "nombre": "Base de datos PostgreSQL Principal",
                "tipo": "db.m5.xlarge",
                "vcpu": 4,
                "ram_gb": 16,
                "almacenamiento_gb": 500,
                "costo_hora_usd": 0.38,
            },
            {
                "id_servidor": "srv-cache-redis",
                "nombre": "Cluster Redis Cache",
                "tipo": "cache.r5.large",
                "vcpu": 2,
                "ram_gb": 13,
                "almacenamiento_gb": 50,
                "costo_hora_usd": 0.16,
            },
        ],
    },
    "carlos.lopez@hotmail.com": {
        "cliente": "Carlos Lopez",
        "email": "carlos.lopez@hotmail.com",
        "plan": "Standard Startup",
        "servidores": [
            {
                "id_servidor": "srv-app-api",
                "nombre": "Servidor API FastAPI",
                "tipo": "t3.medium",
                "vcpu": 2,
                "ram_gb": 4,
                "almacenamiento_gb": 80,
                "costo_hora_usd": 0.08,
            }
        ],
    },
}


@tool
def buscar_servidores_infraestructura(email_cliente: str) -> dict:
    """Consulta la infraestructura de servidores cloud contratada por un cliente segun su email.

    Devuelve la lista detallada de servidores activos, especificaciones tecnicas (vCPU, RAM, disco)
    y el costo por hora en dolares de cada maquina.
    """
    email_limpio = email_cliente.strip().lower()
    if email_limpio in CATALOGO_SERVIDORES:
        return CATALOGO_SERVIDORES[email_limpio]
    return {
        "error": f"No se encontro infraestructura registrada para el email {email_cliente}.",
        "servidores": [],
    }


herramientas_investigador = [buscar_servidores_infraestructura]


async def ejecutar_investigador(estado: EstadoOrquestador) -> dict:
    """Nodo especialista de investigacion y busqueda de infraestructura."""
    modelo_con_tools = obtener_modelo().bind_tools(herramientas_investigador)
    modelo_simple = obtener_modelo()

    prompt_sistema = SystemMessage(
        content=(
            "Sos el agente especialista en investigacion de infraestructura tecnica. "
            "Tu objetivo es consultar la base de servidores del cliente requerido usando la herramienta disponible. "
            "Responde de forma clara y directa, en texto plano y sin asteriscos ni negritas."
        )
    )

    # Extraer la consulta original del usuario para evitar contaminacion de contexto
    primer_mensaje_usuario = ""
    for m in estado["messages"]:
        if getattr(m, "type", "") == "human":
            primer_mensaje_usuario = m.content
            break

    mensaje_instruccion = HumanMessage(
        content=f"Consulta a investigar: {primer_mensaje_usuario}"
    )

    respuesta_llm = await modelo_con_tools.ainvoke([prompt_sistema, mensaje_instruccion])

    datos_obtenidos = {}

    # Ejecutar la herramienta si el modelo la invoco
    if getattr(respuesta_llm, "tool_calls", None):
        for llamada in respuesta_llm.tool_calls:
            if llamada["name"] == "buscar_servidores_infraestructura":
                argumentos = llamada["args"]
                resultado_tool = buscar_servidores_infraestructura.invoke(argumentos)
                datos_obtenidos = resultado_tool
    else:
        # Extraccion de email de respaldo
        email_detectado = "ana.gomez@hotmail.com"
        for palabra in primer_mensaje_usuario.split():
            if "@" in palabra:
                email_detectado = palabra.strip(".,;:()'\"")
        datos_obtenidos = buscar_servidores_infraestructura.invoke({"email_cliente": email_detectado})

    # Sintesis en texto plano para el supervisor
    prompt_resumen = HumanMessage(
        content=(
            f"Con estos datos de infraestructura encontrados: {json.dumps(datos_obtenidos, ensure_ascii=False)}, "
            "redacta una oracion clara indicando el cliente y los servidores que tiene activos."
        )
    )
    sintesis = await modelo_simple.ainvoke([prompt_sistema, prompt_resumen])

    contenido_final = sintesis.content
    if isinstance(contenido_final, list):
        contenido_final = " ".join(
            elem.get("text", "") if isinstance(elem, dict) else str(elem)
            for elem in contenido_final
        )

    mensaje_agente = AIMessage(
        content=f"[Investigador]: {contenido_final}"
    )

    historial = list(estado.get("historial_delegaciones", []))
    historial.append("investigador")

    return {
        "messages": [mensaje_agente],
        "datos_investigacion": datos_obtenidos,
        "historial_delegaciones": historial,
        "contador_pasos": estado.get("contador_pasos", 0) + 1,
    }
