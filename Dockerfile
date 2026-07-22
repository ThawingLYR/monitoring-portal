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

# Stage 3: Cron Tasks Image
FROM python:${PYTHON_VERSION}-slim AS cron-tasks
ARG VERSION
ARG PYTHON_VERSION
WORKDIR /streamlit-app

RUN apt-get update && apt-get install -y git && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy only necessary files from the builder stage
COPY --from=builder /usr/local/lib/python${PYTHON_VERSION}/site-packages /usr/local/lib/python${PYTHON_VERSION}/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .
RUN echo "VERSION = '${VERSION}'" > ./src/app/version.py

# Make run.sh executable
RUN chmod +x cron-jobs.py run-cron.sh entrypoint.sh

# Use run.sh as the entry point
ENTRYPOINT ["/streamlit-app/entrypoint.sh"]

# Stage 3: Map initialization
FROM python:${PYTHON_VERSION}-slim AS map-init
ARG VERSION
ARG PYTHON_VERSION
WORKDIR /streamlit-app

# Copy only necessary files from the builder stage
COPY --from=builder /usr/local/lib/python${PYTHON_VERSION}/site-packages /usr/local/lib/python${PYTHON_VERSION}/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .
RUN echo "VERSION = '${VERSION}'" > ./src/app/version.py

# Can add more init here
CMD [ "python", "-m", "src.init.init_geomorph_map" ]

# Stage 3: Runtime
FROM python:${PYTHON_VERSION}-slim AS streamlit-app
ARG VERSION
ARG PYTHON_VERSION
WORKDIR /streamlit-app

# Copy only necessary files from the builder stage
COPY --from=builder /usr/local/lib/python${PYTHON_VERSION}/site-packages /usr/local/lib/python${PYTHON_VERSION}/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

RUN apt-get update && apt-get install -y curl && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy application code
COPY streamlit_app.py ./
COPY ./src ./src
RUN echo "VERSION = '${VERSION}'" > ./src/app/version.py

ENV PORT=8501
ENV SERVER_ADDRESS=localhost

EXPOSE ${PORT}
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "/streamlit-app/streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]