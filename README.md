# SolarSense

Monorepo com duas frentes acopladas, ambas em torno do mesmo sistema fotovoltaico real:

1. **Sistemas Embarcados (SE)** — aquisição de dados IoT não invasiva do sistema fotovoltaico (ESP32 + MQTT + dashboard em tempo real).
2. **Aprendizado de Máquina (AM/ML1)** — previsão horária de energia, com MLflow, Airflow e Docker, usando os dados do SE e do inversor.

## Por que um monorepo

As duas disciplinas avaliam a organização do GitHub com base na estrutura sugerida em cada edital. O repositório é único, organizado em 4 entidades — Embarcado, Backend, ML e Frontend — acopladas por um Postgres compartilhado: o Backend e os coletores escrevem, o ML lê e grava previsões, e o Frontend fala apenas com a API do Backend. Os nomes de pasta seguem o que cada edital pede; as duas listas não colidem e convivem na raiz.

## Arquitetura

```
ESP32 + sensores ──┐
                   ├─MQTT─> Backend (FastAPI) <──> Postgres <── sungrow-collector (inversor)
weather-station ───┘              │                    ^
(ESP virtual, Open-Meteo)         │ REST               │ lê para treino, grava previsões
                                  v                    │
                              Frontend          ML (src/ + Airflow + MLflow)
```

- **Embarcado** (`esp32-esp8266/`): firmware PlatformIO/Arduino. Lê os sensores e publica em `solarsense/{device_id}/readings`, onde `device_id` é o MAC da placa.
- **Backend** (`applications/backend/`): FastAPI + SQLAlchemy + Alembic. Ingere as leituras do MQTT, expõe a API, dispara o alerta de superaquecimento por e-mail e prevê cada hora nova com o modelo campeão.
- **sungrow-collector** (`applications/sungrow-collector/`): lê o inversor pela API iSolarCloud a cada 5 minutos.
- **weather-station** (`applications/weather-station/`): publica o clima horário da Open-Meteo no mesmo contrato MQTT da ESP, para a usina que ainda não tem placa instalada.
- **ML** (`src/`, `dags/`, `notebooks/`): cinco modelos (KNN, Árvore de Decisão, Random Forest, AdaBoost e MLP) comparados no MLflow contra um baseline físico; o campeão é registrado e usado nas previsões. O Airflow roda o pipeline horário e o retreino semanal.
- **Frontend** (`applications/frontend/`): React + Vite + TypeScript + Tailwind. `applications/frontend-mockup/` é o protótipo clicável com dados fictícios usado para validar a UX.

O dashboard é único para as duas disciplinas, já que o edital do AM/ML1 exige que ele mostre métricas do SE.

Potência estimada como `P ≈ V_nominal (220 V) × I_medido`: a tensão AC não é medida diretamente, para evitar qualquer contato do ESP32 com a rede elétrica.

## Segurança elétrica

O inversor opera em corrente alternada de rede (~220 V). A instalação do sensor de corrente (garra SCT-013) no cabo de saída do inversor é feita com supervisão de eletricista qualificado. Não há instrumentação do lado DC (painel-inversor), que opera em tensões mais altas.

## Como rodar

```bash
cp .env.example .env
docker compose up --build
```

O `docker compose` recusa subir enquanto faltar alguma variável obrigatória e informa qual é.

| Variável | Uso |
|---|---|
| `POSTGRES_PASSWORD` | senha do Postgres |
| `JWT_SECRET_KEY` | chave de assinatura da sessão (`openssl rand -hex 32`) |
| `MQTT_DEVICE_PASSWORD` | senha do usuário `device` do broker (ESP32 e weather-station) |
| `MQTT_BACKEND_PASSWORD` | senha do usuário `backend` do broker |
| `SOLARSENSE_SYSTEM_ID` | sistema usado pelo pipeline de ML e pelo coletor |
| `DATABASE_URL` | só para rodar `src/` ou o backend fora do Docker |

O coletor do inversor usa um arquivo próprio: `applications/sungrow-collector/.env`, a partir do `.env.example` da mesma pasta.

| Serviço | Porta | Observação |
|---|---|---|
| `mosquitto` | 1883 | broker MQTT, com autenticação |
| `postgres` | 5432 | |
| `backend` | 8000 | aplica as migrações ao iniciar |
| `mlflow` | 5000 | apenas em `localhost` |
| `airflow` | 8080 | apenas em `localhost` |
| `sungrow-collector`, `weather-station`, `ml` | — | sem porta exposta |

