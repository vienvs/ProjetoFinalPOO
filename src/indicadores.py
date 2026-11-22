from abc import ABC, abstractmethod

import pandas as pd

REDE_PUBLICA = 'Pública'
REDE_PRIVADA = 'Privada'
REDE_SEM_INFORMACAO = 'Não dispõe da informação'
REDES = (REDE_PUBLICA, REDE_PRIVADA, REDE_SEM_INFORMACAO)


def formatar_inteiro(valor):
    if pd.isna(valor):
        return '—'
    return f'{valor:,.0f}'.replace(',', '.')


def formatar_decimal(valor, casas=1, com_sinal=False):
    if pd.isna(valor):
        return '—'
    texto = f'{valor:+,.{casas}f}' if com_sinal else f'{valor:,.{casas}f}'
    return texto.replace(',', 'X').replace('.', ',').replace('X', '.')


def _inscritos_por_rede(enem):
    tabela = enem.pivot(index='ano', columns='rede_origem', values='inscritos_concluintes')
    return tabela.reindex(columns=list(REDES)).sort_index()


def _total_inscritos(por_rede):
    return por_rede.sum(axis=1, min_count=len(REDES))


def variacao_percentual(serie):
    anterior = serie.reindex(serie.index - 1)
    anterior.index = serie.index
    return (serie / anterior.where(anterior.ne(0)) - 1) * 100


def _como_serie_anual(valores):
    valores = pd.to_numeric(valores, errors='coerce').astype('float64')
    tabela = valores.rename('valor').rename_axis('ano').reset_index()
    tabela['ano'] = tabela['ano'].astype(int)
    return tabela.sort_values('ano').reset_index(drop=True)


class Indicador(ABC):
    def __init__(self, codigo, nome, descricao, formula, unidade, limitacao):
        self._codigo = codigo
        self._nome = nome
        self._descricao = descricao
        self._formula = formula
        self._unidade = unidade
        self._limitacao = limitacao

    @property
    def codigo(self):
        return self._codigo

    @property
    def nome(self):
        return self._nome

    @property
    def descricao(self):
        return self._descricao

    @property
    def formula(self):
        return self._formula

    @property
    def unidade(self):
        return self._unidade

    @property
    def limitacao(self):
        return self._limitacao

    @abstractmethod
    def _calcular(self, dados):
        pass

    @abstractmethod
    def formatar(self, valor):
        pass

    def serie(self, dados):
        tabela = self._calcular(dados)
        if list(tabela.columns) != ['ano', 'valor']:
            raise ValueError(f'{self._codigo}: a série deve ter as colunas ano e valor.')
        return tabela

    def valor_em(self, dados, ano):
        tabela = self.serie(dados)
        linha = tabela.loc[tabela['ano'].eq(ano), 'valor']
        return linha.iloc[0] if not linha.empty else float('nan')

    def __repr__(self):
        return f'{type(self).__name__}({self._codigo!r})'


class IndicadorContagem(Indicador):
    def formatar(self, valor):
        return formatar_inteiro(valor)

    def variacao_em(self, dados, ano):
        atual = self.valor_em(dados, ano)
        anterior = self.valor_em(dados, ano - 1)
        if pd.isna(atual) or pd.isna(anterior) or anterior == 0:
            return float('nan')
        return (atual / anterior - 1) * 100


class IndicadorPercentual(Indicador):
    def __init__(self, codigo, nome, descricao, formula, limitacao, com_sinal=False):
        super().__init__(codigo, nome, descricao, formula, '%', limitacao)
        self._com_sinal = com_sinal

    def formatar(self, valor):
        texto = formatar_decimal(valor, 1, com_sinal=self._com_sinal)
        return texto if texto == '—' else texto + '%'


class InscritosRedePublica(IndicadorContagem):
    def __init__(self):
        super().__init__(
            codigo='inscritos_publica',
            nome='Inscrições de concluintes da rede pública',
            descricao='Concluintes da rede pública (federal, estadual e municipal) inscritos no Enem.',
            formula='Categoria Pública da tabela 3.10 = Federal + Estadual + Municipal.',
            unidade='inscrições',
            limitacao='Inscrição não é presença nem aprovação.')

    def _calcular(self, dados):
        return _como_serie_anual(_inscritos_por_rede(dados['enem'])[REDE_PUBLICA])


class ParticipacaoPublicaNoTotal(IndicadorPercentual):
    def __init__(self):
        super().__init__(
            codigo='participacao_publica_no_total_pct',
            nome='Participação da rede pública nas inscrições',
            descricao='Parcela das inscrições de concluintes que vem da rede pública.',
            formula='Inscrições da rede pública ÷ total de concluintes inscritos × 100.',
            limitacao=('O total inclui os registros sem informação de rede. Descreve os inscritos; '
                       'não é a taxa de participação de todos os concluintes do país.'))

    def _calcular(self, dados):
        por_rede = _inscritos_por_rede(dados['enem'])
        total = _total_inscritos(por_rede)
        return _como_serie_anual(por_rede[REDE_PUBLICA] / total.where(total.ne(0)) * 100)


class ProporcaoSemInformacao(IndicadorPercentual):
    def __init__(self):
        super().__init__(
            codigo='sem_informacao_pct',
            nome='Inscrições sem informação da rede',
            descricao='Parcela das inscrições em que a rede de origem não foi informada.',
            formula='Inscrições sem informação ÷ total de concluintes inscritos × 100.',
            limitacao=('Funciona como alerta de qualidade: quanto maior, menos confiável é a '
                       'comparação entre redes. Não redistribuímos esses registros.'))

    def _calcular(self, dados):
        por_rede = _inscritos_por_rede(dados['enem'])
        total = _total_inscritos(por_rede)
        return _como_serie_anual(por_rede[REDE_SEM_INFORMACAO] / total.where(total.ne(0)) * 100)


