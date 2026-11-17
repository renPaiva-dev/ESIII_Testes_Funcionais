# Trabalho 1 – Testes de desempenho

Engenharia de Software III · Testes Funcionais

## Equipe

| Integrante | Contribuição |
|---|---|
| _a preencher_ | |
| _a preencher_ | |
| _a preencher_ | |

## Estrutura

| Pasta | Conteúdo | Situação |
|---|---|---|
| `pacote-A/exemplo/` | Execução do exemplo resolvido A (Semana do Cliente) | a fazer |
| `pacote-A/desafio/` | Testes do Desafio A (abertura da matrícula) | a fazer |
| `pacote-B/exemplo/` | Execução do exemplo resolvido B (catálogo da biblioteca) | a fazer |
| `pacote-B/desafio/` | Testes do Desafio B (consulta de minicursos) | a fazer |
| `projeto-anterior/estoque-facil/` | Sistema próprio da equipe: Estoque Fácil (Flask + SQLite) | pronto |
| `projeto-anterior/` (testes) | Testes de desempenho do Estoque Fácil | a fazer |
| `resultados/` | CSV, HTML e prints de cada execução | a fazer |
| `relatorio.pdf`, `slides.pdf` | Relatório (4 a 8 páginas) e apresentação | a fazer |

## Como rodar

Requisitos: Python 3.11 ou superior.

### Projeto anterior: Estoque Fácil

```sh
cd projeto-anterior/estoque-facil
python -m venv .venv
.venv\Scripts\Activate.ps1          # Windows PowerShell
# source .venv/bin/activate         # Linux/macOS
python -m pip install -r requirements.txt
python app.py                       # http://127.0.0.1:5001
```

Usuários, regras de negócio, API e localizadores estão em
[projeto-anterior/estoque-facil/README.md](projeto-anterior/estoque-facil/README.md).

## Versões utilizadas

| Item | Versão |
|---|---|
| Python | _a preencher_ |
| Flask | _a preencher_ |
| Locust ou Gatling | _a preencher_ |
| Sistema operacional | _a preencher_ |

> Os testes de carga foram executados apenas contra sistemas rodando localmente.
