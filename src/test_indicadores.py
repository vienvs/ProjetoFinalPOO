import sys
from pathlib import Path

import pandas as pd
import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from src.indicadores import (CatalogoIndicadores, Indicador, formatar_decimal,
                             formatar_inteiro)

PROCESSADOS = RAIZ / 'data' / 'processed'


@pytest.fixture(scope='module')
def dados():
    return {
        'enem': pd.read_csv(PROCESSADOS / 'enem_brasil_rede.csv'),
        'superior': pd.read_csv(PROCESSADOS / 'superior_brasil.csv'),
        'trajetoria': pd.read_csv(PROCESSADOS / 'trajetoria_coorte_2020.csv'),
    }


@pytest.fixture(scope='module')
def catalogo():
    return CatalogoIndicadores.padrao()


def test_catalogo_tem_pelo_menos_cinco_indicadores(catalogo):
    assert len(catalogo) >= 5


def test_toda_serie_tem_colunas_ano_e_valor_para_2020_a_2024(catalogo, dados):
    for indicador in catalogo:
        serie = indicador.serie(dados)
        assert list(serie.columns) == ['ano', 'valor'], indicador.codigo
        assert serie['ano'].tolist() == [2020, 2021, 2022, 2023, 2024], indicador.codigo


def test_indicadores_do_enem_batem_com_a_tabela_exploratoria(catalogo, dados):
    esperado = pd.read_csv(PROCESSADOS / 'indicadores_exploratorios.csv')
    calculado = catalogo.tabela(dados)
    for coluna in ['inscritos_publica', 'participacao_publica_no_total_pct',
                   'sem_informacao_pct', 'variacao_anual_publica_pct']:
        pd.testing.assert_series_equal(
            calculado[coluna], esperado[coluna], check_names=False, check_exact=False,
            check_dtype=False)


def test_variacao_do_primeiro_ano_fica_ausente(catalogo, dados):
    assert pd.isna(catalogo['variacao_anual_publica_pct'].valor_em(dados, 2020))


def test_valor_de_ano_inexistente_e_ausente(catalogo, dados):
    assert pd.isna(catalogo['inscritos_publica'].valor_em(dados, 1999))


def test_inscritos_publica_2024(catalogo, dados):
    assert catalogo['inscritos_publica'].valor_em(dados, 2024) == 841213


def test_variacao_em_contagem(catalogo, dados):
    variacao = catalogo['inscritos_publica'].variacao_em(dados, 2021)
    assert variacao == pytest.approx((603041 / 685864 - 1) * 100)


def test_trajetoria_fecha_em_100_por_cento(catalogo, dados):
    for ano in range(2020, 2025):
        soma = sum(catalogo[c].valor_em(dados, ano) for c in
                   ['permanencia_coorte', 'conclusao_acumulada_coorte', 'desistencia_acumulada_coorte'])
        assert soma == pytest.approx(100, abs=0.5), ano


def test_ausencia_na_trajetoria_nao_vira_zero(catalogo, dados):
    com_falha = dict(dados)
    trajetoria = dados['trajetoria'].copy()
    trajetoria['conclusoes_no_ano'] = trajetoria['conclusoes_no_ano'].astype(float)
    trajetoria.loc[trajetoria['ano_referencia'].eq(2021), 'conclusoes_no_ano'] = float('nan')
    com_falha['trajetoria'] = trajetoria
    serie = catalogo['conclusao_acumulada_coorte'].serie(com_falha)
    assert serie.loc[serie['ano'].eq(2020), 'valor'].notna().all()
    assert serie.loc[serie['ano'].ge(2021), 'valor'].isna().all()


def test_total_ausente_quando_falta_uma_rede(catalogo, dados):
    sem_privada = dict(dados)
    sem_privada['enem'] = dados['enem'][dados['enem']['rede_origem'].ne('Privada')]
    serie = catalogo['participacao_publica_no_total_pct'].serie(sem_privada)
    assert serie['valor'].isna().all()


def test_formatacao_em_portugues():
    assert formatar_inteiro(1234567) == '1.234.567'
    assert formatar_decimal(52.0037, 1) == '52,0'
    assert formatar_decimal(22.64, 1, com_sinal=True) == '+22,6'
    assert formatar_decimal(float('nan')) == '—'


def test_formatar_percentual_e_contagem(catalogo):
    assert catalogo['participacao_publica_no_total_pct'].formatar(52.0037) == '52,0%'
    assert catalogo['variacao_anual_publica_pct'].formatar(-12.08) == '-12,1%'
    assert catalogo['inscritos_publica'].formatar(841213) == '841.213'
    assert catalogo['inscritos_publica'].formatar(float('nan')) == '—'


def test_indicador_base_e_abstrato():
    with pytest.raises(TypeError):
        Indicador('x', 'x', 'x', 'x', 'x', 'x')


def test_codigo_repetido_e_recusado(catalogo):
    primeiro = catalogo['inscritos_publica']
    with pytest.raises(ValueError):
        CatalogoIndicadores([primeiro, primeiro])


def test_tabela_longa_traz_nome_legivel(catalogo, dados):
    longa = catalogo.tabela_longa(dados, ['permanencia_coorte'])
    assert set(longa['indicador']) == {'Permanência da coorte 2020'}
    assert len(longa) == 5
