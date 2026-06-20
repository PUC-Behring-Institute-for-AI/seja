FROM python:3.12-slim AS build

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY mcp/ /build/mcp/
RUN pip install --no-cache-dir /build/mcp/ && \
    rm -rf /build/mcp

COPY scripts/seja /usr/local/bin/seja
RUN chmod +x /usr/local/bin/seja

FROM python:3.12-slim AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    jq \
    gettext-base \
    ca-certificates \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

COPY --from=build /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY --from=build /usr/local/bin/seja /usr/local/bin/seja

COPY Docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

RUN mkdir -p /opt/seja/security /usr/local/share/seja

COPY opencode/ /root/.config/opencode/
COPY project-template/ /root/.config/seja/project-template/
COPY security/cosign.pub /root/.seja/cosign.pub
COPY scripts/seja /usr/local/bin/seja-script
COPY security/cosign.pub /opt/seja/security/cosign.pub
COPY docker-compose.yml /usr/local/share/seja/docker-compose.yml

ARG TARGETARCH

RUN arch_bin="x64"; \
    if [ "${TARGETARCH}" = "arm64" ]; then \
        arch_bin="arm64"; \
    fi; \
    curl -fsSL "https://github.com/anomalyco/opencode/releases/latest/download/opencode-linux-${arch_bin}.tar.gz" \
        -o /tmp/opencode.tar.gz && \
    tar xzf /tmp/opencode.tar.gz -C /usr/local/bin/ && \
    mv /usr/local/bin/opencode /usr/local/bin/oc && \
    rm /tmp/opencode.tar.gz

EXPOSE 8765 4096

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8765/health || exit 1

ENTRYPOINT ["/entrypoint.sh"]
CMD ["oc"]
