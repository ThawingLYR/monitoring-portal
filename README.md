# 🚀 ThawingLYR Monitoring Portal

<div align="center">

Your all-in-one solution for permafrost monitoring in Longyearbyen.



<img width="40%" src="https://thawinglyr.com/wp-content/uploads/2026/05/cropped-thawinglyr_v3_b-scaled-1.png">




Built with ❤️ at <a href="https://www.unis.no">UNIS</a> by the <a href="https://thawinglyr.com">ThawingLYR</a> project.

</div>




## 📌 About the Project

The **Monitoring Portal** is a **Streamlit-based** application developed as part of the **ThawingLYR** initiative. This project aims to **build an integrated climate and permafrost response system**, delivering **real-time data on permafrost, terrain movement, and weather** in Longyearbyen. The portal provides **live dashboards** to help researchers, local authorities, and communities **predict, manage, and mitigate risks** posed by thawing permafrost.


## 🌍 About ThawingLYR

This portal is part of **[ThawingLYR](https://github.com/ThawingLYR)**, a **3-year research project (2025–2027)** funded by the **Research Council of Norway** and led by the **University Centre in Svalbard (UNIS)**. The project combines **mapping, monitoring, modelling, and local knowledge** to address the urgent challenges of thawing permafrost in Arctic settlements.


## 🤝 Partners

<div align="center">

    <div style="display: flex; justify-content: center; flex-wrap: wrap; gap: 20px; margin-bottom: 20px;">
    <img src="https://thawinglyr.com/wp-content/uploads/2025/08/unis-hovedlogo-mtxt.png-1-1.webp" alt="UNIS" style="height: 60px;" />
    <img src="https://thawinglyr.com/wp-content/uploads/2025/08/logo-nb-1-1024x170.png" alt="Nordland Research Institute" style="height: 60px;" />
    <img src="https://thawinglyr.com/wp-content/uploads/2025/08/Nord_University_logo.svg_-1024x366.png" alt="Nord University" style="height: 60px;" />
    <img src="https://thawinglyr.com/wp-content/uploads/2025/08/NMBU_logo_rgb_Primary_logo-1024x538.jpg" alt="NMBU" style="height: 60px;" />
    <img src="https://thawinglyr.com/wp-content/uploads/2025/08/Met_RGB_Horisontal_ENG-1.jpg" alt="MET Norway" style="height: 60px;" />
    <img src="https://thawinglyr.com/wp-content/uploads/2025/08/Screenshot-2025-08-30-at-14.11.54-1024x208.png" alt="Longyearbyen Lokalstyre" style="height: 60px;" />
    <img src="https://thawinglyr.com/wp-content/uploads/2025/08/5075667_2009841.jpg" alt="Svalbard Museum" style="height: 60px;" />
    <img src="https://thawinglyr.com/wp-content/uploads/2025/08/244_662340674.jpg" alt="Instanes AS" style="height: 60px;" />
    <img src="https://thawinglyr.com/wp-content/uploads/2025/08/Screenshot-2025-08-30-at-14.07.15.png" alt="NORSAR" style="height: 60px;" />
    <img src="https://thawinglyr.com/wp-content/uploads/2025/08/Screenshot-2025-08-30-at-14.09.50.png" alt="Tilsig AS" style="height: 60px;" />
    </div>

</div>

## 🛠️ Getting Started

### Prerequisites

- Python 3.13+
- [UV](https://github.com/astral-sh/uv) (for dependency management)
- Docker (for containerized deployment)
- Git

### API Keys

This app uses data from multiple providers, for which **API keys must be provided**:

- **Frost API** (Norwegian Meteorological Institute):  
Obtain a key at [frost.met.no](https://frost.met.no/auth/requestCredentials.html).
- **Tilsig API**:  
Please contact the [project maintainers](https://github.com/ThawingLYR/monitoring-portal/issues) to request access.


> 🔑 **Note:** Store your API keys securely in the `.env` file (see `.env.example` for the required format).

## 💻 Development

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

Your local dev server will be available at `http://localhost:8501`.

## 🐳 Docker Deployment

### Quick Start

For **production** or **local testing**, use the provided Docker container.

1. Clone the repository:
  ```bash
   git clone https://github.com/ThawingLYR/monitoring-portal.git
   cd monitoring-portal
  ```
2. Build the image:
  ```bash
   docker build -t monitoring-portal .
  ```
3. Run the container:
  ```bash
   docker run -p 8501:8501 --env-file .env -v cached-data:/streamlit-app/cached-data monitoring-portal
  ```
   The app will be accessible at [http://localhost:8501](http://localhost:8501).

> [!IMPORTANT]  
> **For production**, run the app behind a reverse proxy (e.g., [Caddy](https://caddyserver.com/)) to handle **TLS termination** and ensure secure connections.

## 🚀 Releases & Container Registry

When a **GitHub Release** is published, the Docker image is **automatically built and pushed** to the [GitHub Container Registry (GHCR)](https://ghcr.io/).

### Pull and Run the Latest Image

```bash
docker pull ghcr.io/thawinglyr/monitoring-portal:latest
docker run -p 8501:8501 --env-file .env -v cached-data:/streamlit-app/cached-data ghcr.io/thawinglyr/monitoring-portal:latest
```

> 💡 **Pro Tip:** The `cached-data` volume persists locally cached data between container restarts.

## 🤝 Contributing

We welcome contributions! Here’s how you can help:

1. **Fork** the repository.
2. Create a **feature branch** (`git checkout -b feature/your-idea`).
3. Commit your changes (`git commit -m "Add your feature"`).
4. Push to the branch (`git push origin feature/your-idea`).
5. Open a **Pull Request**.

> 📜 **Note:** Ensure your code passes `pre-commit` checks before submitting.

## 📜 License

This project is licensed under the **EUPL 1.2**. See the LICENCE file for details.

## 🆘 Support & Feedback

- **Found a bug?** [Open an issue](https://github.com/ThawingLYR/monitoring-portal/issues).
- **Have a feature request?** Share it in [Discussions](https://github.com/ThawingLYR/monitoring-portal/discussions)

**🌟 Star this repo if you find it useful!**

📅 **Project Timeline:** 2025–2027 | 🏢 **Lead Institution:** [UNIS](https://www.unis.no) | 💰 **Funding:** Research Council of Norway