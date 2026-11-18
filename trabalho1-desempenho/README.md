# Trabalho 1 – Testes de desempenho

Engenharia de Software III · Testes Funcionais

## Equipe

| Integrante | Contribuição |
|---|---|
| **Renato de Paiva Belarmino** | Modelagem e implementação dos scripts de carga no Locust (`Pacote A`, `Pacote B` e `Estoque Fácil`), automação da execução em lote, análise estatística, planos de teste, relatório técnico e slides. |
| **Alisson Gabriel** | Revisão geral da estrutura e dos artefatos do repositório no Git, elaboração da documentação inicial (`README.md`) e gravação dos vídeos demonstrativos de execução. |

---
## Estrutura

| Pasta | Conteúdo | Situação |
|---|---|---|
| `pacote-A/exemplo/` | Execução do exemplo resolvido A (Semana do Cliente), comparada com a referência do professor | pronto |
| `pacote-A/desafio/` | Testes do Desafio A (abertura da matrícula) | pronto (3 repetições) |
| `pacote-B/exemplo/` | Execução do exemplo resolvido B (catálogo da biblioteca) | pronto |
| `pacote-B/desafio/` | Testes do Desafio B (consulta de minicursos) | pronto (3 repetições) |
| `projeto-anterior/estoque-facil/` | Sistema próprio da equipe: Estoque Fácil (Flask + SQLite) | pronto |
| `projeto-anterior/desempenho/` | Testes de desempenho do Estoque Fácil | pronto (3 repetições) |
| `resultados/` | CSV, HTML e logs de cada execução | pronto |
| `relatorio.pdf` | Relatório (8 páginas) | pronto |
| `slides.pdf` | Slides da apresentação (21 slides: abertura, bloco do pacote A, bloco do pacote B, encerramento) | pronto |

## Como rodar

Cada pasta de testes tem um README com os comandos e um `plano_e_relatorio.md` com o plano, os resultados e a análise:
[Exemplo A](pacote-A/exemplo/README.md) · [Desafio A](pacote-A/desafio/README.md) ·
[Exemplo B](pacote-B/exemplo/README.md) · [Desafio B](pacote-B/desafio/README.md) ·
[Projeto anterior](projeto-anterior/desempenho/README.md).

Use sempre `127.0.0.1` no `--host`. No Linux, `localhost` tenta IPv6 primeiro e soma cerca de 2 s a cada requisição.

Requisitos: Python 3.11 ou superior e o kit da disciplina (`ESIII_Testes_Funcionais.zip`), que traz os sistemas dos pacotes A e B.

### Ambiente dos testes (uma vez)

```sh
python -m venv .venv
source .venv/bin/activate            # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install flask locust
```

### Sistemas testados (cada um em um terminal)

```sh
cd <kit>/02_Pacote_A_SaborExpress_Matricula/app && python app.py      # pacote A, porta 5000
cd <kit>/03_Pacote_B_Biblioteca_Minicursos && python app.py           # pacote B, porta 8000
cd projeto-anterior/estoque-facil && SEED_PRODUTOS=1000 python app.py --reset   # Estoque Fácil, porta 5001
```

Depois, em outro terminal com o venv ativo, siga o README de cada pasta de testes (links acima).

Os scripts `rodar.sh` e `rodar_fases.sh` precisam de bash e curl (Linux, macOS ou Git Bash/WSL no Windows). No Windows sem bash, use os comandos `python -m locust ...` que estão no README de cada pasta.

### Projeto anterior: Estoque Fácil

```sh
cd projeto-anterior/estoque-facil
python -m venv .venv
.venv\Scripts\Activate.ps1          # Windows PowerShell
# source .venv/bin/activate         # Linux/macOS
python -m pip install -r requirements.txt
SEED_PRODUTOS=1000 python app.py --reset   # http://127.0.0.1:5001, com os 1.000 produtos usados nos testes
```

Usuários, regras de negócio, API e localizadores estão em
[projeto-anterior/estoque-facil/README.md](projeto-anterior/estoque-facil/README.md).

## Versões utilizadas

| Item | Versão |
|---|---|
| Python | 3.12.3 |
| Flask | 3.1.3 |
| Locust | 2.47.0 |
| Sistema operacional | Ubuntu 24.04.5 LTS (Intel Core i7-13620H, 15 GiB) |

> Os testes de carga foram executados apenas contra sistemas rodando localmente.
