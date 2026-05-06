## Development

Get started with local development in just a few steps:

```bash
# Clone the repository
git clone https://github.com/ThawingLYR/monitoring-portal.git
cd monitoring-portal

# Set up a virtual environment and install dependencies
uv venv
uv sync --dev

# Install the pre-commit hooks
pre-commit install

# Run the application
streamlit run streamlit_app.py
```

## Docker

This app provide a docker container for production and quick local tests.

First clone the repository

```bash
git clone https://github.com/ThawingLYR/monitoring-portal.git
cd monitoring-portal
```

Then build the image

```bash
docker build -t monitoring-portal .
```

Then run the image

```bash
docker run -p 8501:8501 --env-file .env -v cached-data:/streamlet-app/cached-data monitoring-portal
```

and the application will be available on [http://localhost:8501](http://localhost:8501).

> [!IMPORTANT]
> In production, the app should run behind a reverse proxy like Caddy to handle the TLS terminaison.

## Releases

When a Github Release is created, the docker container will be build and push to the Github container registry.

The image can be used with 

```bash
docker pull ghcr.io/thawinglyr/monitoring-portal:latest
docker run -p 8501:8501 --env-file .env -v cached-data:/streamlet-app/cached-data ghcr.io/thawinglyr/monitoring-portal:latest
```

The `cached-data` folder can be used to store locally cached data.


