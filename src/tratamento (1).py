import json
import numbers
import unicodedata
from pathlib import Path

import pandas as pd
from openpyxl.utils import get_column_letter

from src.fontes import FonteExcel, ROOT, fontes_oficiais, localizar_planilha


def normalizar(valor):
    texto = unicodedata.normalize('NFKD', str(valor))
    return ' '.join(''.join(c for c in texto if not unicodedata.combining(c)).lower().split())


def contagem(valor):
    if pd.isna(valor) or str(valor).strip() in {'', '-', '...', '…'}:
        return pd.NA
    if not isinstance(valor, numbers.Real) or valor < 0 or int(valor) != valor:
        raise ValueError(f'Contagem inesperada: {valor!r}')
    return int(valor)


def soma_completa(valores):
    valores = list(valores)
    return pd.NA if any(pd.isna(v) for v in valores) else sum(valores)


def conferir_soma(partes, total, contexto):
    calculado = soma_completa(partes)
    if pd.isna(calculado) or pd.isna(total) or calculado != total:
        raise ValueError(f'Total não reconciliado em {contexto}: {calculado} != {total}')


class ExtratorSinopse:
    def __init__(self):
        self._evidencias = []

    @property
    def evidencias(self):
        return list(self._evidencias)

    def nacional(self, arquivo, aba, ano, termos_titulo):
        tabela = FonteExcel(arquivo, aba, limite_linhas=24).carregar()
        titulo = ' '.join(str(v) for v in tabela.iloc[3] if pd.notna(v))
        if str(ano) not in titulo or any(normalizar(t) not in normalizar(titulo) for t in termos_titulo):
            raise ValueError(f'Título inesperado: {arquivo.name}/{aba}: {titulo}')
        linhas = tabela.index[tabela[0].map(normalizar).isin(['brasil', 'total brasil'])]
        if len(linhas) != 1:
            raise ValueError(f'Esperada uma linha Brasil em {arquivo.name}/{aba}')
        indice = int(linhas[0])
        self._evidencias.append({
            'ano': ano, 'arquivo': arquivo.name, 'aba': aba, 'titulo': titulo,
            'linha_excel': indice + 1,
            'cabecalho': [[None if pd.isna(v) else v for v in row]
                         for row in tabela.iloc[5:indice, :min(tabela.shape[1], 100)].values.tolist()],
            'celulas': {f'{get_column_letter(i+1)}{indice+1}': v
                        for i, v in enumerate(tabela.iloc[indice])
                        if pd.notna(v) and i < 100},
        })
        return tabela, tabela.iloc[indice]

    def enem(self, arquivo, ano):
        tabela, brasil = self.nacional(arquivo, '3.10', ano, ['concluintes', 'dependência'])

        esperado = ['Federal', 'Estadual', 'Municipal', 'Privada']
        if [normalizar(v) for v in tabela.iloc[7, 3:7]] != [normalizar(v) for v in esperado]:
            raise ValueError(f'Layout do Enem mudou em {ano}')
        if 'informacao' not in normalizar(tabela.iloc[6, 7]):
            raise ValueError('Categoria sem informação não identificada')
        total = contagem(brasil.iloc[2])
        federal, estadual, municipal, privada, ignorada = map(contagem, brasil.iloc[3:8])
        publica = soma_completa([federal, estadual, municipal])
        conferir_soma([publica, privada, ignorada], total, f'Enem {ano}')
        return [dict(ano=ano, abrangencia='Brasil', rede_origem=rede,
                     inscritos_concluintes=valor, total_concluintes_inscritos=total,
                     fonte_id=f'enem_{ano}', aba='3.10')
                for rede, valor in [('Pública', publica), ('Privada', privada),
                                    ('Não dispõe da informação', ignorada)]]

    def superior(self, arquivo, ano):
        tabela, brasil = self.nacional(arquivo, '4.4', ano, ['ingressantes', 'graduação'])
        if normalizar(tabela.iloc[6, 4]) != 'total' or normalizar(tabela.iloc[6, 5]) != 'universidade':
            raise ValueError(f'Layout da Educação Superior mudou em {ano}')

        total, universidades = map(contagem, brasil.iloc[4:6])

        conferir_soma([contagem(brasil.iloc[i]) for i in [5, 34, 63, 92]], total,
                      f'Educação Superior {ano}')
        return dict(ano=ano, abrangencia='Brasil', categoria_ies='Todas',
                    modalidade='Presencial e a distância', forma_ingresso='Todas',
                    ingressantes_graduacao=total, ingressantes_universidades=universidades,
                    fonte_id=f'superior_{ano}', aba='4.4')

    def basica(self, arquivo, ano):
        aba = 'Ensino Médio 1.25'
        tabela, brasil = self.nacional(arquivo, aba, ano, ['matrículas', 'ensino médio'])
        if [normalizar(v) for v in tabela.iloc[8, 6:10]] != ['federal', 'estadual', 'municipal', 'privada']:
            raise ValueError(f'Layout da Educação Básica mudou em {ano}')
        total = contagem(brasil.iloc[4])

        dependencias = [soma_completa(contagem(brasil.iloc[i]) for i in range(col, 30, 5))
                        for col in range(6, 10)]
        conferir_soma(dependencias, total, f'Educação Básica {ano}')
        return [dict(ano=ano, abrangencia='Brasil', rede_origem=rede,
                     matriculas_em_regular=valor,
                     universo='Todas as séries do ensino médio regular; não são concluintes',
                     fonte_id=f'basica_{ano}', aba=aba)
                for rede, valor in [('Pública', soma_completa(dependencias[:3])),
                                    ('Privada', dependencias[3])]]


