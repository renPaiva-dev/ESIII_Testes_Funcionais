# Estoque Fácil

Sistema web simples de controle de estoque: cadastro de produtos, entradas e saídas,
alerta de estoque baixo e relatório. Feito em Python (Flask) com banco SQLite.

Serve de alvo para a parte **"Projeto anterior"** dos dois trabalhos de Engenharia de Software III:
testes de desempenho (Locust/Gatling, pela API) e testes funcionais (Selenium, pelas telas).

## Como rodar

Requisitos: Python 3.11+.

```sh
python -m venv .venv
.venv\Scripts\Activate.ps1          # Windows PowerShell
# source .venv/bin/activate         # Linux/macOS
python -m pip install -r requirements.txt
python app.py                       # http://127.0.0.1:5001
```

- `python app.py --reset` recria os dados iniciais antes de subir.
- `POST http://127.0.0.1:5001/api/reset` faz o mesmo com o sistema no ar. Use antes de cada teste.
- O banco fica em `dados/estoque.db`. Ele é criado e preenchido na primeira execução.

| Variável | Padrão | Uso |
|---|---|---|
| `PORTA` | `5001` | Porta HTTP. Não conflita com o Pacote A (5000) nem com o Pacote B (8000). |
| `ESTOQUE_DB` | `dados/estoque.db` | Arquivo do banco SQLite. |
| `SEED_PRODUTOS` | `30` | Quantidade de produtos iniciais (mínimo 10). Serve para testes de **volume**: 1000, 100000... Depois de mudar, rode com `--reset`. |
| `PERMITIR_RESET` | `1` | Com `0`, o `POST /api/reset` responde 403. |

PowerShell: `$env:SEED_PRODUTOS="10000"; python app.py --reset`

## Usuários

| Usuário | Senha | Perfil | Pode |
|---|---|---|---|
| `admin` | `admin123` | admin | Tudo. |
| `operador` | `oper123` | operador | Consultar, registrar entradas e saídas, ver o relatório. Não cadastra, não edita e não exclui. |

## Regras de negócio

As mensagens abaixo são exibidas exatamente assim, tanto na tela quanto no campo `erro` da API.

| Regra | Comportamento esperado |
|---|---|
| **RN01 – Login** | Usuário e senha válidos abrem a lista de produtos. Campo vazio: "Informe usuário e senha." Credencial errada: "Usuário ou senha inválidos." |
| **RN02 – Acesso** | Todas as telas exigem login. Sem login, o sistema redireciona para `/login`. |
| **RN03 – Perfil** | Só o admin cadastra, edita e exclui. O operador que tentar recebe "Acesso restrito ao administrador." e o link "Novo produto" e os botões Editar/Excluir não aparecem para ele. |
| **RN04 – SKU** | Obrigatório. Espaços nas pontas são removidos e o texto vira maiúsculo. De 3 a 20 caracteres (letras, números ou hífen), sem começar por hífen: "SKU deve ter de 3 a 20 caracteres (letras, números ou hífen)." SKU único: "SKU já cadastrado." Não pode ser alterado depois do cadastro. |
| **RN05 – Nome** | Espaços nas pontas são removidos. De 3 a 60 caracteres: "Nome deve ter de 3 a 60 caracteres." |
| **RN06 – Preço** | De 0,01 a 99.999,99, com no máximo 2 casas decimais. Aceita vírgula ou ponto: "Preço deve estar entre 0,01 e 99.999,99." |
| **RN07 – Estoque mínimo** | Obrigatório, inteiro de 0 a 10000: "Estoque mínimo deve ser um inteiro entre 0 e 10000." |
| **RN08 – Quantidade inicial** | Opcional (vazio = 0), inteiro de 0 a 10000: "Quantidade inicial deve ser um inteiro entre 0 e 10000." Se for maior que 0, gera uma entrada "Saldo inicial" no histórico. |
| **RN09 – Movimentação** | O tipo é obrigatório: "Selecione o tipo de movimentação (entrada ou saída)." Quantidade inteira de 1 a 10000: "Quantidade deve ser um inteiro entre 1 e 10000." Observação de até 200 caracteres: "Observação deve ter no máximo 200 caracteres." |
| **RN10 – Saldo** | A entrada soma e a saída subtrai. A saída maior que o saldo é recusada e nada é gravado: "Estoque insuficiente. Saldo atual: N." **O saldo nunca fica negativo**, nem com acessos simultâneos. Sucesso: "Entrada registrada. Saldo atual: N." ou "Saída registrada. Saldo atual: N." |
| **RN11 – Situação** | Saldo 0: "Sem estoque". Saldo ≤ mínimo: "Estoque baixo". Caso contrário: "Normal". |
| **RN12 – Exclusão** | Só é permitida com saldo 0: "Só é possível excluir produto com estoque zerado." Ao excluir, o histórico do produto também é removido. Sucesso: "Produto excluído." |
| **RN13 – Busca** | Procura por parte do nome ou do SKU, sem diferenciar maiúsculas. O filtro "Só estoque baixo" mostra os produtos com saldo ≤ mínimo. A lista vem em ordem alfabética, 20 por página. |
| **RN14 – Histórico** | Cada movimentação registra data, tipo, quantidade, saldo após, usuário e observação. A tela mostra as 50 mais recentes primeiro. |

