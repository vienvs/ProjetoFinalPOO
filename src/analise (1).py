import pandas as pd


class AnalisadorColeta:
    def __init__(self, enem):
        self._enem = enem.copy()

    def resumo(self):
        tabela = self._enem.pivot(index='ano', columns='rede_origem', values='inscritos_concluintes')
        tabela = tabela.rename(columns={'Pública':'inscritos_publica', 'Privada':'inscritos_privada',
                                         'Não dispõe da informação':'inscritos_sem_informacao'})
        tabela['total_concluintes_inscritos'] = tabela.sum(axis=1, min_count=3)
        total = tabela['total_concluintes_inscritos'].where(tabela['total_concluintes_inscritos'].ne(0))
        tabela['participacao_publica_no_total_pct'] = tabela.inscritos_publica / total * 100
        tabela['sem_informacao_pct'] = tabela.inscritos_sem_informacao / total * 100
        tabela['variacao_anual_publica_pct'] = tabela.inscritos_publica.pct_change(fill_method=None) * 100
        return tabela.sort_index().reset_index().rename_axis(None, axis=1)