class VariacaoAnualPublica(IndicadorPercentual):
    def __init__(self):
        super().__init__(
            codigo='variacao_anual_publica_pct',
            nome='Variação anual das inscrições públicas',
            descricao='Quanto as inscrições da rede pública cresceram ou caíram em relação à edição anterior.',
            formula='(inscrições públicas do ano ÷ inscrições públicas do ano anterior − 1) × 100.',
            limitacao='O primeiro ano da série não tem variação. A causa das oscilações não é medida aqui.',
            com_sinal=True)

    def _calcular(self, dados):
        publica = _inscritos_por_rede(dados['enem'])[REDE_PUBLICA]
        return _como_serie_anual(variacao_percentual(publica))


class IngressantesGraduacao(IndicadorContagem):
    def __init__(self):
        super().__init__(
            codigo='ingressantes_graduacao',
            nome='Ingressantes na graduação',
            descricao='Ingressos na graduação, presencial e a distância, em todas as organizações acadêmicas.',
            formula='Coluna "ingressantes_graduacao" da tabela 4.4 do Censo da Educação Superior.',
            unidade='ingressos',
            limitacao=('Inclui todas as redes de origem e todas as formas de ingresso: '
                       'não identifica quem entrou pelo Enem.'))

    def _calcular(self, dados):
        return _como_serie_anual(dados['superior'].set_index('ano')['ingressantes_graduacao'])


class IndicadorTrajetoria(IndicadorPercentual):
    def _calcular(self, dados):
        trajetoria = dados['trajetoria'].sort_values('ano_referencia').set_index('ano_referencia')
        falecimentos = trajetoria['falecimentos_no_ano'].cumsum(skipna=False)
        base = trajetoria['vinculos_ingressantes_coorte'] - falecimentos
        return _como_serie_anual(self._numerador(trajetoria) / base.where(base.gt(0)) * 100)

    @abstractmethod
    def _numerador(self, trajetoria):
        pass


LIMITE_TRAJETORIA = ('Conta vínculos com cursos, não pessoas únicas. A coorte de 2020 tem cinco anos de '
                     'acompanhamento e não se compara diretamente a coortes com dez anos.')


class PermanenciaCoorte(IndicadorTrajetoria):
    def __init__(self):
        super().__init__(
            codigo='permanencia_coorte',
            nome='Permanência da coorte 2020',
            descricao='Vínculos da coorte de 2020 ainda ativos no curso de ingresso.',
            formula='Vínculos em permanência no ano ÷ (vínculos iniciais − falecimentos acumulados) × 100.',
            limitacao=LIMITE_TRAJETORIA)

    def _numerador(self, trajetoria):
        return trajetoria['vinculos_permanencia']


class ConclusaoAcumuladaCoorte(IndicadorTrajetoria):
    def __init__(self):
        super().__init__(
            codigo='conclusao_acumulada_coorte',
            nome='Conclusão acumulada da coorte 2020',
            descricao='Parte da coorte de 2020 que concluiu o curso de ingresso até o ano de referência.',
            formula='Soma das conclusões anuais até o ano ÷ (vínculos iniciais − falecimentos acumulados) × 100.',
            limitacao=LIMITE_TRAJETORIA)

    def _numerador(self, trajetoria):
        return trajetoria['conclusoes_no_ano'].cumsum(skipna=False)


class DesistenciaAcumuladaCoorte(IndicadorTrajetoria):
    def __init__(self):
        super().__init__(
            codigo='desistencia_acumulada_coorte',
            nome='Desistência acumulada da coorte 2020',
            descricao='Parte da coorte de 2020 que desistiu do curso de ingresso até o ano de referência.',
            formula='Soma das desistências anuais até o ano ÷ (vínculos iniciais − falecimentos acumulados) × 100.',
            limitacao=('Desistência do curso não significa saída do ensino superior. ' + LIMITE_TRAJETORIA))

    def _numerador(self, trajetoria):
        return trajetoria['desistencias_no_ano'].cumsum(skipna=False)


class CatalogoIndicadores:
    def __init__(self, indicadores):
        self._indicadores = {}
        for indicador in indicadores:
            if indicador.codigo in self._indicadores:
                raise ValueError(f'Código de indicador repetido: {indicador.codigo}')
            self._indicadores[indicador.codigo] = indicador

    @classmethod
    def padrao(cls):
        return cls([InscritosRedePublica(), ParticipacaoPublicaNoTotal(),
                    ProporcaoSemInformacao(), VariacaoAnualPublica(),
                    IngressantesGraduacao(), PermanenciaCoorte(),
                    ConclusaoAcumuladaCoorte(), DesistenciaAcumuladaCoorte()])

    @property
    def codigos(self):
        return list(self._indicadores)

    def __len__(self):
        return len(self._indicadores)

    def __iter__(self):
        return iter(self._indicadores.values())

    def __getitem__(self, codigo):
        return self._indicadores[codigo]

    def tabela(self, dados):
        resultado = None
        for indicador in self:
            serie = indicador.serie(dados).rename(columns={'valor': indicador.codigo})
            resultado = serie if resultado is None else resultado.merge(serie, on='ano', how='outer')
        return resultado.sort_values('ano').reset_index(drop=True)

    def tabela_longa(self, dados, codigos=None):
        partes = []
        for codigo in (codigos or self.codigos):
            indicador = self[codigo]
            parte = indicador.serie(dados)
            parte['codigo'] = indicador.codigo
            parte['indicador'] = indicador.nome
            partes.append(parte)
        return pd.concat(partes, ignore_index=True)
