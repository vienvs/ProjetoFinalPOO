---
layout: home
title: Do Enem à graduação
---

**Rede pública, Enem e ensino superior no Brasil · 2020 a 2024**

Sistema em Python que lê dados oficiais do Inep, trata as tabelas com Pandas, calcula indicadores em classes
orientadas a objetos e apresenta os resultados em gráficos Plotly e num painel Streamlit.

- [Código-fonte e instruções para executar o painel](https://github.com/vienvs/ProjetoFinalPOO#readme).
- Painel interativo: `streamlit run app.py`. Para abrir o painel no computador, siga os comandos no README. Os cinco gráficos também estão disponíveis nesta página.

---

## 1. Justificativa do tema

O Enem é a principal porta de acesso ao ensino superior público e a programas como Sisu e Prouni.
O MEC estimou que a parcela de concluintes da rede pública inscritos no Enem passou de 48% (2022) para
58% (2023) e 94% (2024, valor preliminar). Já o Censo da Educação Superior 2024 indica que só 27% dos
concluintes da rede estadual de 2023 se matricularam na graduação em 2024, contra 60% da rede privada.
Esse contraste entre **participar do exame**, **ingressar** e **concluir** motiva o projeto.

Os **94%** estimados pelo MEC usam como base os concluintes da rede pública. Já os **52%** calculados neste projeto usam como base todos os concluintes inscritos no Enem de 2024, inclusive os que ficaram sem rede informada.

**Hipótese:** o aumento das inscrições de concluintes da rede pública no Enem pode não se refletir, na mesma
intensidade, no ingresso e na conclusão do ensino superior.

**Perguntas orientadoras**

| # | Pergunta | Onde é respondida |
|---|---|---|
| P1 | Como evoluíram as inscrições de concluintes da rede pública no Enem? | Indicadores 1 e 4 · gráficos de linhas e barras |
| P2 | Como se distribuem as redes registradas e os registros sem informação? | Indicadores 2 e 3 · gráfico de setores |
| P3 | Como a série do Enem se apresenta ao lado do ingresso na graduação? | Indicador 5 · gráfico de dispersão |
| P4 | Quantos ingressantes de 2020 permanecem, concluem ou desistem do curso? | Indicadores 6 a 8 · gráfico de trajetória |

**Objetivos:** descrever a evolução das inscrições, comparar as redes de origem, contextualizar o ingresso na
graduação, acompanhar a trajetória de uma coorte e documentar definições e limitações, aplicando POO, Pandas,
Plotly e Streamlit.

## 2. Fonte pública dos dados

Todos os dados vêm do **Inep/MEC** ([dados abertos](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos)), nas edições de 2020 a 2024:

| Base | Tabela usada | Conteúdo |
|---|---|---|
| [Sinopses do Enem](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/sinopses-estatisticas/enem) | 3.10 | Concluintes inscritos por dependência administrativa da escola |
| [Sinopses da Educação Superior](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/sinopses-estatisticas/educacao-superior) | 4.4 | Ingressantes na graduação |
| [Sinopses da Educação Básica](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/sinopses-estatisticas/educacao-basica) | Ensino Médio 1.25 | Matrículas no ensino médio regular por rede |
| [Indicadores de Trajetória](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/indicadores-educacionais/indicadores-de-trajetoria-da-educacao-superior) | INDICADORES_TRAJETORIA | Permanência, conclusão e desistência da coorte de 2020 |

O arquivo `data/processed/fontes.json` registra a URL de cada ZIP, a aba lida e os hashes SHA-256.
O `evidencias_extracao.json` guarda as células originais de cada linha nacional, para auditoria.

## 3. Variáveis utilizadas

| Tabela (`data/processed/`) | Chave | Variáveis principais |
|---|---|---|
| `enem_brasil_rede.csv` | ano, rede_origem | `inscritos_concluintes` e `total_concluintes_inscritos` (inteiros, em inscrições) |
| `superior_brasil.csv` | ano | `ingressantes_graduacao` e `ingressantes_universidades` (inteiros, em ingressos) |
| `basica_matriculas_brasil.csv` | ano, rede_origem | `matriculas_em_regular` (todas as séries; **não são concluintes**) |
| `trajetoria_coorte_2020.csv` | ano_referencia | `vinculos_ingressantes_coorte`, `vinculos_permanencia`, `conclusoes_no_ano`, `desistencias_no_ano`, `falecimentos_no_ano` |

A variável `rede_origem` assume três valores: **Pública** (soma de federal, estadual e municipal), **Privada** e
**Não dispõe da informação**. Um campo vazio representa ausência e nunca é tratado como zero.
O dicionário completo está em `data/processed/DICIONARIO.md`.

## 4. Tratamento e análise dos dados

1. **Obtenção:** `scripts/preparar_dados.py --baixar` baixa os ZIPs oficiais para `data/raw/`, que fica fora do Git.
2. **Leitura:** `FonteExcel` abre apenas a aba necessária, e `FonteCSV` lê as tabelas tratadas.
3. **Seleção e filtragem:** apenas a linha *Brasil* de cada sinopse, conferindo o título e o layout das colunas.
4. **Ausentes:** os símbolos `-`, `...` e vazio viram `pd.NA`, e as somas usam `min_count`, de modo que uma ausência não vira zero.
5. **Duplicidades:** a chave de negócio (ano e rede; curso, coorte e ano) é verificada, e o processamento para se houver repetição. Os dados oficiais não tinham duplicatas (`duplicidades_chave = 0`), por isso nada precisou ser apagado.
6. **Reconciliação:** a soma das redes precisa igualar o total publicado. Se divergir, o script recusa os dados.
7. **Agrupamento e ordenação:** `groupby` por ano de referência na trajetória, `pivot` por rede no Enem e `sort_values` por ano.
8. **Estatísticas descritivas:** `info()`, `isna().sum()`, `duplicated()` e `describe()` no notebook `notebooks/01_exploracao.ipynb`.

O script grava as tabelas num diretório temporário e só substitui `data/processed/` depois de todas as conferências.

## 5. Arquitetura orientada a objetos

```
dados oficiais (ZIP/XLSX) ─► FonteExcel ─► ExtratorSinopse ─► data/processed/*.csv
                                                                    │
                     FonteCSV ◄─────────────────────────────────────┘
                        │
                        ▼
   CatalogoIndicadores (Indicador ×8)    Visualizador (Grafico ×5)    FiltrosDashboard
                        └──────────────────────┬───────────────────────────┘
                                               ▼
                                     Dashboard (Streamlit) ◄── app.py
```

```
FonteDados (abstrata) ── FonteCSV, FonteExcel
Indicador (abstrata) ─┬─ IndicadorContagem ─── InscritosRedePublica, IngressantesGraduacao
                      └─ IndicadorPercentual ─┬─ ParticipacaoPublicaNoTotal, ProporcaoSemInformacao,
                                              │  VariacaoAnualPublica
                                              └─ IndicadorTrajetoria (abstrata) ── PermanenciaCoorte,
                                                 ConclusaoAcumuladaCoorte, DesistenciaAcumuladaCoorte
Grafico (abstrata) ── GraficoLinhas, GraficoBarras, GraficoSetores, GraficoDispersao, GraficoTrajetoria
```

- **Encapsulamento:** os atributos são protegidos (`_caminho`, `_formula`, `_evidencias` etc.) e expostos por `@property` somente leitura. Listas são devolvidas como cópia.
- **Herança e polimorfismo:** `carregar()` tem uma implementação para CSV e outra para Excel. Em `Indicador.serie()` e `Grafico.construir()` (padrão *template method*), cada subclasse implementa apenas `_calcular()` ou `_desenhar()`.
- **SOLID:**
  - Responsabilidade única: um módulo por etapa (fontes → tratamento → análise/indicadores → visualização → painel).
  - Aberto/fechado: um novo indicador ou gráfico é só uma nova subclasse registrada no catálogo.
  - Substituição de Liskov: qualquer `Indicador` funciona no catálogo e no painel.
  - Segregação de interfaces: as classes abstratas exigem poucos métodos.
  - Inversão de dependência: o `Dashboard` recebe o catálogo e o visualizador como parâmetros.

## 6. Classes implementadas

| Classe | Módulo | Responsabilidade |
|---|---|---|
| `FonteDados`, `FonteCSV`, `FonteExcel` | `src/fontes.py` | Contrato de leitura e implementações para CSV e planilhas do Inep |
| `ExtratorSinopse` | `src/tratamento.py` | Localiza a linha nacional, valida o layout, reconcilia totais e guarda evidências |
| `AnalisadorColeta` | `src/analise.py` | Resumo anual do Enem por rede (totais, parcelas e variação) |
| `Indicador` e 8 subclasses | `src/indicadores.py` | Nome, fórmula, unidade, limitação, série anual e formatação pt-BR de cada indicador |
| `CatalogoIndicadores` | `src/indicadores.py` | Registra os indicadores, recusa códigos repetidos e monta as tabelas larga e longa |
| `Grafico` e 5 subclasses | `src/visualizacao.py` | Desenho Plotly com título, fonte e aviso padronizados |
| `Visualizador` | `src/visualizacao.py` | Reúne os gráficos, constrói as figuras e exporta HTML |
| `FiltrosDashboard` | `src/dashboard.py` | Guarda período, redes e ano escolhidos e filtra as tabelas |
| `Dashboard` | `src/dashboard.py` | Organiza cabeçalho, KPIs, filtros, gráficos, tabela e análise no Streamlit |

Uso dos objetos (em `app.py`): `Dashboard(carregar_dados()).executar()`. O painel cria internamente
`CatalogoIndicadores.padrao()` e `Visualizador()`.

## 7. Indicadores desenvolvidos

| # | Indicador | Fórmula | Unidade | Limitação |
|---|---|---|---|---|
| 1 | Inscrições de concluintes da rede pública | Federal + Estadual + Municipal (tabela 3.10) | inscrições | Inscrição não é presença nem aprovação |
| 2 | Participação da rede pública nas inscrições | Pública ÷ total de concluintes inscritos × 100 | % | Descreve os inscritos; o total inclui registros sem rede |
| 3 | Inscrições sem informação da rede | Sem informação ÷ total × 100 | % | Alerta de qualidade; os registros não são redistribuídos |
| 4 | Variação anual das inscrições públicas | (ano ÷ ano anterior − 1) × 100 | % | 2020 não tem variação; as causas não são medidas |
| 5 | Ingressantes na graduação | Tabela 4.4 do Censo Superior | ingressos | Todas as origens e formas de ingresso |
| 6 | Permanência da coorte 2020 | Permanência ÷ (vínculos iniciais − falecimentos acumulados) × 100 | % | Vínculos com cursos, não pessoas |
| 7 | Conclusão acumulada da coorte 2020 | Σ conclusões ÷ (vínculos iniciais − falecimentos acumulados) × 100 | % | Cinco anos de acompanhamento |
| 8 | Desistência acumulada da coorte 2020 | Σ desistências ÷ (vínculos iniciais − falecimentos acumulados) × 100 | % | Desistir do curso ≠ sair do ensino superior |

**Resultados**

| Ano | Inscrições públicas | Part. pública | Sem informação | Variação | Ingressantes | Permanência | Conclusão | Desistência |
|---|---|---|---|---|---|---|---|---|
| 2020 | 685.864 | 49,1% | 35,2% | — | 3.765.475 | 83,3% | 1,1% | 15,6% |
| 2021 | 603.041 | 52,4% | 29,3% | −12,1% | 3.944.897 | 59,2% | 5,0% | 35,8% |
| 2022 | 724.523 | 55,0% | 27,7% | +20,1% | 4.756.728 | 40,3% | 10,4% | 49,3% |
| 2023 | 728.878 | 52,0% | 31,6% | +0,6% | 4.993.992 | 26,2% | 16,7% | 57,1% |
| 2024 | 841.213 | 52,0% | 48,0% | +15,4% | 5.010.433 | 13,6% | 24,4% | 62,1% |

## 8. Gráficos e interpretação

Os gráficos abaixo são interativos: passe o mouse para ver os valores.

**Linhas: inscrições por rede.** As inscrições da rede pública caem na edição de 2021, ainda sob a pandemia,
e crescem nas edições seguintes. O gráfico sozinho não explica as causas das oscilações.

<iframe src="graficos/01_linhas.html" width="100%" height="600" loading="lazy" title="Gráfico de linhas"></iframe>

**Barras: comparação absoluta entre redes.** As barras mostram números absolutos, não probabilidades de acesso.
Em 2024, a sinopse registra 519 inscrições na categoria privada e 775.870 sem rede informada. A causa dessa distribuição permanece em aberto.

<iframe src="graficos/02_barras.html" width="100%" height="600" loading="lazy" title="Gráfico de barras"></iframe>

**Setores: composição de 2024.** Os registros sem informação (48%) fazem parte do denominador e não foram
redistribuídos entre as redes.

<iframe src="graficos/03_setores.html" width="100%" height="600" loading="lazy" title="Gráfico de setores"></iframe>

**Dispersão: Enem e ingresso na graduação.** Cada ponto é um ano. As duas séries terminam 2024 acima de 2020,
mas em 2021 as inscrições caíram enquanto os ingressos subiram. Além disso, elas descrevem populações diferentes. O gráfico não acompanha pessoas, não forma um funil e não comprova causalidade.

<iframe src="graficos/04_dispersao.html" width="100%" height="600" loading="lazy" title="Gráfico de dispersão"></iframe>

**Linhas: trajetória da coorte 2020.** A permanência cai ano a ano, enquanto conclusão e desistência acumulam.
As três curvas somam 100% em cada ano.

<iframe src="graficos/05_trajetoria.html" width="100%" height="600" loading="lazy" title="Trajetória da coorte 2020"></iframe>

## 9. Funcionamento do dashboard

Execute `streamlit run app.py`. O painel tem:

- **Cabeçalho:** título, recorte (Brasil, 2020–2024) e aviso sobre o que os dados não medem.
- **Filtros (barra lateral):** período (edições do Enem), rede da escola de origem e ano do gráfico de composição.
- **KPIs:** quatro cartões do Enem e da graduação e três da coorte de 2020, todos no último ano do período, com variação em relação ao ano anterior quando ela se aplica.
- **Visualizações em abas:** evolução das inscrições, composição, Enem e graduação, e trajetória. Elas se atualizam conforme os filtros.
- **Tabela de dados:** escolha entre indicadores, Enem, graduação e trajetória, com botão para baixar em CSV.
- **Análise interpretativa:** textos gerados a partir dos valores filtrados, a lista de limitações e a fórmula de cada indicador.

As tabelas processadas ficam no repositório, então o painel roda sem baixar os dados do Inep.

## 10. Conclusões e limitações

**Conclusões**

- As inscrições de concluintes da rede pública no Enem passaram de **685.864 (2020)** para **841.213 (2024)**, alta de 22,7%, apesar da queda de 12,1% em 2021.
- Entre os concluintes inscritos, a parcela identificada como da rede pública variou de **52,0% a 55,0%** entre 2021 e 2024. Em 2024, porém, **48%** dos registros não informam a rede.
- Os ingressos na graduação, de todas as origens, subiram de 3,77 milhões para **5,01 milhões** (+33,1%).
- Na coorte de 2020, descontados os falecimentos acumulados até 2024, **24,4% concluíram**, **62,1% desistiram** do curso de ingresso e **13,6% permaneciam**.
- A contagem de inscrições da rede pública cresceu entre 2020 e 2024. Na coorte da graduação, a desistência do curso foi o desfecho mais frequente até 2024. **Não está comprovado** que mais estudantes da rede pública ingressaram pelo Enem e concluíram a graduação: isso exigiria dados que liguem as mesmas pessoas entre as etapas.

**Limitações**

- Inscrição não é presença nem aprovação. As sinopses não trazem comparecimento nem notas por rede.
- As séries do Enem, da graduação e da coorte são agregadas e não acompanham as mesmas pessoas.
- Os ingressantes incluem todas as formas de ingresso, e a rede de origem deles não é identificada.
- Em 2024, a rede privada tem só 519 inscrições e 775.870 registros não têm rede. Comparações entre redes nesse ano exigem cautela.
- A trajetória conta vínculos com cursos, e não pessoas, e tem só cinco anos de acompanhamento.
- O recorte é nacional. Estados e a separação entre rede estadual e federal ficam como trabalho futuro.

## 11. Referências

- INEP. Sinopses Estatísticas do Enem 2020–2024. <https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/sinopses-estatisticas/enem>
- INEP. Sinopses Estatísticas da Educação Superior 2020–2024. <https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/sinopses-estatisticas/educacao-superior>
- INEP. Sinopses Estatísticas da Educação Básica 2020–2024. <https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/sinopses-estatisticas/educacao-basica>
- INEP. Indicadores de Trajetória da Educação Superior 2020–2024. <https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/indicadores-educacionais/indicadores-de-trajetoria-da-educacao-superior>
- MEC/Inep. [Panorama Brasil, Enem de novembro de 2024](https://www.gov.br/mecconfia/pt-br/centrais-de-conteudo/infograficos/enem/bra-nov-24-pdf.pdf) e [resultados do Censo da Educação Superior 2024](https://download.inep.gov.br/educacao_superior/censo_superior/documentos/2024/apresentacao_censo_da_educacao_superior_2024.pdf).
- Pandas: <https://pandas.pydata.org> · Plotly: <https://plotly.com/python/> · Streamlit: <https://docs.streamlit.io>

Arquivos do Inep processados em 19/11/2026 (datas e hashes em `data/processed/fontes.json`).
