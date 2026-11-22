from abc import ABC, abstractmethod
from pathlib import Path

import plotly.express as px

CORES_REDES = {'Pública': '#147d92', 'Privada': '#e68a36', 'Não dispõe da informação': '#9aa6b2'}
CORES_TRAJETORIA = {'permanencia_coorte': '#2563b0',
                    'conclusao_acumulada_coorte': '#2a7d5f',
                    'desistencia_acumulada_coorte': '#b85c5c'}

AVISO_ENEM = ('Rede registrada na sinopse; sem informação preservada. '
              'Em 2024, 48% das inscrições de concluintes ficaram sem rede informada.')
AVISO_TRAJETORIA = ('Vínculos com cursos, não pessoas únicas. A coorte de 2020 tem cinco anos de '
                    'acompanhamento e não se compara diretamente a coortes com dez anos.')


def _periodo(tabela):
    inicio, fim = int(tabela['ano'].min()), int(tabela['ano'].max())
    return str(inicio) if inicio == fim else f'{inicio}–{fim}'


class Grafico(ABC):
    dados_necessarios = ()
    titulo_legenda = 'Rede da escola de origem'

    def __init__(self, nome, titulo, subtitulo, fonte, comentario, aviso=AVISO_ENEM):
        self._nome = nome
        self._titulo = titulo
        self._subtitulo = subtitulo
        self._fonte = fonte
        self._comentario = comentario
        self._aviso = aviso

    @property
    def nome(self):
        return self._nome

    @property
    def comentario(self):
        return self._comentario

    def disponivel(self, dados):
        return all(chave in dados for chave in self.dados_necessarios)

    def construir(self, dados, **opcoes):
        figura = self._desenhar(dados, **opcoes)
        titulo, subtitulo = self._titulos(dados, **opcoes)
        return self._acabamento(figura, titulo, subtitulo)

    @abstractmethod
    def _desenhar(self, dados, **opcoes):
        pass

    def _titulos(self, dados, **opcoes):
        periodo = _periodo(dados[self.dados_necessarios[0]])
        return self._titulo, self._subtitulo.format(periodo=periodo)

    def _acabamento(self, figura, titulo, subtitulo):
        figura.update_layout(
            template='plotly_white', height=580,
            title=dict(text=f'{titulo}<br><sup>{subtitulo}</sup>', font=dict(size=21)),
            font=dict(family='Arial', size=13, color='#23334a'),
            margin=dict(l=85, r=40, t=110, b=150),
            legend_title_text=self.titulo_legenda,
        )
        figura.add_annotation(x=0, y=-0.24, xref='paper', yref='paper', showarrow=False,
                              xanchor='left', align='left',
                              text=self._fonte + '<br>' + self._aviso, font=dict(size=11))
        return figura


class GraficoLinhas(Grafico):
    dados_necessarios = ('enem',)

    def __init__(self):
        super().__init__(
            nome='01_linhas',
            titulo='Inscrições de concluintes no Enem por rede registrada',
            subtitulo='Brasil · {periodo} · contagem de inscrições, não aprovações',
            fonte='Fonte: Inep, Sinopses do Enem, tabela 3.10 de cada edição.',
            comentario=('Cada linha é uma rede registrada na sinopse do Enem. A leitura exige cautela com a '
                        'cobertura de cada categoria e com as particularidades da pandemia; '
                        'o gráfico sozinho não explica as causas das oscilações.'))

    def _desenhar(self, dados, **opcoes):
        enem = dados['enem'].sort_values('ano')
        figura = px.line(enem, x='ano', y='inscritos_concluintes', color='rede_origem', markers=True,
                         color_discrete_map=CORES_REDES,
                         labels={'ano': 'Edição do Enem', 'inscritos_concluintes': 'Inscrições de concluintes',
                                 'rede_origem': 'Rede de origem'})
        figura.update_xaxes(dtick=1)
        figura.update_yaxes(rangemode='tozero')
        return figura


class GraficoBarras(Grafico):
    dados_necessarios = ('enem',)

    def __init__(self):
        super().__init__(
            nome='02_barras',
            titulo='Inscrições por rede registrada',
            subtitulo='Brasil · {periodo} · barras não representam taxas de acesso',
            fonte='Fonte: Inep, Sinopses do Enem, tabela 3.10.',
            comentario=('As barras contam as inscrições conforme a rede registrada. Em 2024, 519 aparecem '
                        'na categoria privada e 775.870 ficaram sem rede informada.'))

    def _desenhar(self, dados, **opcoes):
        enem = dados['enem'].sort_values('ano')
        figura = px.bar(enem, x='ano', y='inscritos_concluintes', color='rede_origem', barmode='group',
                        color_discrete_map=CORES_REDES,
                        labels={'ano': 'Edição do Enem', 'inscritos_concluintes': 'Inscrições de concluintes',
                                'rede_origem': 'Rede de origem'})
        figura.update_xaxes(dtick=1)
        return figura


