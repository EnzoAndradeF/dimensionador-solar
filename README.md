

## Dimensionador Solar — Quantitativo de Painéis por Inversor

[![AWS](https://img.shields.io/badge/AWS-EC2-orange?style=flat-square&logo=amazon-aws)](https://aws.amazon.com/)
[![Docker](https://img.shields.io/badge/Docker-Containerized-blue?style=flat-square&logo=docker)](https://www.docker.com/)
[![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-CI%2FCD-2088FF?style=flat-square&logo=github-actions)](https://github.com/features/actions)
[![Python](https://img.shields.io/badge/Python-3.11-yellow?style=flat-square&logo=python)](https://www.python.org/)
[![Nginx](https://img.shields.io/badge/Nginx-Reverse_Proxy-009639?style=flat-square&logo=nginx)](https://nginx.org/)
[![SSL](https://img.shields.io/badge/SSL%2FTLS-Let's_Encrypt-003A70?style=flat-square&logo=letsencrypt)](https://letsencrypt.org/)

Aplicação desenvolvida em **Python** para automação de dimensionamento fotovoltaico, validação de segurança elétrica em inversores/módulos e otimização de arranjos de entrada MPPT.

O projeto é totalmente conteinerizado com **Docker**, integrado a uma esteira automatizada de **CI/CD no GitHub Actions** e hospedado na nuvem **AWS (EC2)** sob um proxy reverso **Nginx** com criptografia **HTTPS (SSL/TLS)**.


### 🌐 Aplicação em Produção
- **URL Segura (HTTPS):** [Acessar Dimensionador Solar](https://dimensionador-solar-enzo.duckdns.org) 
- **Endereço IP AWS:** `http://3.23.128.112`

![alt text](Diagrama.png)