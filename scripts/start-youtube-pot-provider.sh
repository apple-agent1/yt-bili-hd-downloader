#!/usr/bin/env bash
set -euo pipefail

IMAGE="brainicism/bgutil-ytdlp-pot-provider:latest"
NAME="bgutil-provider"
PROXY_PORT="${PROXY_PORT:-7897}"
USE_PROXY=1

if [[ "${1:-}" == "--no-proxy" ]]; then
  USE_PROXY=0
fi

command -v docker >/dev/null || {
  echo "docker is required to start the YouTube PO Token provider." >&2
  exit 1
}

docker info >/dev/null
docker rm -f "$NAME" >/dev/null 2>&1 || true
docker pull "$IMAGE"

args=(run --name "$NAME" -d -p 4416:4416 --init)
if [[ "$USE_PROXY" -eq 1 ]]; then
  args+=(
    -e "HTTP_PROXY=http://host.docker.internal:${PROXY_PORT}"
    -e "HTTPS_PROXY=http://host.docker.internal:${PROXY_PORT}"
    -e "ALL_PROXY=socks5://host.docker.internal:${PROXY_PORT}"
  )
fi
args+=("$IMAGE")

docker "${args[@]}" >/dev/null

for _ in {1..20}; do
  if curl -fsS http://127.0.0.1:4416/ping; then
    echo
    echo "YouTube PO Token provider is ready on http://127.0.0.1:4416."
    exit 0
  fi
  sleep 0.5
done

echo "Provider container started, but /ping did not respond in time." >&2
docker logs --tail 80 "$NAME" >&2 || true
exit 1