No cadastro e na edição, as validações seguem esta ordem e só aparece a **primeira** mensagem de erro:
SKU → nome → preço → estoque mínimo → quantidade inicial → SKU duplicado.
Quando o formulário é recusado, os valores digitados continuam nos campos.

Outras mensagens de sucesso: "Produto cadastrado com sucesso." e "Produto atualizado com sucesso."

## Dados iniciais (iguais após cada reset)

| id | SKU | Nome | Preço | Qtd | Mínimo | Situação |
|---|---|---|---|---|---|---|
| 1 | CAN-001 | Caneta esferográfica azul | 2,50 | 200 | 50 | Normal |
| 2 | CAD-001 | Caderno universitário 200 folhas | 18,90 | 40 | 10 | Normal |
| 3 | LAP-001 | Lápis preto HB | 1,20 | 8 | 30 | Estoque baixo |
| 4 | BOR-001 | Borracha branca | 1,80 | 60 | 20 | Normal |
| 5 | GRA-001 | Grampeador de mesa | 32,00 | 5 | 5 | Estoque baixo (limite: igual ao mínimo) |
| 6 | RES-001 | Resma papel A4 500 folhas | 29,90 | 25 | 10 | Normal |
| 7 | MAR-001 | Marca-texto amarelo | 4,50 | 0 | 10 | Sem estoque (pode ser excluído) |
| 8 | TES-001 | Tesoura escolar | 7,90 | 15 | 5 | Normal |
| 9 | COL-001 | Cola branca 90 g | 3,60 | 13 | 12 | Normal (limite: 1 acima do mínimo) |
| 10 | PAS-001 | Pasta catálogo 20 plásticos | 11,00 | 30 | 8 | Normal |
| 11+ | GEN-00011… | Item genérico 00011… | gerado | gerado | gerado | Gerados sempre iguais (semente fixa) |

Com o padrão de 30 produtos, a lista tem 2 páginas.

## Telas e localizadores (para Selenium)

Toda tela pode mostrar `#mensagem-sucesso` (`[data-testid='sucesso']`) ou `#mensagem-erro` (`[data-testid='erro']`).
O cabeçalho mostra o login em `#usuario-logado` e os links `#link-produtos`, `#link-novo` (só admin), `#link-relatorio` e `#link-sair`.

| Tela | URL | Elementos |
|---|---|---|
| Login | `/login` | `#usuario`, `#senha`, `#btn-entrar` |
| Lista | `/produtos` | `#busca`, `#filtro-baixo`, `#btn-buscar`, `#total-produtos`, `#tabela-produtos`, linha `[data-testid='produto-<SKU>']` com células `.sku .nome .preco .quantidade .minimo`, `[data-testid='situacao-<SKU>']`, `#link-produto-<SKU>`, `#lista-vazia`, `#pagina-atual`, `#proxima-pagina`, `#pagina-anterior` |
| Novo / editar | `/produtos/novo`, `/produtos/<id>/editar` | `#sku` (desabilitado na edição), `#nome`, `#preco`, `#estoque_minimo`, `#quantidade` (só no cadastro), `#btn-salvar`, `#link-cancelar` |
| Detalhe | `/produtos/<id>` | `#nome-produto`, `#detalhe-sku`, `#detalhe-preco`, `#saldo`, `#detalhe-minimo`, `#situacao`, `#btn-editar`, `#btn-excluir` (só admin), `#tipo` (select: `entrada`/`saida`), `#quantidade-mov`, `#observacao`, `#btn-registrar`, `#tabela-historico` com linhas `[data-testid='mov-<id>']` e células `.tipo .quantidade .saldo .usuario .obs`, `#historico-vazio` |
| Relatório | `/relatorio` | `#rel-produtos`, `#rel-unidades`, `#rel-valor`, `#rel-baixa`, `#rel-entradas`, `#rel-saidas`, `#tabela-baixa` com linhas `[data-testid='baixa-<SKU>']`, `#lista-mais-saidas` |

