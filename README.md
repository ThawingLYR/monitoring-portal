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