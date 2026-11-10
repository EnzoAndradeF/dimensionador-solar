<div align="center">

  <p><b>Dimensionador Solar v2.0.0</b> — Sistema Web de Dimensionamento Fotovoltaico & Compatibilidade MPPT</p>
  <a href="https://github.com/EnzoAndradeF/dimensionador-solar/issues/new?assignees=&labels=bug&template=01_BUG_REPORT.md&title=bug%3A+">Reportar um Bug</a>
  ·
  <a href="https://github.com/EnzoAndradeF/dimensionador-solar/issues/new?assignees=&labels=enhancement&template=02_FEATURE_REQUEST.md&title=feat%3A+">Solicitar uma funcionalidade</a>
  ·
  <a href="https://dimensionador-solar.duckdns.org">Acessar Aplicação em Produção</a>
</div>

<div align="center">
  <br />

  <!-- Status & Deploy -->
  <a href="https://dimensionador-solar.duckdns.org">
    <img src="https://img.shields.io/badge/AWS_EC2-Live-232F3E?style=flat-square&logo=amazon-aws&logoColor=FF9900" alt="AWS EC2" />
  </a>
  <a href="https://dimensionador-solar.duckdns.org">
    <img src="https://img.shields.io/badge/SSL-HTTPS-00C7B7?style=flat-square&logo=letsencrypt&logoColor=white" alt="SSL" />
  </a>
  <a href="https://github.com/EnzoAndradeF/dimensionador-solar/actions">
    <img src="https://img.shields.io/badge/CI%2FCD-GitHub_Actions-2088FF?style=flat-square&logo=githubactions&logoColor=white" alt="CI/CD" />
  </a>

  <!-- Stack Tecnológica Core -->
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white" alt="Docker" />
  <img src="https://img.shields.io/badge/Nginx-Reverse_Proxy-009639?style=flat-square&logo=nginx&logoColor=white" alt="Nginx" />
  <img src="https://img.shields.io/badge/PostgreSQL-15-4169E1?style=flat-square&logo=postgresql&logoColor=white" alt="Postgres" />
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-API-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Streamlit-UI-FF4B4B?style=flat-square&logo=streamlit&logoColor=white" alt="Streamlit" />

</div>

<br />


## Sobre o projeto

O **Dimensionador Solar** é uma plataforma web completa projetada para simplificar e automatizar o cálculo de dimensionamento de sistemas geradores fotovoltaicos. A aplicação permite a seleção de módulos solares, inversores e controladores MPPT, realizando a verificação de compatibilidade elétrica e o dimensionamento térmico e de strings em tempo real.

O projeto evoluiu de um script monolítico para uma **arquitetura moderna em microsserviços conteinerizados**, orquestrados via Docker Compose, com terminação SSL/TLS (HTTPS) nativa via Nginx/Certbot, persistência de dados em PostgreSQL e integração contínua (CI/CD) desacoplada no GitHub Actions.

Funcionalidades do **Dimensionador Solar**:

- Calculadora de dimensionamento de inversores e entradas MPPT.
- Módulo de verificação de compatibilidade de painéis solares.
- Interface reativa construída em Streamlit com navegação lateral.
- API REST assíncrona em FastAPI para processamento de regras de negócio.
- Banco de dados relacional PostgreSQL 15 com persistência via Docker Volume.
- Reverse Proxy Nginx configurado com HTTPS (porta 443) e WSS (WebSockets).
- Certificados SSL/TLS gratuitos com renovação automática via Certbot (Let's Encrypt).
- Domínio personalizado via DuckDNS (`dimensionador-solar.duckdns.org`).
- Esteiras de CI/CD separadas: Build & Push de imagens no Docker Hub e Deploy via SSH na AWS EC2.

### Stacks 

- [Python 3.11](https://www.python.org/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Streamlit](https://streamlit.io/)
- [PostgreSQL 15](https://www.postgresql.org/)
- [Docker & Docker Compose](https://www.docker.com/)
- [Nginx](https://nginx.org/)
- [AWS EC2](https://aws.amazon.com/ec2/)
- [DuckDNS](https://www.duckdns.org/) & [Let's Encrypt / Certbot](https://certbot.eff.org/)
- [GitHub Actions](https://github.com/features/actions)

## Arquitetura e infraestrutura 

```mermaid
graph TD
    subgraph CLIENT["🌐 Cliente & Segurança"]
        User["👤 Usuário / Web Browser"]
        DuckDNS["🦆 DuckDNS (DNS Dynamic resolution)"]
        Certbot["🔒 Let's Encrypt / Certbot (SSL/TLS)"]
    end

    subgraph AWS["☁️ AWS EC2 (Ubuntu Linux Server)"]
        subgraph DOCKER["🐳 Docker Compose Network"]
            
            subgraph PROXY_LAYER["🛡️ Camada de Proxy"]
                Nginx["⚡ Nginx Reverse Proxy\n• HTTP (80) -> Redirect HTTPS (443)\n• SSL Termination (/etc/letsencrypt)\n• Support Streamlit WebSockets"]
            end

            subgraph APP_LAYER["🚀 Camada de Aplicação"]
                Frontend["🎨 Streamlit Frontend\n• Internal Port: 8501\n• MPPT Calculator & UI"]
                Backend["⚡ FastAPI Backend\n• Internal Port: 8000\n• Regras de Negócio & API"]
            end

            subgraph DATA_LAYER["💾 Persistência"]
                Postgres[("🐘 PostgreSQL DB v15\n• Internal Port: 5432\n• Volume: postgres_data")]
            end
        end
    end

    subgraph DEVOPS["🔄 Esteira CI/CD"]
        GitHub["🐙 GitHub Repository"]
        ActionsCI["⚙️ CI (docker-ci.yml)\n1. Build Images\n2. Push to Docker Hub"]
        ActionsCD["🚀 CD (docker-cd.yml)\n1. Connect SSH\n2. Git Pull & Compose Pull\n3. Restart Containers & Prune"]
        DockerHub["🐳 Docker Hub Registry"]
    end

    User -->|HTTPS 443| DuckDNS
    DuckDNS -->|IP: 3.23.128.112| Nginx
    Certbot -.->|SSL Certificates| Nginx

    Nginx -->|Proxy Pass /| Frontend
    Nginx -->|Proxy Pass /api/| Backend

    Frontend <-->|REST API| Backend
    Backend <-->|SQLAlchemy ORM| Postgres

    GitHub -->|Push to main| ActionsCI
    ActionsCI -->|Push Imagens| DockerHub
    ActionsCI -->|Trigger Completion| ActionsCD
    ActionsCD -->|SSH Commands| AWS
    DockerHub -.->|Docker Pull| DOCKER
```