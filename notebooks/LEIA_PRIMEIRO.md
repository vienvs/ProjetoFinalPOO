# Minha parte: dados e notebook

Esta é a versão ajustada à divisão de tarefas do grupo. Use este pacote no lugar da entrega anterior, mais ampla.

## O que enviar ao GitHub

Envie o conteúdo de **data/** e **notebooks/** para a raiz do repositório, preservando as subpastas:

```
ProjetoFinalPOO/
├── data/
│   ├── raw/.gitignore
│   └── processed/  (CSVs, fontes, evidências e gráficos)
└── notebooks/
    ├── 01_exploracao.ipynb
    └── LEIA_PRIMEIRO.md
```

Não coloque a pasta externa `Minha-parte-POO` dentro do repositório: entre nela e envie as duas pastas que estão dentro.
Não envie o ZIP como substituto dos arquivos Python/tabelas. O ZIP serve para transportar a entrega.
Não envie os arquivos brutos do Inep. O `.gitignore` dentro de `data/raw/` exclui tudo dali, exceto ele próprio.

Não é necessário substituir `README.md`, `requirements.txt`, `.gitignore` da raiz, `src/`, `tests/` ou arquivos de colegas.
A pasta `dados/` que já existe no repositório permanece como está; esta contribuição usa `data/`, conforme o print combinado.
Se `data/` ou `notebooks/` já tiverem sido criadas por alguém, revise os nomes coincidentes numa branch e num pull request.

## Como ver e executar

Abra `data/processed/graficos/index.html` no navegador para ver o resultado sem instalar Python.
Abra `notebooks/01_exploracao.ipynb` no VS Code ou Jupyter para acompanhar o código e as saídas.
Para executar, use pandas, plotly e openpyxl num kernel Python. O notebook contém todas as classes/funções de que precisa.
Não há importações do código de outras frentes. O apêndice permite repetir o download e o tratamento, de forma opcional.

## Dados e limites

Brasil, de 2020 a 2024. As sinopses do Enem, Censo Escolar e Censo Superior foram conferidas por totais nacionais;
a trajetória acompanha a coorte de 2020. As fontes e seus hashes estão em `data/processed/fontes.json`.
A análise não identifica pessoas que ingressaram pelo Enem. Em 2024, a tabela oficial do Enem registra 519 inscrições
da rede privada e 775.870 sem informação da rede; esses valores são preservados e exigem cautela na comparação.
Matrículas do ensino médio não são usadas como concluintes. Inscrições não são presença nem aprovação.
