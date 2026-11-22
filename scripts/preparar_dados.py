import argparse
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.analise import AnalisadorColeta
from src.fontes import PASTA_PROCESSADOS, carregar_dados
from src.indicadores import REDES, CatalogoIndicadores
from src.tratamento import preparar


def gerar_resumo(pasta):
    dados = carregar_dados(pasta)
    enem = dados['enem']
    anos = set(range(2020, 2025))
    for ano, grupo in enem.groupby('ano'):
        if len(grupo) != len(REDES) or set(grupo['rede_origem']) != set(REDES):
            raise ValueError(f'Redes incompletas ou repetidas no Enem de {ano}.')
        inscricoes = grupo['inscritos_concluintes']
        totais = grupo['total_concluintes_inscritos']
        if inscricoes.isna().any() or (inscricoes < 0).any() or not totais.eq(inscricoes.sum()).all():
            raise ValueError(f'As inscrições por rede divergem do total em {ano}.')

    for nome, coluna in [('enem', 'ano'), ('superior', 'ano'), ('trajetoria', 'ano_referencia')]:
        serie = dados[nome][coluna]
        if set(serie) != anos or (nome != 'enem' and serie.duplicated().any()):
            raise ValueError(f'Confira os anos em {nome}.')
    if not dados['trajetoria']['ano_ingresso'].eq(2020).all():
        raise ValueError('A tabela de trajetória deve conter apenas a coorte de 2020.')

    catalogo = CatalogoIndicadores.padrao()
    catalogo.tabela(dados)
    resumo = AnalisadorColeta(enem).resumo()
    resumo.to_csv(pasta / 'indicadores_exploratorios.csv', index=False)
    print(f'{len(resumo)} anos conferidos e {len(catalogo)} indicadores calculados.')


def main():
    parser = argparse.ArgumentParser(description='Prepara as tabelas nacionais do Inep.')
    modo = parser.add_mutually_exclusive_group()
    modo.add_argument('--brutos', action='store_true', help='Reprocessa os ZIPs de data/raw.')
    modo.add_argument('--baixar', action='store_true', help='Baixa os ZIPs ausentes e reprocessa.')
    args = parser.parse_args()
    PASTA_PROCESSADOS.mkdir(parents=True, exist_ok=True)
    if args.brutos or args.baixar:
        with TemporaryDirectory(dir=PASTA_PROCESSADOS) as temporario:
            pasta = Path(temporario)
            preparar(baixar=args.baixar, saida=pasta)
            gerar_resumo(pasta)
            for arquivo in pasta.iterdir():
                arquivo.replace(PASTA_PROCESSADOS / arquivo.name)
    else:
        gerar_resumo(PASTA_PROCESSADOS)
    print('Tabelas disponíveis em data/processed/.')


if __name__ == '__main__':
    main()
