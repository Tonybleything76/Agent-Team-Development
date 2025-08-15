FROM python:3.11-slim
WORKDIR /app
COPY adeptly_mcp_sdk ./adeptly_mcp_sdk
RUN pip install --no-cache-dir ./adeptly_mcp_sdk mcp-agent
COPY agents ./agents
RUN find agents -name "pyproject.toml" -maxdepth 2 -exec sh -c 'for f in "$@"; do pip install --no-cache-dir "$(dirname "$f")"; done' sh {} +
CMD ["bash","-lc","python -c 'print(\"Build OK\")' && tail -f /dev/null"]
