import sys
from pathlib import Path

import pandas as pd
import streamlit as st

try:
    from src.analise import AnalisadorColeta
    from src.fontes import carregar_dados
    from src.indicadores import REDES, CatalogoIndicadores, formatar_decimal, formatar_inteiro
    from src.visualizacao import Visualizador
except ModuleNotFoundError:
    from fontes import carregar_dados
    from indicadores import REDES, CatalogoIndicadores, formatar_decimal, formatar_inteiro
    from visualizacao import Visualizador
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # analise.py importa src.indicadores
    from src.analise import AnalisadorColeta

CODIGOS_TRAJETORIA = ['permanencia_coorte', 'conclusao_acumulada_coorte', 'desistencia_acumulada_coorte']

LINK_ENEM = 'https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/sinopses-estatisticas/enem'
LINK_SUPERIOR = ('https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/'
                 'sinopses-estatisticas/educacao-superior')


class FiltrosDashboard:
    def __init__(self, ano_inicial, ano_final, redes, ano_setores):
        self._ano_inicial = ano_inicial
        self._ano_final = ano_final
        self._redes = list(redes)
        self._ano_setores = ano_setores

    @property
    def ano_inicial(self):
        return self._ano_inicial

    @property
    def ano_final(self):
        return self._ano_final

    @property
    def redes(self):
        return list(self._redes)

    @property
    def ano_setores(self):
        return self._ano_setores

    def filtrar_anos(self, tabela, coluna='ano'):
        return tabela[tabela[coluna].between(self._ano_inicial, self._ano_final)]

    def filtrar_redes(self, tabela):
        return tabela[tabela['rede_origem'].isin(self._redes)]


