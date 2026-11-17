#!/usr/bin/env bash
# Roda as fases do Desafio B (guia do aluno) e guarda as evidências em
# ../../resultados/pacote-B-desafio/
#
# Uso:   ./rodar_fases.sh [repeticoes] [primeira_repeticao]
# Ex.:   ./rodar_fases.sh 3          -> r1, r2, r3 de cada fase
#        ./rodar_fases.sh 1 2        -> só a repetição r2
#        CONTINUO=1 ./rodar_fases.sh 3   -> também roda o perfil contínuo estresse->recuperação
#
# Antes: suba o sistema B (python app.py, porta 8000) e ative o venv com locust.
set -uo pipefail

REPETICOES=${1:-3}
PRIMEIRA=${2:-1}
HOST=${HOST:-http://127.0.0.1:8000}
PYTHON=${PYTHON:-$(command -v python || command -v python3)}
PASTA="$(cd "$(dirname "$0")" && pwd)"
SAIDA="$PASTA/../../resultados/pacote-B-desafio"
mkdir -p "$SAIDA"

"$PYTHON" -c "import locust" 2>/dev/null || { echo "Locust não encontrado em $PYTHON (ative o venv ou defina PYTHON=...)"; exit 1; }
curl -sf -m 3 "$HOST/api/cursos" > /dev/null || { echo "Sistema B fora do ar em $HOST"; exit 1; }

# nome usuarios ritmo duracao  (tabela de fases do guia)
FASES=(
  "verificacao1 1 1 15s"
  "referencia5 5 1 90s"
  "carga20 20 2 90s"
  "estresse50 50 5 90s"
  "estresse100 100 10 90s"
  "recuperacao20 20 2 90s"
)

rodar() {  # prefixo, depois argumentos extras do locust
  local prefixo=$1; shift
  "$PYTHON" -m locust -f "$PASTA/desafio_locust.py" --host "$HOST" --headless --only-summary \
    --stop-timeout 5s --csv "$prefixo" --csv-full-history --html "$prefixo.html" "$@" \
    > "$prefixo.log" 2>&1
  # Saída diferente de zero por falhas de requisição é evidência do estresse, não erro do script.
  grep -E "^\[(META|PROTEÇÃO)\]" "$prefixo.log" | sed 's/^/    /'
}

for ((i = PRIMEIRA; i < PRIMEIRA + REPETICOES; i++)); do
  for fase in "${FASES[@]}"; do
    read -r nome u r t <<< "$fase"
    echo "=== $(date +%H:%M:%S) ${nome}_r$i  (-u $u -r $r -t $t)"
    rodar "$SAIDA/${nome}_r$i" -u "$u" -r "$r" -t "$t"
  done
  if [[ "${CONTINUO:-0}" == "1" ]]; then
    echo "=== $(date +%H:%M:%S) continuo100para20_r$i  (perfil contínuo)"
    PERFIL=estresse_recuperacao rodar "$SAIDA/continuo100para20_r$i"
  fi
done

"$PYTHON" "$PASTA/analisar_fases.py" "$SAIDA" | tee "$SAIDA/resumo.md"