Os formulários usam `novalidate` e campos de texto comuns, sem `maxlength`. Assim, toda validação acontece no servidor e pode ser testada pela tela, por exemplo um nome com 61 caracteres.
Os preços aparecem no formato brasileiro: `R$ 1.234,56`.

## API REST (JSON)

A API não exige login, para facilitar os testes de carga locais. Os erros vêm como `{"erro": "<mensagem>"}`.

| Método e rota | Corpo | Respostas |
|---|---|---|
| `GET /health` | – | 200 `{"status": "ok"}` |
| `GET /api/produtos?q=&baixo=1&pagina=1` | – | 200 `{total, pagina, paginas, itens[≤20]}` |
| `GET /api/produtos/<id>` | – | 200 com o produto e o campo `situacao`; 404 se não existir |
| `POST /api/produtos` | `{"sku", "nome", "preco", "estoque_minimo", "quantidade"?}` | 201; 422 dado inválido; 409 SKU duplicado; 400 JSON inválido |
| `PUT /api/produtos/<id>` | `{"nome", "preco", "estoque_minimo"}` | 200; 422; 404 |
| `DELETE /api/produtos/<id>` | – | 200; 409 com saldo maior que 0; 404 |
| `POST /api/produtos/<id>/movimentacoes` | `{"tipo": "entrada"\|"saida", "quantidade", "observacao"?, "usuario"?}` | 201 `{id, tipo, quantidade, saldo_apos, ...}`; 409 estoque insuficiente; 422; 404 |
| `GET /api/produtos/<id>/movimentacoes` | – | 200 com as últimas 50 movimentações |
| `GET /api/relatorio` | – | 200 `{total_produtos, total_unidades, valor_total, produtos_em_baixa, entradas, saidas, lista_em_baixa, mais_saidas}` |
| `POST /api/reset` | – | 200; 403 se desabilitado |

Em teste de desempenho, 409 e 422 são **respostas corretas de regra de negócio**, não falhas técnicas.
Falhas técnicas são 5xx e timeout. Com o banco sobrecarregado, a API responde
**503 "Banco de dados ocupado. Tente novamente."**.

## O que observar nos testes de desempenho

Estas são características reais do sistema. Não há atrasos artificiais no código.

- **Escritas serializadas:** o SQLite permite uma gravação por vez. Cada movimentação e cada cadastro abre uma transação exclusiva (`BEGIN IMMEDIATE`). As leituras continuam em paralelo (modo WAL).
- **Integridade sob concorrência:** a saída usa uma atualização condicional (`quantidade >= pedido`). Dá para verificar que o saldo nunca fica negativo e que a soma das saídas aceitas bate com o saldo inicial.
- **O relatório cresce com o uso:** `GET /api/relatorio` percorre todos os produtos e todas as movimentações. Quanto mais movimentações a carga gerar, mais lento ele tende a ficar.
- **O login é custoso de propósito:** a senha é verificada com hash `scrypt`, um custo intencional de segurança.
- **Volume:** `SEED_PRODUTOS` muda o tamanho do catálogo. Volume é quantidade de dados, diferente de quantidade de usuários.
- **Servidor de desenvolvimento:** roda no servidor embutido do Flask, com uma thread por requisição. Registre isso nas limitações do relatório.

As metas (SLA) devem ser definidas e justificadas pela equipe, como pede o guia.

## Estrutura

```
05_Projeto_Estoque/
  app.py          cria a aplicação, trata erros e sobe o servidor
  web.py          telas (rotas HTML, login e perfis)
  api.py          API REST em JSON
  estoque.py      regras de negócio (serviços usados pela web e pela API)
  regras.py       validações puras (sem banco nem Flask)
  db.py           SQLite: conexão, transações, esquema e dados iniciais
  templates/      HTML (Jinja2)
  static/         CSS
  requirements.txt
```
