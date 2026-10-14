from langgraph.graph import StateGraph, START, END
from state import EstadoOrquestador
from supervisor import ejecutar_supervisor
from agents.research_agent import ejecutar_investigador
from agents.analyst_agent import ejecutar_analista
from validator import ejecutar_validador


def rutar_desde_supervisor(estado: EstadoOrquestador) -> str:
    """Funcion de decision de la arista condicional del Supervisor."""
    return estado.get("siguiente_paso", "FIN")


def construir_grafo_orquestador():
    """Construye y compila el StateGraph jerarquico con nodo Supervisor."""
    grafo = StateGraph(EstadoOrquestador)

    # Registro de nodos
    grafo.add_node("supervisor", ejecutar_supervisor)
    grafo.add_node("investigador", ejecutar_investigador)
    grafo.add_node("analista", ejecutar_analista)
    grafo.add_node("validador", ejecutar_validador)

    # Flujo de entrada
    grafo.add_edge(START, "supervisor")

    # Arista condicional desde el supervisor hacia especialistas o hacia el fin
    grafo.add_conditional_edges(
        "supervisor",
        rutar_desde_supervisor,
        {
            "investigador": "investigador",
            "analista": "analista",
            "validador": "validador",
            "FIN": END,
        },
    )

    # Retorno ciclico de cada especialista hacia el supervisor
    grafo.add_edge("investigador", "supervisor")
    grafo.add_edge("analista", "supervisor")
    grafo.add_edge("validador", "supervisor")

    return grafo.compile()


orquestador = construir_grafo_orquestador()
