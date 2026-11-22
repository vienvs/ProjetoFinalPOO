import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from src.dashboard import CODIGOS_TRAJETORIA
from src.fontes import carregar_dados
from src.indicadores import CatalogoIndicadores
from src.visualizacao import Visualizador


def test_visualizador_gera_os_cinco_graficos():
    dados = carregar_dados()
    dados['trajetoria_pct'] = CatalogoIndicadores.padrao().tabela_longa(dados, CODIGOS_TRAJETORIA)
    tipos = {nome: figura.data[0].type for nome, figura in Visualizador().todas(dados).items()}
    assert tipos == {'01_linhas': 'scatter', '02_barras': 'bar', '03_setores': 'pie',
                     '04_dispersao': 'scatter', '05_trajetoria': 'scatter'}


def test_app_abre_e_responde_aos_filtros():
    app = AppTest.from_file(str(RAIZ / 'app.py'), default_timeout=60).run()
    assert not app.exception
    assert len(app.metric) == 7
    app.sidebar.slider[0].set_value((2021, 2023)).run()
    app.sidebar.multiselect[0].set_value(['Pública']).run()
    assert not app.exception
    assert app.metric[0].value == '728.878'
    tabela = next(caixa for caixa in app.selectbox if caixa.label == 'Tabela')
    tabela.set_value('Estatísticas descritivas das inscrições').run()
    assert not app.exception
    assert app.dataframe[0].value['rede_origem'].tolist() == ['Pública']
