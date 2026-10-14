import os
from dotenv import load_dotenv

load_dotenv()


def obtener_modelo():
    proveedor = os.getenv("LLM_PROVIDER", "gemini").lower()
    temperatura = float(os.getenv("LLM_TEMPERATURE", "0.0"))

    if proveedor == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        modelo = os.getenv("LLM_MODEL", "gemini-3.5-flash-lite")
        clave = os.getenv("GEMINI_API_KEY")
        if not clave or clave.startswith("tu_"):
            raise ValueError("Falta configurar GEMINI_API_KEY en el archivo .env")
        return ChatGoogleGenerativeAI(model=modelo, google_api_key=clave)

    if proveedor == "anthropic":
        from langchain_anthropic import ChatAnthropic
        modelo = os.getenv("LLM_MODEL", "claude-3-5-haiku-latest")
        clave = os.getenv("ANTHROPIC_API_KEY")
        if not clave or clave.startswith("tu_"):
            raise ValueError("Falta configurar ANTHROPIC_API_KEY en el archivo .env")
        return ChatAnthropic(model=modelo, api_key=clave, temperature=temperatura)

    from langchain_openai import ChatOpenAI
    modelo = os.getenv("LLM_MODEL", "gpt-4o-mini")
    clave = os.getenv("OPENAI_API_KEY")
    if not clave or clave.startswith("tu_"):
        raise ValueError("Falta configurar OPENAI_API_KEY en el archivo .env")
    return ChatOpenAI(model=modelo, api_key=clave, temperature=temperatura)
