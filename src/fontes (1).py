import hashlib
import os
import shutil
import ssl
import subprocess
import sys
import zipfile
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen

import pandas as pd
from openpyxl import load_workbook


class FonteDados(ABC):
    def __init__(self, caminho):
        self._caminho = Path(caminho)

    @property
    def caminho(self):
        return self._caminho

    @abstractmethod
    def carregar(self):
        ...


class FonteCSV(FonteDados):
    def carregar(self):
        return pd.read_csv(self.caminho, encoding='utf-8')


class FonteExcel(FonteDados):
    def __init__(self, caminho, aba, limite_linhas=None):
        super().__init__(caminho)
        self._aba = aba
        self._limite_linhas = limite_linhas

    def carregar(self):


        livro = load_workbook(self.caminho, read_only=True, data_only=True)
        try:
            if self._aba not in livro.sheetnames:
                raise ValueError(f'Aba ausente: {self._aba} em {self.caminho.name}')
            return pd.DataFrame(livro[self._aba].iter_rows(
                max_row=self._limite_linhas, values_only=True))
        finally:
            livro.close()


ROOT = Path(__file__).resolve().parent.parent


PAGINA = 'https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/'
DOWNLOAD = 'https://download.inep.gov.br/'

def fontes_oficiais():
    fontes = []
    for ano in range(2020, 2025):
        nome_enem = 'Sinopse_Enem2020.zip' if ano == 2020 else f'sinopse_enem_{ano}.zip'
        prefixo_basica = 'sinopses_estatisticas' if ano <= 2022 else 'sinopse_estatistica'
        for base, pagina, url, aba in [
            ('enem', 'sinopses-estatisticas/enem',
             f'informacoes_estatisticas/sinopses_estatisticas/sinopses_enem/{ano}/{nome_enem}', '3.10'),
            ('superior', 'sinopses-estatisticas/educacao-superior',
             f'informacoes_estatisticas/sinopses_estatisticas/sinopses_educacao_superior/sinopse_educacao_superior_{ano}.zip', '4.4'),
            ('basica', 'sinopses-estatisticas/educacao-basica',
             f'dados_abertos/sinopses_estatisticas/{prefixo_basica}_censo_escolar_{ano}.zip', 'Ensino Médio 1.25'),
        ]:
            fontes.append(dict(id=f'{base}_{ano}', base=base, ano=ano,
                               pagina=PAGINA+pagina, url=DOWNLOAD+url, aba=aba))
    fontes.append(dict(id='trajetoria_2020_2024', base='trajetoria', ano='2020-2024',
                       pagina=PAGINA+'indicadores-educacionais/indicadores-de-trajetoria-da-educacao-superior',
                       url=DOWNLOAD+'informacoes_estatisticas/indicadores_educacionais/indicadores_trajetoria_es_2020_2024.zip',
                       aba='INDICADORES_TRAJETORIA'))
    return fontes

def baixar_zip(url, destino):

    import truststore
    contexto = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    temporario = destino.with_suffix('.part')
    if sys.platform == 'win32':


        ambiente = {**os.environ, 'INEP_COLETA_URL':url, 'INEP_COLETA_DESTINO':str(temporario)}
        subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command',
                        "$ProgressPreference='SilentlyContinue'; "
                        'Invoke-WebRequest -UseBasicParsing -Uri $env:INEP_COLETA_URL '
                        '-OutFile $env:INEP_COLETA_DESTINO -TimeoutSec 60 -ErrorAction Stop'],
                       env=ambiente, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
    else:
        with urlopen(url, context=contexto, timeout=60) as resposta, temporario.open('wb') as saida:
            shutil.copyfileobj(resposta, saida)
    if not zipfile.is_zipfile(temporario):
        raise ValueError(f'O endereço não retornou ZIP válido: {url}')
    temporario.replace(destino)

def localizar_planilha(fonte, baixar=False):
    base, ano = fonte['base'], fonte['ano']
    pasta = ROOT/'data/raw'/base
    if base != 'trajetoria':
        pasta /= str(ano)
    pasta.mkdir(parents=True, exist_ok=True)
    zips = list(pasta.glob('*.zip'))
    if not zips and baixar:
        destino = pasta/Path(fonte['url']).name
        print(f'Baixando {fonte["id"]} (os ZIPs podem ter centenas de MB)...', flush=True)
        baixar_zip(fonte['url'], destino)
        zips = [destino]
    if len(zips) != 1:
        raise FileNotFoundError(f'Esperado um ZIP em {pasta}. Use --baixar ou baixe {fonte["url"]}')
    zip_path = zips[0]
    with zipfile.ZipFile(zip_path) as arquivo:
        nomes = [n for n in arquivo.namelist() if n.lower().endswith('.xlsx')
                 and 'anexo' not in n.lower() and not Path(n).name.startswith('~$')]
        if len(nomes) != 1:
            raise ValueError(f'Planilha principal ambígua em {zip_path.name}: {nomes}')

        planilha = pasta/Path(nomes[0]).name

        with arquivo.open(nomes[0]) as entrada, planilha.open('wb') as saida:
            shutil.copyfileobj(entrada, saida)
        fonte['membro_zip'] = nomes[0]
    with zip_path.open('rb') as entrada:
        fonte['sha256_zip'] = hashlib.file_digest(entrada, 'sha256').hexdigest()
    fonte['sha256_xlsx'] = hashlib.sha256(planilha.read_bytes()).hexdigest()
    fonte['arquivo_zip'] = zip_path.relative_to(ROOT).as_posix()
    fonte['arquivo_xlsx'] = planilha.relative_to(ROOT).as_posix()
    fonte['data_arquivo_local'] = datetime.fromtimestamp(zip_path.stat().st_mtime).astimezone().isoformat()
    fonte['data_processamento'] = datetime.now().astimezone().isoformat()
    return planilha
