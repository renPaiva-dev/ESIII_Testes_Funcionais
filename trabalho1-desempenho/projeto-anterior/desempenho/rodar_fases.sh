#!/usr/bin/env bash
# Testes de desempenho do Estoque Fácil (projeto anterior). Evidências em
# ../../resultados/projeto-anterior/
#
# Uso:   ./rodar_fases.sh [repeticoes] [primeira_repeticao]
#        CONTINUO=1 ./rodar_fases.sh 3   -> também roda o perfil contínuo 1200 -> 20 usuários
#
# Antes: suba o Estoque Fácil com 1000 produtos e ative o venv com locust:
#   cd ../estoque-facil && SEED_PRODUTOS=1000 python app.py --reset
set -uo pipefail

REPETICOES=${1:-3}
PRIMEIRA=${2:-1}
HOST=${HOST:-http://127.0.0.1:5001}
PYTHON=${PYTHON:-$(command -v python || command -v python3)}
PASTA="$(cd "$(dirname "$0")" && pwd)"
SAIDA="$PASTA/../../resultados/projeto-anterior"
mkdir -p "$SAIDA"

"$PYTHON" -c "import locust" 2>/dev/null || { echo "Locust não encontrado em $PYTHON (ative o venv ou defina PYTHON=...)"; exit 1; }
curl -sf -m 3 "$HOST/health" > /dev/null || { echo "Estoque Fácil fora do ar em $HOST"; exit 1; }

# nome usuarios ritmo duracao reset   (reset=0 mantém o banco do estresse anterior)
FASES=(
  "verificacao1 1 1 15s 1"
  "referencia5 5 1 90s 1"
  "carga20 20 2 90s 1"
  "estresse200 200 20 90s 1"
  "estresse400 400 40 90s 1"
  "estresse800 800 80 90s 1"
  "estresse1200 1200 100 90s 1"
  "recuperacao20 20 2 90s 0"
)

rodar() {  # prefixo, depois argumentos extras do locust
  local prefixo=$1; shift
  "$PYTHON" -m locust -f "$PASTA/locustfile_estoque.py" --host "$HOST" --headless --only-summary \
    --stop-timeout 5s --csv "$prefixo" --csv-full-history --html "$prefixo.html" "$@" \
    > "$prefixo.log" 2>&1
  grep -E "^\[(SLA|INTEGRIDADE|PROTEÇÃO)\]" "$prefixo.log" | grep -E "NÃO|PROTEÇÃO|INTEGRIDADE" | sed 's/^/    /'
}

for ((i = PRIMEIRA; i < PRIMEIRA + REPETICOES; i++)); do
  for fase in "${FASES[@]}"; do
    read -r nome u r t reset <<< "$fase"
    echo "=== $(date +%H:%M:%S) ${nome}_r$i  (-u $u -r $r -t $t, reset=$reset)"
    RESET=$reset rodar "$SAIDA/${nome}_r$i" -u "$u" -r "$r" -t "$t"
  done
  if [[ "${CONTINUO:-0}" == "1" ]]; then
    echo "=== $(date +%H:%M:%S) continuo1200para20_r$i  (perfil contínuo)"
    PERFIL=estresse_recuperacao USUARIOS_ESTRESSE=1200 rodar "$SAIDA/continuo1200para20_r$i"
  fi
done

"$PYTHON" "$PASTA/analisar_fases.py" "$SAIDA" | tee "$SAIDA/resumo.md"
