# Projeto anterior – desempenho do Estoque Fácil (Trabalho 1)

Teste de desempenho do sistema da equipe, o **Estoque Fácil** (`../estoque-facil`, Flask + SQLite, porta 5001), feito com Locust (Python).

| Arquivo | Para que serve |
|---|---|
| `locustfile_estoque.py` | Perfis Operador e Gerente, verificações de conteúdo, metas por operação, integridade dos saldos e proteção automática |
| `rodar_fases.sh` | Roda as fases N vezes e guarda as evidências em `../../resultados/projeto-anterior/` |
| `analisar_fases.py` | Gera `resumo.md` e `registro_resultados.csv` (formato do modelo da disciplina) |
| `plano_e_relatorio.md` | Plano, ambiente, resultados, análise, limitações e recomendações, no formato do modelo da disciplina |

## Como rodar

```sh
# terminal 1: Estoque Fácil com 1000 produtos
cd trabalho1-desempenho/projeto-anterior/estoque-facil
SEED_PRODUTOS=1000 python app.py --reset

# terminal 2: testes (venv com locust ativo)
cd trabalho1-desempenho/projeto-anterior/desempenho
./rodar_fases.sh 3                   # 8 fases x 3 repetições (~30 min)
CONTINUO=1 ./rodar_fases.sh 3        # + perfil contínuo 1200 -> 20 usuários (~40 min)
```

O script zera o banco (`POST /api/reset`) no início de cada fase, **exceto na recuperação**, que roda com `RESET=0` para começar com o banco do jeito que o estresse deixou.

## Plano, resultados e análise

Estão em [`plano_e_relatorio.md`](plano_e_relatorio.md), no formato do modelo `Modelo_Plano_e_Relatorio_Desempenho.md`. As evidências de cada execução estão em [`../../resultados/projeto-anterior/`](../../resultados/projeto-anterior/), com o registro no formato do modelo em `registro_resultados.csv`.
