# syntax=docker/dockerfile:1.7

ARG CODEX_VERSION=0.165.0
ARG UV_VERSION=0.13.6@sha256:af22a52f5eafef3d78e551599d405c02df61919d18028f0cea8eda93bc9986d0

FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv-binaries
FROM debian:trixie-slim@sha256:89c1ea91e897f0fe0a3731595330bc45b8bdef4047464a07116f891a94054b31

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# Use Codex's bundled bubblewrap; Debian's version breaks its /proc fallback.
RUN apt-get update \
    && apt-get install --assume-yes --no-install-recommends \
        ca-certificates \
        nodejs \
        npm \
        python3 \
        python3-venv \
        tini \
    && rm -rf /var/lib/apt/lists/*

COPY --from=uv-binaries /uv /uvx /usr/local/bin/

ARG CODEX_VERSION
RUN npm install --global "@openai/codex@${CODEX_VERSION}" \
    && npm cache clean --force

RUN groupadd --gid 1001 worker \
    && useradd --uid 1001 --gid worker --create-home --shell /bin/bash worker

RUN chmod 0700 /home/worker /root

COPY resources/codex/ /usr/local/share/choir/codex/
COPY --chmod=0755 resources/entrypoint.sh /usr/local/bin/choir-entrypoint

ENV HOME=/home/worker
ENV CODEX_HOME=/home/worker/.codex
ENV PATH="/home/worker/.local/bin:${PATH}"
ENV UV_PYTHON_DOWNLOADS=never

USER worker
WORKDIR /home/worker

ENTRYPOINT ["/usr/bin/tini", "--", "/usr/local/bin/choir-entrypoint"]
CMD ["codex", "app-server", "--remote-control", "--listen", "unix://", "--strict-config"]
