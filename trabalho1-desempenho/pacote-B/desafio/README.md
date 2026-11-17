# Desafio B – Consulta de minicursos (Trabalho 1)

Teste de desempenho da consulta de minicursos do sistema B (`http://127.0.0.1:8000`), feito com Locust (Python).

| Arquivo | Para que serve |
|---|---|
| `desafio_locust.py` | As duas tarefas (pesos 7 e 3), as verificações de conteúdo e a proteção automática |
| `rodar_fases.sh` | Roda as 6 fases do guia N vezes e guarda as evidências em `../../resultados/pacote-B-desafio/` |
| `analisar_fases.py` | Gera `resumo.md` e `registro_resultados.csv` (formato do modelo da disciplina) |
| `plano_e_relatorio.md` | Plano, ambiente, resultados, análise, limitações e recomendações, no formato do modelo da disciplina |

## Como rodar

```sh
# terminal 1: sistema B
cd <kit>/03_Pacote_B_Biblioteca_Minicursos
python app.py

# terminal 2: testes (venv com locust ativo)
cd trabalho1-desempenho/pacote-B/desafio
./rodar_fases.sh 3                  # 6 fases x 3 repetições (~25 min)
CONTINUO=1 ./rodar_fases.sh 3       # + perfil contínuo estresse -> recuperação (~35 min)
python analisar_fases.py ../../resultados/pacote-B-desafio   # refaz só a análise
```

Uma fase isolada, igual ao guia:

```sh
python -m locust -f desafio_locust.py --host http://127.0.0.1:8000 --headless \
  -u 20 -r 2 -t 90s --stop-timeout 5s --csv-full-history --csv carga20_r1 --html carga20_r1.html
```

Execução curta para a apresentação (100 usuários até a proteção disparar, cerca de 25 s). A saída do ensaio está em `resultados/pacote-B-desafio/demo_estresse100_ensaio.log`:

```sh
python -m locust -f desafio_locust.py --host http://127.0.0.1:8000 --headless -u 100 -r 10 -t 40s
```

## Plano, resultados e análise

Estão em [`plano_e_relatorio.md`](plano_e_relatorio.md), no formato do modelo `Modelo_Plano_e_Relatorio_Desempenho.md`. As evidências de cada execução estão em [`../../resultados/pacote-B-desafio/`](../../resultados/pacote-B-desafio/), com o registro no formato do modelo em `registro_resultados.csv`.
