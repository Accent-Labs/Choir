# syntax=docker/dockerfile:1.7

FROM debian:trixie-slim@sha256:d7e12182ce18b85b93007c1dedf31f2d29e01ccf3182cc4017c709b6259bc132

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# Use Codex's bundled bubblewrap; Debian's version breaks its /proc fallback.
RUN apt-get update \
    && apt-get install --assume-yes --no-install-recommends \
        ca-certificates \
        nodejs \
        npm \
        tini \
    && rm -rf /var/lib/apt/lists/*

ARG CODEX_VERSION=0.162.1

RUN npm install --global "@openai/codex@${CODEX_VERSION}" \
    && npm cache clean --force

RUN groupadd --gid 1001 worker \
    && useradd --uid 1001 --gid worker --create-home --shell /bin/bash worker

RUN chmod 0700 /home/worker /root

COPY resources/codex/ /usr/local/share/choir/codex/
COPY --chmod=0755 resources/entrypoint.sh /usr/local/bin/choir-entrypoint

ENV HOME=/home/worker
ENV CODEX_HOME=/home/worker/.codex

USER worker
WORKDIR /home/worker

ENTRYPOINT ["/usr/bin/tini", "--", "/usr/local/bin/choir-entrypoint"]
CMD ["codex", "--strict-config"]
