from typing import Literal
from langgraph.graph import MessagesState

# Literal con las opciones validas para el enrutamiento
DestinoRuta = Literal["investigador", "analista", "validador", "FIN"]


class EstadoOrquestador(MessagesState):
    """Estado compartido del orquestador multi-agente."""
    siguiente_paso: DestinoRuta
    datos_investigacion: dict
    analisis_computo: dict
    validacion: dict
    tarea_completada: bool
    contador_pasos: int
    historial_delegaciones: list[str]
