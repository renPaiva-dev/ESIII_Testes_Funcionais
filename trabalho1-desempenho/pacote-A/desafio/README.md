# Desafio A – Abertura da matrícula (Trabalho 1)

Teste de desempenho do módulo **Matrícula Acadêmica** do sistema A (`http://127.0.0.1:5000`), feito com Locust (Python).

| Arquivo | Para que serve |
|---|---|
| `locustfile_matricula.py` | Jornada do aluno, verificações de conteúdo, perfis de carga, checagem do SLA e da integridade das vagas |
| `rodar.sh` | Roda um tipo de teste N vezes e guarda as evidências em `../../resultados/pacote-A-desafio/` |
| `analisar_patamares.py` | Resume o histórico por patamar de alunos e por endpoint (mostra qual piora primeiro) |
| `comparar_repeticoes.py` | Compara r1, r2 e r3 de cada tipo e grava `comparacao.md` (o `rodar.sh` chama sozinho no fim) |
| `plano_e_relatorio.md` | Plano, ambiente, resultados, análise, limitações e recomendações, no formato do modelo da disciplina |

## Como rodar

```sh
# terminal 1: sistema A
cd <kit>/02_Pacote_A_SaborExpress_Matricula/app
python app.py

# terminal 2: testes (venv com locust ativo)
cd trabalho1-desempenho/pacote-A/desafio
./rodar.sh verificacao      # 1 aluno por 15 s: confere o script

# versão curta da carga (40 s, 100 alunos), com a tabela ao vivo, para a apresentação:
TIPO_TESTE=demo python -m locust -f locustfile_matricula.py --host http://127.0.0.1:5000 --headless
./rodar.sh carga 3          # carga_r1, carga_r2, carga_r3
./rodar.sh pico 3
./rodar.sh estresse 3
```

O script zera o sistema (`POST /api/admin/reset`) no início de cada execução. Para desligar esse reset, use `RESET=0`.
Use sempre `127.0.0.1` e não `localhost`. No Linux, `localhost` tenta IPv6 primeiro e cada requisição perde cerca de 2 s, o que falsifica a medição (veja `resultados/pacote-A-exemplo/invalido-localhost-ipv6`).

Cada execução gera os arquivos abaixo:

| Arquivo | Conteúdo |
|---|---|
| `*_stats.csv`, `*.html` | Números finais por endpoint |
| `*_stats_history.csv` | Linha do tempo, por endpoint |
| `*_regras.csv` | SLA, respostas 409/422 e integridade das vagas |
| `*_patamares.md` | Tabela por patamar |
| `*.log` | Saída do terminal |

## Plano, resultados e análise

Estão em [`plano_e_relatorio.md`](plano_e_relatorio.md), no formato do modelo `Modelo_Plano_e_Relatorio_Desempenho.md`. As evidências de cada execução estão em [`../../resultados/pacote-A-desafio/`](../../resultados/pacote-A-desafio/), com o registro no formato do modelo em `registro_resultados.csv`.