def tabela_trajetoria(arquivo):
    tabela = FonteExcel(arquivo, 'INDICADORES_TRAJETORIA').carregar()
    cabecalho = tabela.iloc[8].tolist()
    df = tabela.iloc[9:].copy()
    df.columns = cabecalho
    df = df[df['CO_IES'].notna()].copy()

    rodape = df['CO_IES'].map(normalizar).eq('fonte: censo da educacao superior/inep.')
    if rodape.sum() > 1 or df.loc[rodape, 'CO_CURSO'].notna().any():
        raise ValueError('Rodapé de trajetória inesperado')
    df = df.loc[~rodape].copy()
    chave = ['CO_IES', 'CO_CURSO', 'NU_ANO_INGRESSO', 'NU_ANO_REFERENCIA']
    if df.duplicated(chave).any():
        raise ValueError('Duplicidades na chave curso/coorte/ano; investigar antes de agregar')
    numericas = ['NU_ANO_INGRESSO', 'NU_ANO_REFERENCIA', 'QT_INGRESSANTE',
                 'QT_PERMANENCIA', 'QT_CONCLUINTE', 'QT_DESISTENCIA', 'QT_FALECIDO']
    for col in numericas:
        df[col] = pd.to_numeric(df[col], errors='raise').astype('Int64')
    if set(df['NU_ANO_INGRESSO'].dropna()) != {2020}:
        raise ValueError('Coorte diferente de 2020')
    if df[numericas[:2]].isna().any().any():
        raise ValueError('Ano de ingresso/referência ausente na trajetória')
    grupos = df.groupby('NU_ANO_REFERENCIA')


    soma = grupos[numericas[2:]].agg(lambda serie: serie.sum(min_count=len(serie)))
    for coluna in numericas[2:]:
        soma['ausentes_' + coluna.lower()] = grupos[coluna].apply(lambda serie: int(serie.isna().sum()))
    soma['cursos_observados'] = df.groupby('NU_ANO_REFERENCIA').size()
    soma = soma.reset_index().rename(columns={
        'NU_ANO_REFERENCIA':'ano_referencia', 'QT_INGRESSANTE':'vinculos_ingressantes_coorte',
        'QT_PERMANENCIA':'vinculos_permanencia', 'QT_CONCLUINTE':'conclusoes_no_ano',
        'QT_DESISTENCIA':'desistencias_no_ano', 'QT_FALECIDO':'falecimentos_no_ano'})
    soma['ano_ingresso'] = 2020
    soma['fonte_id'] = 'trajetoria_2020_2024'
    soma['unidade'] = 'Vínculos em cursos; não pessoas únicas'
    amostra = df.head(25)
    perfil = dict(registros=int(len(df)), cursos=int(df[['CO_IES','CO_CURSO']].drop_duplicates().shape[0]),
                  linhas_de_rodape=int(rodape.sum()), duplicidades_chave=int(df.duplicated(chave).sum()),
                  tipos={c:str(t) for c,t in df.dtypes.items()},
                  ausencias={c:int(v) for c,v in df.isna().sum().items()},
                  nota='Ausências geográficas preservadas; agregação nacional inclui esses cursos.')
    return soma, amostra, perfil


def preparar(baixar=False):
    fontes = fontes_oficiais()
    extrator = ExtratorSinopse()
    registros = {'enem': [], 'superior': [], 'basica': []}
    saida = ROOT/'data/processed'
    saida.mkdir(parents=True, exist_ok=True)
    for fonte in fontes:
        print('Processando', fonte['id'], flush=True)
        arquivo = localizar_planilha(fonte, baixar)
        base = fonte['base']
        if base == 'trajetoria':
            trajetoria, amostra, perfil_trajetoria = tabela_trajetoria(arquivo)
        else:
            resultado = getattr(extrator, base)(arquivo, fonte['ano'])
            registros[base].extend(resultado if isinstance(resultado, list) else [resultado])
    tabelas = {base: pd.DataFrame(linhas) for base, linhas in registros.items()}
    for base, df in tabelas.items():
        chave = ['ano'] + (['rede_origem'] if base in ['enem', 'basica'] else [])
        if df.duplicated(chave).any():
            raise ValueError(f'Chave duplicada em {base}')
        if set(df['ano']) != set(range(2020, 2025)):
            raise ValueError(f'Anos incompletos em {base}')
    nomes = {'enem':'enem_brasil_rede.csv', 'superior':'superior_brasil.csv',
             'basica':'basica_matriculas_brasil.csv'}
    for base, df in tabelas.items():
        df.to_csv(saida/nomes[base], index=False, encoding='utf-8')
    trajetoria.to_csv(saida/'trajetoria_coorte_2020.csv', index=False, encoding='utf-8')
    amostra.to_csv(saida/'trajetoria_amostra_25_linhas.csv', index=False, encoding='utf-8')
    (saida/'perfil_trajetoria.json').write_text(
        json.dumps(perfil_trajetoria, ensure_ascii=False, indent=2), encoding='utf-8')
    (saida/'fontes.json').write_text(json.dumps(fontes, ensure_ascii=False, indent=2), encoding='utf-8')
    (saida/'evidencias_extracao.json').write_text(
        json.dumps(extrator.evidencias, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Pronto: tabelas nacionais e evidências em dados/processed.', flush=True)
