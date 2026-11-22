# Do Enem à graduação 🎓

Como evoluíram as inscrições de concluintes da rede pública no Enem entre 2020 e 2024? O projeto compara as redes de origem dos inscritos no Brasil e apresenta, no mesmo período, os ingressos na graduação e a trajetória dos estudantes que iniciaram um curso superior em 2020.

## 📊 O que os números mostram

| Série do Inep | O que a tabela permite acompanhar |
| --- | --- |
| Enem | Inscrições por rede, participação pública no total, registros sem rede informada e variação anual |
| Educação Básica | Matrículas no ensino médio regular, somadas todas as séries |
| Educação Superior | Ingressos na graduação por todas as formas de seleção |
| Trajetória | Permanência, conclusão e desistência no curso de ingresso da coorte de 2020 |

Em 2024, a sinopse registra **841.213 inscrições da rede pública** e **775.870 sem informação de rede**. A parcela pública usa como denominador todos os concluintes inscritos naquela edição. As bases agregadas permitem comparar períodos, mas não identificar quais inscritos entraram na graduação pelo Enem. Na trajetória, cada registro acompanha o vínculo com um curso.

[Consultar o dicionário das tabelas](data/processed/DICIONARIO.md) · [Ver fontes, planilhas e abas do Inep](data/processed/fontes.json)

## ▶️ Executar

Com Python 3.12, abra o PowerShell na raiz do repositório e execute os comandos abaixo.

~~~powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts/preparar_dados.py
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m streamlit run src/dashboard.py
~~~

O script usa os CSVs já versionados, confere os totais e as cinco edições, calcula os oito indicadores e grava o resumo anual do Enem. O painel oferece filtros por período e rede, gráficos interativos e exportação da tabela selecionada.

Para refazer a extração a partir dos ZIPs locais em `data/raw/`, execute o script com `--brutos`. A opção `--baixar` busca os ZIPs ausentes nos endereços oficiais e refaz a extração. As sinopses ficam em `data/raw/enem/ANO/`, `basica/ANO/` e `superior/ANO/` sob a mesma raiz. O arquivo de trajetória fica em `data/raw/trajetoria/`.

## 🗂️ Organização

| Caminho | Conteúdo |
| --- | --- |
| `notebooks/01_exploracao.ipynb` | Exploração das fontes, tipos, ausências e gráficos |
| `src/fontes.py` e `src/tratamento.py` | Leitura de CSV e Excel e extração das tabelas nacionais |
| `src/analise.py` e `src/indicadores.py` | Resumo anual, fórmulas e unidades dos indicadores |
| `scripts/preparar_dados.py` | Preparação e conferência dos dados |
| `data/processed/` | Tabelas, dicionário, fontes e evidências da extração |
| `src/visualizacao.py` e `src/dashboard.py` | Figuras Plotly e painel Streamlit |
| `tests/` | Testes dos dados e dos cálculos |

## Integração com o Streamlit

O ponto de entrada para o futuro `app.py` é `main()` em `src.dashboard`. Ele lê três CSVs locais (Enem, graduação e trajetória), monta o catálogo de indicadores e abre o painel.

~~~python
from src.dashboard import main

main()
~~~
