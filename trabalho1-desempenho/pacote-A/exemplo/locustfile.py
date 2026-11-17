"""
Trabalho Prático 1 - SITUAÇÃO RESOLVIDA PELO PROFESSOR
"Semana do Cliente" da lanchonete Sabor Express

Perfis de usuário:
  - ClienteApp (90%): consulta cardápio, faz pedido e acompanha o pedido.
  - Gerente   (10%): consulta o relatório de vendas.

Tipos de teste (escolha pela variável de ambiente TIPO_TESTE):
  carga     -> 50 usuários constantes por 2 min       (comportamento esperado)
  estresse  -> degraus de +25 usuários a cada 30 s até 250 (achar o limite)
  pico      -> 10 usuários, salto para 150 por 30 s, volta para 10 (spike)
  resistencia -> 40 usuários por 15 min                (soak / endurance)

Exemplos (Linux/macOS):
  TIPO_TESTE=carga    locust -f locustfile.py --host http://localhost:5000 --headless --csv res/carga    --html res/carga.html
  TIPO_TESTE=estresse locust -f locustfile.py --host http://localhost:5000 --headless --csv res/estresse --html res/estresse.html
Windows (PowerShell):
  $env:TIPO_TESTE="estresse"; locust -f locustfile.py --host http://localhost:5000 --headless --csv res/estresse --html res/estresse.html

Antes de cada execução, zere os dados:  curl -X POST http://localhost:5000/api/admin/reset
"""
import os
import random

from locust import HttpUser, LoadTestShape, between, events, task

# Critérios de aceitação (SLA combinado com o "cliente")
SLA_P95_MS = 500
SLA_ERRO_MAX = 0.01  # 1%


class ClienteApp(HttpUser):
    weight = 9
    wait_time = between(1, 3)

    def on_start(self):
        self.meus_pedidos = []

    @task(5)
    def ver_cardapio(self):
        self.client.get("/api/cardapio", name="GET /api/cardapio")

    @task(2)
    def fazer_pedido(self):
        itens = [{"id": random.randint(1, 6), "qtd": random.randint(1, 2)}
                 for _ in range(random.randint(1, 3))]
        with self.client.post("/api/pedidos", json={"cliente": "locust", "itens": itens},
                              name="POST /api/pedidos", catch_response=True) as r:
            if r.status_code == 201:
                self.meus_pedidos.append(r.json()["id"])
            else:
                r.failure(f"status {r.status_code}")

    @task(2)
    def acompanhar_pedido(self):
        if self.meus_pedidos:
            pid = random.choice(self.meus_pedidos)
            # name agrupa todas as URLs /api/pedidos/<id> numa linha só do relatório
            self.client.get(f"/api/pedidos/{pid}", name="GET /api/pedidos/[id]")


class Gerente(HttpUser):
    weight = 1
    wait_time = between(2, 5)

    @task
    def relatorio(self):
        self.client.get("/api/relatorio/vendas", name="GET /api/relatorio/vendas")


class PerfilDeCarga(LoadTestShape):
    """Define a curva de usuários ao longo do tempo conforme TIPO_TESTE."""
    tipo = os.getenv("TIPO_TESTE", "carga")

    def tick(self):
        t = self.get_run_time()
        if self.tipo == "carga":
            return (50, 10) if t < 120 else None
        if self.tipo == "estresse":
            degrau = int(t // 30) + 1          # 1, 2, 3, ...
            usuarios = 25 * degrau
            return (usuarios, 25) if usuarios <= 250 else None
        if self.tipo == "pico":
            if t < 30:
                return (10, 10)
            if t < 60:
                return (150, 150)               # salto brusco
            if t < 90:
                return (10, 50)
            return None
        if self.tipo == "resistencia":
            return (40, 10) if t < 15 * 60 else None
        raise ValueError(f"TIPO_TESTE desconhecido: {self.tipo}")


# SLA específico por endpoint (o agregado pode esconder um endpoint ruim!)
SLA_POR_ENDPOINT_MS = {"GET /api/relatorio/vendas": 2000}


@events.quitting.add_listener
def verificar_sla(environment, **_):
    """Faz o processo terminar com código 1 se o SLA não for atendido
    (útil para rodar em pipeline de integração contínua)."""
    total = environment.stats.total
    if total.num_requests == 0:
        return
    reprovado = False
    p95 = total.get_response_time_percentile(0.95)
    taxa_erro = total.fail_ratio
    print(f"\n[SLA] geral: p95 = {p95:.0f} ms (limite {SLA_P95_MS}) | "
          f"erros = {taxa_erro:.2%} (limite {SLA_ERRO_MAX:.0%})")
    if p95 > SLA_P95_MS or taxa_erro > SLA_ERRO_MAX:
        reprovado = True
    for nome, limite in SLA_POR_ENDPOINT_MS.items():
        entrada = environment.stats.entries.get((nome, "GET"))
        if entrada and entrada.num_requests:
            p95_ep = entrada.get_response_time_percentile(0.95)
            print(f"[SLA] {nome}: p95 = {p95_ep:.0f} ms (limite {limite})")
            if p95_ep > limite:
                reprovado = True
    print("[SLA] REPROVADO" if reprovado else "[SLA] APROVADO")
    if reprovado:
        environment.process_exit_code = 1
