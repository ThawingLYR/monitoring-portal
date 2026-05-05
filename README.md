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
docker run -p 8501:8501 --env-file .env monitoring-portal
```

and the application will be available on [http://localhost:8501](http://localhost:8501).

> [!IMPORTANT]
> In production, the app should run behind a reverse proxy like Caddy to handle the TLS terminaison.


