# Dicionário das tabelas entregues

Codificação dos CSVs: UTF-8. Separador: vírgula. Campo numérico vazio representa ausência; não significa zero. As contagens são inteiras quando disponíveis. Percentuais usam escala de 0 a 100; o nome termina em `_pct`.

## Campos comuns

| Campo | Tipo | Significado |
|---|---|---|
| ano | inteiro | Edição do Enem ou ano de referência do censo |
| abrangencia | texto | Brasil; não há linhas de UF ou região misturadas |
| rede_origem | categoria | Pública, Privada ou, somente no Enem, Não dispõe da informação |
| fonte_id | texto | Identificador que se relaciona a `id` no catálogo `fontes.json` |
| aba | texto | Nome da tabela na planilha oficial |

## enem_brasil_rede.csv

Chave: `ano, rede_origem`. São 15 linhas, três categorias em cada edição.

| Campo | Tipo/unidade | Significado |
|---|---|---|
| inscritos_concluintes | inteiro, inscrições | Concluintes inscritos da categoria registrada; pública soma Federal, Estadual e Municipal |
| total_concluintes_inscritos | inteiro, inscrições | Total nacional da tabela 3.10, repetido nas três linhas do ano apenas para conferência; **não somar essa coluna por rede** |

Concluinte no Enem significa cursar o último ano e concluiria naquele ano. Não equivale a conclusão escolar comprovada. A categoria sem informação não foi imputada.

## superior_brasil.csv

Chave: `ano`. São cinco linhas.

| Campo | Tipo/unidade | Significado |
|---|---|---|
| ingressantes_graduacao | inteiro, ingressos | Graduação em todas as organizações acadêmicas, tabela 4.4, coluna E |
| ingressantes_universidades | inteiro, ingressos | Subconjunto em universidades, tabela 4.4, coluna F; **não adicionar ao total anterior** |
| categoria_ies | texto | Todas; não informa rede escolar de origem |
| modalidade | texto | Presencial e a distância |
| forma_ingresso | texto | Todas; não identifica ingresso exclusivamente pelo Enem |

## basica_matriculas_brasil.csv

Chave: `ano, rede_origem`. São dez linhas.

| Campo | Tipo/unidade | Significado |
|---|---|---|
| matriculas_em_regular | inteiro, matrículas | Ensino médio regular em todas as séries, agrupado por rede |
| universo | texto | Declara que o dado representa matrículas, não concluintes |

A extração soma cada dependência administrativa nas séries e não soma as colunas de subtotais. Não se calcula uma taxa de participação de concluintes usando essas matrículas como denominador.

## trajetoria_coorte_2020.csv

Chave: `ano_ingresso, ano_referencia`. A coorte é fixa em 2020 e os cinco anos de observação são 2020–2024.

| Campo | Tipo/unidade | Significado |
|---|---|---|
| ano_ingresso | inteiro | 2020 |
| ano_referencia | inteiro | Ano da observação da coorte |
| vinculos_ingressantes_coorte | inteiro, vínculos | Soma dos ingressantes nos cursos observados naquela referência; **não somar entre referências** |
| vinculos_permanencia | inteiro, vínculos | Soma dos vínculos ativos nos cursos na referência |
| conclusoes_no_ano | inteiro, eventos | Conclusões anuais, não acumuladas |
| desistencias_no_ano | inteiro, eventos | Desistências anuais de cursos, não abandono de todo o ensino superior |
| falecimentos_no_ano | inteiro, eventos | Falecimentos registrados no ano |
| cursos_observados | inteiro, registros | Quantidade de registros curso/coorte/ano incluídos na agregação |
| ausentes_qt_* | inteiro, registros | Quantidade de registros sem a contagem correspondente; se positiva, o total daquela contagem fica vazio |
| unidade | texto | Explicita que os dados são vínculos com cursos, não pessoas únicas |

Não calculamos uma média simples das taxas oficiais dos cursos. `trajetoria_amostra_25_linhas.csv` contém os 25 primeiros registros válidos e mantém os nomes oficiais das variáveis para exploração. A amostra é ilustrativa do formato, **não representativa estatisticamente**.

## indicadores_exploratorios.csv

Chave: `ano`. É derivado exclusivamente da tabela tratada do Enem.

| Campo | Unidade/fórmula |
|---|---|
| inscritos_publica | Contagem da rede pública registrada |
| inscritos_privada | Contagem da rede privada registrada |
| inscritos_sem_informacao | Contagem sem informação da rede |
| total_concluintes_inscritos | Soma das três categorias mutuamente exclusivas |
| participacao_publica_no_total_pct | Pública / todos os concluintes inscritos × 100 |
| sem_informacao_pct | Sem informação / todos os concluintes inscritos × 100 |
| variacao_anual_publica_pct | (Pública no ano / pública no ano anterior − 1) × 100; ausente em 2020 |

Esses percentuais descrevem os inscritos. Não são taxa de aprovação, taxa de comparecimento, taxa de transição nem probabilidade de ingresso na graduação.

## Arquivos de auditoria

- `fontes.json`: página, URL do ZIP, aba, nome do membro do ZIP, caminhos relativos, hashes SHA-256 e datas operacionais. O horário tem fuso explícito. A data do arquivo local registra a coleta, não a publicação oficial.
- `evidencias_extracao.json`: células da linha nacional, cabeçalhos, título e linha do Excel para cada uma das 15 sinopses. O catálogo original e os CSVs devem ser usados juntos.
- `validacao.json`: resultado da execução desta versão autônoma do notebook; sem dependência dos testes da entrega anterior.
