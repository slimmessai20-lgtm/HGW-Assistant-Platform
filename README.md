# 🪐 HGW-Assistant-Platform (Home Gateway AI Assistant)

![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Angular](https://img.shields.io/badge/Angular-DD0031?style=for-the-badge&logo=angular&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white)
![AI](https://img.shields.io/badge/AI-GPT--OSS%20120B-F37A20?style=for-the-badge)

An intelligent, containerized AI assistant designed specifically for enterprise network operations, automating tasks like VoIP configuration, DHCP management, firewall rule analysis, and ping diagnostics via a modern web interface.

## 🌟 Key Features

- **Conversational Interface:** Communicate naturally with an LLM (powered by GPT-OSS 120B) to configure your network.
- **Voice Control (Speech-to-Text):** Send commands via microphone.
- **Secure Authentication:** JWT-based authentication (HS256) with role-based access control (Admin, Engineer, User).
- **Tool-Calling Architecture (MCP):** 48 specialized tools integrated allowing the AI to execute real commands on the Home Gateway (Telnet automation, Ping, Traceroute, Wi-Fi config).
- **Containerized Infrastructure:** Deploys instantly via Docker Compose (Frontend, Backend, DB).

## 🏗️ Architecture (Monorepo)

This platform is divided into three main components:

- `/frontend` - **Angular 21 SPA** served by Nginx. Features reactive forms, voice recording, chat history, and dark mode UI.
- `/backend` - **FastAPI (Python 3.12)**. Handles API routing, JWT generation, database interactions (SQLAlchemy), and LLM orchestration.
- `/mcp-server` - **Model Context Protocol (MCP)**. Python-based standalone server defining the tools that the LLM can execute.

## 🚀 Quick Start (Docker)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/slimmessai20-lgtm/HGW-Assistant-Platform.git
   cd HGW-Assistant-Platform
   ```

2. **Configure Environment:**
   Create a `.env` file in the `backend/` directory based on `.env.example` with your Groq API Key and Database secrets.

3. **Deploy:**
   ```bash
   cd backend
   docker compose up --build -d
   ```

4. **Access the App:**
   - Dashboard: `http://localhost:8080`
   - API Swagger Docs: `http://localhost:8000/docs`

## 🛡️ Security
- Passwords hashed with `bcrypt`.
- Telnet operations encrypted via Fernet (AES-128-CBC) before database storage.
- Private Docker network (`hgw_net`) ensuring the database is never exposed to the host.

## 👨‍💻 Author
**Slim Messai** - Network & AI Enthusiast
