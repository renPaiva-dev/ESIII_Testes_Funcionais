# Engenharia de Software III – Testes Funcionais e de Desempenho

Repositório da disciplina **Engenharia de Software III** (Prof. Hélcio Soares) contendo os artefatos, scripts de automação, relatórios e evidências de execução dos testes de desempenho utilizando **Python** e **Locust**.

## Equipe

| Integrante | Contribuição |
|---|---|
| **Renato de Paiva Belarmino** | Modelagem e implementação dos scripts de carga no Locust (`Pacote A`, `Pacote B` e `Estoque Fácil`), automação da execução em lote (`rodar.sh`, `rodar_fases.sh`) e pós-processamento estatístico (`analisar_*.py`, `comparar_repeticoes.py`). |
| **Alisson Gabriel** | Refatoração em camadas do sistema **Estoque Fácil** (`controllers`, `services`, `repositories`, `models`), elaboração dos planos de teste (`plano_e_relatorio.md`), execução das baterias de repetições, consolidação do relatório técnico (`relatorio.pdf`), slides (`slides.pdf`) e documentação. |

---

## Estrutura do Repositório

Todo o conteúdo do **Trabalho 1** está organizado dentro do diretório [`trabalho1-desempenho/`](trabalho1-desempenho/):

| Caminho | Descrição |
|---|---|
| [`trabalho1-desempenho/README.md`](trabalho1-desempenho/README.md) | Guia detalhado de instalação, ambiente e execução dos sistemas e testes. |
| [`trabalho1-desempenho/relatorio.pdf`](trabalho1-desempenho/relatorio.pdf) | Relatório técnico consolidado (metodologia, medições, gráficos e recomendações). |
| [`trabalho1-desempenho/slides.pdf`](trabalho1-desempenho/slides.pdf) | Apresentação do trabalho (21 slides). |
| [`trabalho1-desempenho/pacote-A/`](trabalho1-desempenho/pacote-A/) | Scripts de teste, análise e planos do Exemplo A (*Semana do Cliente*) e Desafio A (*Abertura da Matrícula*). |
| [`trabalho1-desempenho/pacote-B/`](trabalho1-desempenho/pacote-B/) | Scripts de teste, análise e planos do Exemplo B (*Catálogo da Biblioteca*) e Desafio B (*Consulta de Minicursos*). |
| [`trabalho1-desempenho/projeto-anterior/`](trabalho1-desempenho/projeto-anterior/) | Código-fonte do sistema próprio **Estoque Fácil** (Flask + SQLite) e sua suíte de testes de desempenho. |
| [`trabalho1-desempenho/resultados/`](trabalho1-desempenho/resultados/) | Evidências brutas e consolidadas (`CSV`, `HTML`, logs, análises por patamar e `registro_resultados.csv`). |

---

## Resumo dos Resultados (Trabalho 1)

Todos os cenários foram executados localmente contra `127.0.0.1` com validação funcional de conteúdo (HTTP 200 com payload válido), tratamento de regras de negócio (`409`/`422`), auditoria de integridade pós-teste e **3 repetições** por patamar (`r1`, `r2`, `r3`):

| Sistema | Carga Nominal | Ponto de Quebra | Gargalo Identificado | Recuperação |
|---|---|---|---|---|
| **Desafio A** – Matrícula Acadêmica | **Não atende** (p95 do comprovante entre `4,7 s` e `5,5 s`; meta `≤ 1,5 s`) | Entre `50` e `100` matrículas simultâneas | Geração síncrona/em série do comprovante (~4 req/s) | Retorna a `~260 ms` após esvaziar a fila |
| **Desafio B** – Consulta de Minicursos | **Atende** (`p95 = 36 ms`, `0%` de falhas; meta `≤ 500 ms`) | `100` usuários (`~32,6%` de recusas `HTTP 503`) | Limite artificial de 4 consultas simultâneas (~133 req/s) | `12 s` no perfil contínuo (meta `≤ 30 s`) |
| **Estoque Fácil** – Projeto Anterior | **Atende com folga** (`p95` entre `9 ms` e `24 ms`, `0%` de falhas) | `800` usuários (reprova em 2 de 3 repetições) | CPU (`scrypt` em logins simultâneos) e escrita serializada/WAL no SQLite | `3–4 s` após redução da carga |

---

## Como Executar

1. Acesse o diretório do trabalho e crie o ambiente virtual Python (`>= 3.11`):

```bash
cd trabalho1-desempenho
python3 -m venv .venv
source .venv/bin/activate
pip install flask locust
```

2. Siga os comandos específicos de cada sistema e cenário descritos em [`trabalho1-desempenho/README.md`](trabalho1-desempenho/README.md).