class Dashboard:
    def __init__(self, dados, catalogo=None, visualizador=None):
        self._dados = dados
        self._catalogo = catalogo if catalogo is not None else CatalogoIndicadores.padrao()
        self._visualizador = visualizador if visualizador is not None else Visualizador()
        self._resultados = self._catalogo.tabela(dados)
        self._trajetoria_pct = self._catalogo.tabela_longa(dados, CODIGOS_TRAJETORIA)

    def executar(self):
        st.set_page_config(page_title='Do Enem à graduação', layout='wide')
        self._cabecalho()
        filtros = self._barra_lateral()
        if not filtros.redes:
            st.warning('Escolha ao menos uma rede da escola de origem na barra lateral.')
            st.stop()
        self._kpis(filtros)
        self._visualizacoes(filtros)
        self._tabela(filtros)
        self._analise(filtros)
        self._rodape()

    def _cabecalho(self):
        st.title('Do Enem à graduação')
        st.caption('Brasil · 2020 a 2024 · estudantes da rede pública, Enem e ensino superior · dados oficiais do Inep')
        st.info('Esta análise compara a participação no Enem e o ingresso na graduação. Ela não identifica '
                'estudantes da rede pública que ingressaram pelo Enem. Inscrição não é presença nem aprovação.')

    def _barra_lateral(self):
        anos = sorted(int(ano) for ano in self._dados['enem']['ano'].unique())
        st.sidebar.header('Filtros')
        if len(anos) > 1:
            inicio, fim = st.sidebar.slider('Período (edição do Enem)', min_value=anos[0],
                                            max_value=anos[-1], value=(anos[0], anos[-1]))
        else:
            inicio = fim = anos[0]
        redes = st.sidebar.multiselect(
            'Rede da escola de origem', options=list(REDES), default=list(REDES),
            help='Vale para o gráfico de linhas, o de barras e a tabela de inscrições. '
                 'Os indicadores e o gráfico de composição sempre usam todas as redes.')
        anos_do_periodo = [ano for ano in anos if inicio <= ano <= fim]
        ano_setores = st.sidebar.selectbox('Ano do gráfico de composição', options=anos_do_periodo,
                                           index=len(anos_do_periodo) - 1)
        st.sidebar.caption('O Enem de 2020 foi aplicado em 2021; os anos seguem a edição do exame.')
        return FiltrosDashboard(inicio, fim, redes, ano_setores)

    def _metrica(self, coluna, rotulo, indicador, ano):
        valor = indicador.formatar(indicador.valor_em(self._dados, ano))
        delta = None
        if hasattr(indicador, 'variacao_em'):
            variacao = indicador.variacao_em(self._dados, ano)
            if pd.notna(variacao):
                delta = f'{formatar_decimal(variacao, 1, com_sinal=True)}% vs {ano - 1}'
        coluna.metric(rotulo, valor, delta=delta, help=f'{indicador.descricao} {indicador.limitacao}')

    def _kpis(self, filtros):
        ano = filtros.ano_final
        catalogo = self._catalogo
        st.subheader(f'Indicadores principais · {ano}')
        primeira = st.columns(4)
        self._metrica(primeira[0], 'Inscrições · rede pública', catalogo['inscritos_publica'], ano)
        self._metrica(primeira[1], 'Participação pública', catalogo['participacao_publica_no_total_pct'], ano)
        self._metrica(primeira[2], 'Sem informação da rede', catalogo['sem_informacao_pct'], ano)
        self._metrica(primeira[3], 'Ingressantes na graduação', catalogo['ingressantes_graduacao'], ano)
        st.caption(f'Coorte de ingressantes de 2020 · % dos vínculos com os cursos de ingresso, até {ano}')
        segunda = st.columns(3)
        self._metrica(segunda[0], 'Permanência', catalogo['permanencia_coorte'], ano)
        self._metrica(segunda[1], 'Conclusão acumulada', catalogo['conclusao_acumulada_coorte'], ano)
        self._metrica(segunda[2], 'Desistência acumulada', catalogo['desistencia_acumulada_coorte'], ano)

    def _mostrar(self, nome, dados, **opcoes):
        grafico = self._visualizador.grafico(nome)
        st.plotly_chart(grafico.construir(dados, **opcoes), key=f'grafico_{nome}')
        st.caption(grafico.comentario)

    def _visualizacoes(self, filtros):
        st.subheader('Visualizações')
        por_anos = {'enem': filtros.filtrar_anos(self._dados['enem']),
                    'superior': filtros.filtrar_anos(self._dados['superior']),
                    'trajetoria_pct': filtros.filtrar_anos(self._trajetoria_pct)}
        por_anos_e_redes = {**por_anos, 'enem': filtros.filtrar_redes(por_anos['enem'])}
        abas = st.tabs(['Evolução das inscrições', 'Composição', 'Enem e graduação',
                        'Trajetória da coorte 2020'])
        with abas[0]:
            self._mostrar('01_linhas', por_anos_e_redes)
            self._mostrar('02_barras', por_anos_e_redes)
        with abas[1]:
            self._mostrar('03_setores', por_anos, ano=filtros.ano_setores)
        with abas[2]:
            self._mostrar('04_dispersao', por_anos)
        with abas[3]:
            self._mostrar('05_trajetoria', por_anos)

    def _tabela_indicadores(self, filtros):
        nomes = {indicador.codigo: f'{indicador.nome} ({indicador.unidade})' for indicador in self._catalogo}
        return filtros.filtrar_anos(self._resultados).rename(columns=nomes)

    def _tabela(self, filtros):
        st.subheader('Tabela de dados')
        enem_filtrado = filtros.filtrar_redes(filtros.filtrar_anos(self._dados['enem']))
        tabelas = {
            'Indicadores calculados': self._tabela_indicadores(filtros),
            'Estatísticas descritivas das inscrições': AnalisadorColeta(enem_filtrado).estatisticas(),
            'Inscrições no Enem por rede': enem_filtrado,
            'Ingressantes na graduação': filtros.filtrar_anos(self._dados['superior']),
            'Trajetória da coorte 2020': filtros.filtrar_anos(self._dados['trajetoria'], 'ano_referencia'),
        }
        escolha = st.selectbox('Tabela', options=list(tabelas))
        tabela = tabelas[escolha]
        st.dataframe(tabela, hide_index=True)
        st.download_button('Baixar esta tabela em CSV', tabela.to_csv(index=False).encode('utf-8'),
                           file_name='dados_dashboard.csv', mime='text/csv')

    def _inscricoes(self, rede, ano):
        enem = self._dados['enem']
        linha = enem.loc[enem['rede_origem'].eq(rede) & enem['ano'].eq(ano), 'inscritos_concluintes']
        return linha.iloc[0] if not linha.empty else float('nan')

    def _evolucao(self, indicador, filtros):
        ini, fim = filtros.ano_inicial, filtros.ano_final
        valor_ini = indicador.valor_em(self._dados, ini)
        valor_fim = indicador.valor_em(self._dados, fim)
        if ini != fim and pd.notna(valor_ini) and pd.notna(valor_fim) and valor_ini != 0:
            variacao = formatar_decimal((valor_fim / valor_ini - 1) * 100, 1, com_sinal=True)
            return (f'passaram de {formatar_inteiro(valor_ini)} em {ini} para '
                    f'{formatar_inteiro(valor_fim)} em {fim} ({variacao}%)')
        return f'foram {formatar_inteiro(valor_fim)} em {fim}'

    def _textos_analise(self, filtros):
        fim = filtros.ano_final
        catalogo, dados = self._catalogo, self._dados
        participacao = formatar_decimal(catalogo['participacao_publica_no_total_pct'].valor_em(dados, fim))
        sem_informacao = formatar_decimal(catalogo['sem_informacao_pct'].valor_em(dados, fim))
        permanencia, conclusao, desistencia = (
            formatar_decimal(catalogo[codigo].valor_em(dados, fim)) for codigo in CODIGOS_TRAJETORIA)
        return [
            ('**Rede pública no Enem.** As inscrições de concluintes da rede pública '
             f'{self._evolucao(catalogo["inscritos_publica"], filtros)}. '
             'São inscrições, não presença nem aprovação.'),
            (f'**Peso da rede pública.** Em {fim}, a rede pública responde por {participacao}% das inscrições '
             f'de concluintes, mas {sem_informacao}% dos registros estão sem informação de rede. Por isso esse '
             'percentual descreve os inscritos e não deve ser lido como a participação de toda a rede pública '
             'no Enem.'),
            ('**Ingresso na graduação.** Os ingressantes na graduação, de todas as origens e formas de ingresso, '
             f'{self._evolucao(catalogo["ingressantes_graduacao"], filtros)}. Esse total não identifica quem '
             'entrou pelo Enem; por isso o gráfico de dispersão compara séries agregadas e não indica relação '
             'de causa e efeito.'),
            (f'**Coorte de 2020.** Até {fim}, entre os vínculos dos ingressantes de 2020, {permanencia}% seguiam '
             f'em permanência, {conclusao}% concluíram o curso e {desistencia}% desistiram do curso de ingresso. '
             'Desistir do curso não é o mesmo que deixar o ensino superior, e cinco anos de acompanhamento não '
             'se comparam a coortes com dez anos.'),
        ]

    def _limitacoes(self):
        limitacoes = [
            'Inscrição no Enem não é presença nem aprovação.',
            'Os dados não identificam quem ingressou na graduação pelo Enem, nem a rede de origem dos ingressantes.',
            'As séries do Enem, da graduação e da coorte são agregadas e não acompanham as mesmas pessoas.',
        ]
        ultimo = int(self._dados['enem']['ano'].max())
        privada, anterior = self._inscricoes('Privada', ultimo), self._inscricoes('Privada', ultimo - 1)
        sem_informacao = self._inscricoes('Não dispõe da informação', ultimo)
        if pd.notna(privada) and pd.notna(anterior) and pd.notna(sem_informacao) and privada < 0.1 * anterior:
            limitacoes.append(
                f'Em {ultimo}, a categoria privada tem só {formatar_inteiro(privada)} inscrições, enquanto '
                f'{formatar_inteiro(sem_informacao)} registros não informam a rede. A causa não foi confirmada; '
                'comparações entre redes nesse ano exigem cautela.')
        return limitacoes

    def _analise(self, filtros):
        st.subheader('Análise interpretativa')
        for texto in self._textos_analise(filtros):
            st.markdown(texto)
        st.info('Os dados mostram a evolução das inscrições da rede pública e permitem descrever a trajetória '
                'de uma coorte, mas ainda não comprovam que mais estudantes da rede pública ingressaram pelo '
                'Enem e concluíram o curso. Isso exigiria dados que liguem as mesmas pessoas entre as etapas, '
                'o que os dados abertos usados aqui não oferecem.')
        st.markdown('**Limitações**')
        st.markdown('\n'.join(f'- {limitacao}' for limitacao in self._limitacoes()))
        with st.expander('Como cada indicador é calculado'):
            for indicador in self._catalogo:
                st.markdown(f'**{indicador.nome}** ({indicador.unidade})\n\n{indicador.descricao}\n\n'
                            f'Fórmula: {indicador.formula}\n\nLimitação: {indicador.limitacao}')

    def _rodape(self):
        st.divider()
        st.caption(f'Fontes: [Sinopses do Enem]({LINK_ENEM}) e [Sinopses da Educação Superior]({LINK_SUPERIOR}), '
                   'do Inep. Tabelas tratadas em data/processed/.')


def main():
    Dashboard(carregar_dados()).executar()


if __name__ == '__main__':
    main()