class GraficoSetores(Grafico):
    dados_necessarios = ('enem',)

    def __init__(self):
        super().__init__(
            nome='03_setores',
            titulo='Composição das inscrições de concluintes',
            subtitulo='Brasil · inclui registros sem informação da rede',
            fonte='Fonte: Inep, Sinopses do Enem, tabela 3.10. Denominador: todos os concluintes inscritos.',
            comentario=('O setor cinza integra o denominador: os registros sem informação da rede '
                        'não foram redistribuídos entre as redes pública e privada.'))

    @staticmethod
    def _ano(dados, opcoes):
        ano = opcoes.get('ano')
        return int(ano) if ano is not None else int(dados['enem']['ano'].max())

    def _titulos(self, dados, **opcoes):
        return f'{self._titulo} · {self._ano(dados, opcoes)}', self._subtitulo

    def _desenhar(self, dados, **opcoes):
        enem = dados['enem']
        escolhido = enem[enem['ano'].eq(self._ano(dados, opcoes))]
        figura = px.pie(escolhido, names='rede_origem', values='inscritos_concluintes',
                        color='rede_origem', color_discrete_map=CORES_REDES, hole=0.45)
        figura.update_traces(textinfo='percent', textposition='outside',
                             hovertemplate='%{label}<br>%{value:,.0f} inscrições<br>%{percent}<extra></extra>')
        return figura


class GraficoDispersao(Grafico):
    dados_necessarios = ('enem', 'superior')

    def __init__(self):
        super().__init__(
            nome='04_dispersao',
            titulo='Enem e ingresso na graduação: séries agregadas',
            subtitulo='Brasil · {periodo} · sem vínculo individual ou inferência causal',
            fonte='Fonte: Inep, Enem 3.10 e Educação Superior 4.4. Mesmos anos, populações distintas.',
            comentario=('Cada ponto é um ano. Os ingressantes incluem todas as formas de ingresso, redes de origem, '
                        'modalidades e organizações acadêmicas. Os pontos não acompanham indivíduos, não formam '
                        'um funil e não comprovam causalidade.'))

    def _desenhar(self, dados, **opcoes):
        enem = dados['enem']
        publica = enem.loc[enem['rede_origem'].eq('Pública'), ['ano', 'inscritos_concluintes']]
        superior = dados['superior'][['ano', 'ingressantes_graduacao']]
        juntos = publica.merge(superior, on='ano', validate='one_to_one')
        figura = px.scatter(juntos, x='inscritos_concluintes', y='ingressantes_graduacao', text='ano',
                            color_discrete_sequence=[CORES_REDES['Pública']],
                            labels={'inscritos_concluintes': 'Inscrições de concluintes da rede pública no Enem',
                                    'ingressantes_graduacao': 'Ingressantes na graduação · todas as IES e formas'})
        figura.update_traces(marker_size=14, textposition='top center')
        figura.update_xaxes(rangemode='tozero')
        figura.update_yaxes(rangemode='tozero')
        return figura


class GraficoTrajetoria(Grafico):
    dados_necessarios = ('trajetoria_pct',)
    titulo_legenda = 'Situação dos vínculos'

    def __init__(self):
        super().__init__(
            nome='05_trajetoria',
            titulo='Trajetória da coorte de ingressantes de 2020',
            subtitulo='Brasil · {periodo} · % dos vínculos dos ingressantes de 2020 no curso de ingresso',
            fonte='Fonte: Inep, Indicadores de Trajetória da Educação Superior (coorte 2020).',
            comentario=('Os percentuais usam como base os vínculos dos ingressantes de 2020. Desistência é do curso '
                        'de ingresso, não saída do ensino superior. Cinco anos de acompanhamento não se comparam '
                        'a coortes com dez anos.'),
            aviso=AVISO_TRAJETORIA)

    def _desenhar(self, dados, **opcoes):
        trajetoria = dados['trajetoria_pct'].sort_values('ano')
        reserva = px.colors.qualitative.Plotly
        cores = {}
        for posicao, linha in enumerate(trajetoria.drop_duplicates('codigo').itertuples()):
            cores[linha.indicador] = CORES_TRAJETORIA.get(linha.codigo, reserva[posicao % len(reserva)])
        figura = px.line(trajetoria, x='ano', y='valor', color='indicador', markers=True,
                         color_discrete_map=cores,
                         labels={'ano': 'Ano de referência', 'valor': '% dos vínculos da coorte 2020',
                                 'indicador': 'Situação'})
        figura.update_xaxes(dtick=1)
        figura.update_yaxes(range=[0, 100], ticksuffix='%')
        return figura


class Visualizador:
    def __init__(self, graficos=None):
        graficos = graficos if graficos is not None else self.graficos_padrao()
        self._graficos = {grafico.nome: grafico for grafico in graficos}

    @staticmethod
    def graficos_padrao():
        return [GraficoLinhas(), GraficoBarras(), GraficoSetores(), GraficoDispersao(), GraficoTrajetoria()]

    @property
    def nomes(self):
        return list(self._graficos)

    def grafico(self, nome):
        return self._graficos[nome]

    def figura(self, nome, dados, **opcoes):
        return self._graficos[nome].construir(dados, **opcoes)

    def todas(self, dados, **opcoes):
        return {nome: grafico.construir(dados, **opcoes)
                for nome, grafico in self._graficos.items() if grafico.disponivel(dados)}

    def exportar(self, figuras, pasta):
        pasta = Path(pasta)
        pasta.mkdir(parents=True, exist_ok=True)
        for nome, figura in figuras.items():
            figura.write_html(pasta / f'{nome}.html', include_plotlyjs='directory',
                              config={'responsive': True, 'displaylogo': False})
        return pasta
