import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd
from openpyxl import Workbook

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.preparar_dados import gerar_resumo
from src.analise import AnalisadorColeta
from src.fontes import ARQUIVOS, PASTA_PROCESSADOS, FonteCSV, FonteDados
from src.tratamento import ExtratorSinopse

ENEM = {
    2020: (685864, 218705, 491258, 1395827),
    2021: (603041, 210765, 337051, 1150857),
    2022: (724523, 227421, 365616, 1317560),
    2023: (728878, 229628, 442658, 1401164),
    2024: (841213, 519, 775870, 1617602),
}


def enem_df():
    linhas = []
    for ano, (pub, priv, sem, total) in ENEM.items():
        for rede, valor in [('Pública', pub), ('Privada', priv), ('Não dispõe da informação', sem)]:
            linhas.append(dict(ano=ano, abrangencia='Brasil', rede_origem=rede,
                               inscritos_concluintes=valor, total_concluintes_inscritos=total,
                               fonte_id=f'enem_{ano}', aba='3.10'))
    return pd.DataFrame(linhas)


class TestFontes(unittest.TestCase):
    def test_fonte_dados_e_abstrata(self):
        with self.assertRaises(TypeError):
            FonteDados('x.csv')

    def test_fonte_csv_carrega(self):
        with tempfile.TemporaryDirectory() as d:
            caminho = Path(d) / 'enem.csv'
            enem_df().to_csv(caminho, index=False, encoding='utf-8')
            self.assertEqual(FonteCSV(caminho).carregar().shape, (15, 7))


class TestAnaliseColeta(unittest.TestCase):
    def setUp(self):
        self.enem = enem_df()
        self.resumo = AnalisadorColeta(self.enem).resumo()

    def test_totais_conferem_com_publicado(self):
        conferencia = self.enem.groupby('ano').agg(
            soma_categorias=('inscritos_concluintes', 'sum'),
            total_publicado=('total_concluintes_inscritos', 'first'))
        self.assertTrue(conferencia.soma_categorias.eq(conferencia.total_publicado).all())

    def test_chaves_e_anos(self):
        self.assertEqual(set(self.enem.ano), set(range(2020, 2025)))
        self.assertFalse(self.enem.duplicated(['ano', 'rede_origem']).any())

    def test_indicadores_do_notebook(self):
        r = self.resumo.set_index('ano')
        self.assertEqual(r.loc[2020, 'total_concluintes_inscritos'], 1395827)
        self.assertAlmostEqual(r.loc[2020, 'participacao_publica_no_total_pct'], 49.14, places=2)
        self.assertAlmostEqual(r.loc[2024, 'sem_informacao_pct'], 47.96, places=2)
        self.assertTrue(pd.isna(r.loc[2020, 'variacao_anual_publica_pct']))
        self.assertAlmostEqual(r.loc[2021, 'variacao_anual_publica_pct'], -12.08, places=2)
        self.assertAlmostEqual(r.loc[2022, 'variacao_anual_publica_pct'], 20.14, places=2)

    def test_variacao_exige_ano_anterior_e_base_positiva(self):
        dados = self.enem[self.enem.ano.ne(2021)].copy()
        dados.loc[dados.ano.eq(2022), 'inscritos_concluintes'] = 0
        resumo = AnalisadorColeta(dados).resumo().set_index('ano')
        self.assertTrue(pd.isna(resumo.loc[2022, 'variacao_anual_publica_pct']))
        self.assertTrue(pd.isna(resumo.loc[2023, 'variacao_anual_publica_pct']))

    def test_nao_altera_entrada(self):
        copia = self.enem.copy()
        AnalisadorColeta(self.enem).resumo()
        pd.testing.assert_frame_equal(self.enem, copia)


class TestExtratorEnem(unittest.TestCase):
    def test_linha_brasil_2020(self):
        with tempfile.TemporaryDirectory() as d:
            arquivo = Path(d) / 'enem.xlsx'
            wb = Workbook()
            ws = wb.active
            ws.title = '3.10'
            linhas = [(None,) * 8] * 3
            linhas += [('3.10 - Número de Concluintes no Enem segundo a Dependência Administrativa por Região Geográfica e Unidade da Federação - 2020',) + (None,) * 7]
            linhas += [(None,) * 8] * 2
            linhas += [(None,) * 7 + ('Não dispõe da informação',)]
            linhas += [(None, None, None, 'Federal', 'Estadual', 'Municipal', 'Privada', None)]
            linhas += [(None,) * 8]
            linhas += [('Brasil', None, 1395827, 46594, 630939, 8331, 218705, 491258)]
            for linha in linhas:
                ws.append(linha)
            wb.save(arquivo)
            registros = ExtratorSinopse().enem(arquivo, 2020)
        valores = {r['rede_origem']: r['inscritos_concluintes'] for r in registros}
        self.assertEqual(valores, {'Pública': 685864, 'Privada': 218705, 'Não dispõe da informação': 491258})


class TestPreparacao(unittest.TestCase):
    def test_conferencia_com_as_celulas_das_sinopses(self):
        import json

        evidencias = json.loads((PASTA_PROCESSADOS / 'evidencias_extracao.json').read_text('utf-8'))
        enem = FonteCSV(PASTA_PROCESSADOS / ARQUIVOS['enem']).carregar()
        resumo = AnalisadorColeta(enem).resumo().set_index('ano')
        fontes_enem = [fonte for fonte in evidencias if fonte['aba'] == '3.10']
        self.assertEqual(sorted(f['ano'] for f in fontes_enem), list(range(2020, 2025)))
        for fonte in fontes_enem:
            linha = fonte['linha_excel']
            celulas = fonte['celulas']
            publica = sum(celulas[f'{coluna}{linha}'] for coluna in 'DEF')
            resultado = resumo.loc[fonte['ano']]
            self.assertEqual(resultado['inscritos_publica'], publica)
            self.assertEqual(resultado['total_concluintes_inscritos'], celulas[f'C{linha}'])

    def test_reprocessar_e_recusar_total_inconsistente(self):
        with tempfile.TemporaryDirectory() as diretorio:
            pasta = Path(diretorio)
            for nome in ARQUIVOS.values():
                shutil.copy(PASTA_PROCESSADOS / nome, pasta / nome)
            gerar_resumo(pasta)
            arquivo = pasta / 'indicadores_exploratorios.csv'
            esperado = FonteCSV(PASTA_PROCESSADOS / arquivo.name).carregar()
            pd.testing.assert_frame_equal(FonteCSV(arquivo).carregar(), esperado)
            original = arquivo.read_bytes()
            caminho = pasta / ARQUIVOS['enem']
            enem = FonteCSV(caminho).carregar()
            enem.loc[0, 'inscritos_concluintes'] += 1
            enem.to_csv(caminho, index=False)
            with self.assertRaisesRegex(ValueError, 'total'):
                gerar_resumo(pasta)
            self.assertEqual(arquivo.read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
