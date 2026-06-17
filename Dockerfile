FROM python:3.12-slim-bookworm

RUN apt-get update && apt-get install -y curl gnupg2 \
    && curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && curl -fsSL https://packages.microsoft.com/config/debian/12/prod.list | sed 's/^deb \[arch=amd64\]/deb [arch=amd64 signed-by=\/usr\/share\/keyrings\/microsoft-prod.gpg]/' > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

WORKDIR /app

COPY . .
RUN mkdir -p logs data
RUN uv sync

CMD ["uv", "run", "python", "main.py"]