O frontend roda à parte:

```bash
cd applications/frontend
npm install
npm run dev
```

Fica em `http://localhost:5173`, com proxy de `/api` para o backend.

Para desenvolver com hot-reload do backend e Jupyter Lab em `localhost:8888`:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

### Firmware

```bash
cd esp32-esp8266
pio run -e esp32dev-live -t upload
pio device monitor
```

| Ambiente | Uso |
|---|---|
| `esp32dev` | sensores reais, publicação a cada 15 s |
| `esp32dev-live` | LDR, BME280, DHT11 e ZPH02, publicação a cada 2 s |
| `esp32dev-bench` | valores simulados, sem nenhum sensor ligado |

Na primeira inicialização a placa abre a rede Wi-Fi `SolarSense-XXXX`. No portal, informe o Wi-Fi, o endereço do servidor, a porta, o usuário `device` e a senha definida em `MQTT_DEVICE_PASSWORD`. Para reabrir o portal, segure o botão BOOT por 3 segundos. Depois de salvar, a placa fica 10 minutos em modo de pareamento e aparece no app para ser vinculada a um sistema.

Sem placa, o simulador publica no mesmo contrato:

```bash
cd applications/backend
MQTT_USERNAME=device MQTT_PASSWORD=... python scripts/simulate_esp32.py A1B2C3D48823 --pairing
```

## Segurança

- O broker não aceita conexões anônimas. O usuário `device` só publica em `solarsense/+/readings` e o usuário `backend` só lê desse tópico (`infra/mosquitto/acl`). As senhas vêm do `.env` e o arquivo de senhas é gerado quando o container sobe.
- O firmware não carrega credenciais: Wi-Fi, servidor e usuário/senha do broker são informados no portal e ficam na NVS da placa.
- A sessão do app é um JWT em cookie `httpOnly`. Toda rota de sistema verifica o dono no servidor.
- O tráfego MQTT não usa TLS; o broker é pensado para a rede local da instalação.

## Testes

```bash
cd applications/backend && pip install -r requirements-dev.txt && pytest
cd applications/sungrow-collector && pip install -e ".[dev]" && pytest
cd applications/weather-station && pip install -e ".[dev]" && pytest
cd applications/frontend && npm ci && npx tsc -b && npm run lint
```

Os mesmos comandos, mais `ruff` e `mypy`, rodam no GitHub Actions a cada push (`.github/workflows/ci.yml`).

## Estrutura do repositório

```
├── docker-compose.yml        orquestração dos serviços
├── docker-compose.dev.yml    overrides de desenvolvimento
├── infra/                    configuração do Mosquitto, Postgres e Airflow
├── applications/
│   ├── backend/              SE — API, ingestão MQTT, alertas e inferência
│   ├── frontend/             dashboard
│   ├── frontend-mockup/      protótipo clicável com dados fictícios
│   ├── sungrow-collector/    coletor do inversor
│   └── weather-station/      ESP virtual com clima da Open-Meteo
├── esp32-esp8266/            SE — firmware
├── data/raw/                 AM/ML1 — dados do INMET usados na comparação
├── notebooks/                AM/ML1 — análise exploratória
├── src/                      AM/ML1 — features, treino e previsão
├── dags/                     AM/ML1 — pipeline no Airflow
├── Dockerfile                AM/ML1 — imagem de treino
└── requirements.txt          AM/ML1 — dependências Python
```

O edital do AM/ML1 sugere um dashboard próprio em `/app`. Como ele também exige mostrar métricas do SE, o dashboard foi consolidado em `/applications/frontend`, ajuste previsto no próprio edital.

## SE — Sistemas Embarcados

**Tema do edital:** Elétrica.

Cronograma (SE 2026.2):
- 27/10 — definição da ideia
- 17/11 — Check Point
- 03/12 (23h59) — entrega de relatório + repositório
- 12/12 — apresentação na Mostra TechDesign

## AM/ML1 — Aprendizado de Máquina (Machine Learning I)

- **Instituição:** CESAR School
- **Nome da solução:** SolarSense
- Modelos: KNN, Árvore de Decisão, Random Forest, AdaBoost e Multilayer Perceptron, comparados via MLflow.
- Validação: holdout temporal, validação cruzada em série temporal e Grid Search.
- O dashboard inclui métricas do modelo e métricas do SE, servidas pela API do Backend.
