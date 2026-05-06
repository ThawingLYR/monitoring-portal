ARG PYTHON_VERSION=3.14
ARG VERSION=0.X.X

# Stage 1: Dependency resolution
FROM astral/uv:python${PYTHON_VERSION}-bookworm-slim AS uv
WORKDIR /streamlit-app
COPY pyproject.toml .
RUN uv pip compile pyproject.toml > requirements.txt

# Stage 2: Build
FROM python:${PYTHON_VERSION}-slim AS builder
WORKDIR /streamlit-app
COPY --from=uv /streamlit-app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 3: Runtime
FROM python:${PYTHON_VERSION}-slim
ARG VERSION
ARG PYTHON_VERSION
WORKDIR /streamlit-app

# Copy only necessary files from the builder stage
COPY --from=builder /usr/local/lib/python${PYTHON_VERSION}/site-packages /usr/local/lib/python${PYTHON_VERSION}/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .
RUN echo "VERSION = '${VERSION}'" > ./src/app/version.py

EXPOSE 8501
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]