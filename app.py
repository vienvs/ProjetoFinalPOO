"""Ponto de entrada do painel "Do Enem à graduação".

Execute na raiz do projeto com:  streamlit run app.py
No Streamlit Community Cloud, informe app.py como arquivo principal.
"""
import streamlit as st

from src.dashboard import Dashboard
from src.fontes import carregar_dados


@st.cache_data(show_spinner=False)
def dados_processados():
    """Lê uma única vez as tabelas de data/processed/ e reaproveita nas interações."""
    return carregar_dados()


Dashboard(dados_processados()).executar()
