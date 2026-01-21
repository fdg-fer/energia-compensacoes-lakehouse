# 📊 ETL CKAN – Compensações de Continuidade (ANEEL)

Pipeline de ingestão de dados públicos da **ANEEL** via **CKAN**, com foco nos **indicadores de compensação financeira** relacionados à continuidade do fornecimento de energia elétrica.  
Os dados são extraídos, tratados e armazenados em **formato Parquet**, utilizando **MinIO (object storage S3-like)** como camada **Bronze** de um data lake local.

> Projeto desenvolvido com foco em **engenharia de dados**, boas práticas de ingestão, particionamento e arquitetura **lakehouse**, considerando limitações de ambiente sem cloud e Databricks Community Edition.

---
## 🧭 Contexto dos dados

A **ANEEL (Agência Nacional de Energia Elétrica)** disponibiliza mensalmente, em seu portal de dados abertos ([dados.aneel.gov.br](https://dados.aneel.gov.br/)), informações sobre a **qualidade do fornecimento de energia elétrica**, enviadas por todas as **distribuidoras do país**.

Os principais conjuntos de dados tratados neste projeto são:

| Indicador | Nome | Descrição | Unidade |
|------------|------|------------|----------|
| **DEC** | Duração Equivalente de Interrupção por Unidade Consumidora | Mede o tempo médio (em horas) que os consumidores ficaram sem energia em determinado período. | horas |
| **FEC** | Frequência Equivalente de Interrupção por Unidade Consumidora | Mede o número médio de interrupções no fornecimento de energia por unidade consumidora. | vezes |
| **Compensação** | Compensação Financeira Automática | Representa os valores (em R$) creditados aos consumidores quando os limites de continuidade (DEC/FEC) são ultrapassados. | reais |

Os indicadores **DEC** e **FEC** compõem o conjunto de **indicadores de continuidade do fornecimento**, enquanto o dado de **compensação** reflete o **impacto financeiro regulatório** dessas violações, conforme definido nos **Procedimentos de Distribuição (PRODIST) – Módulo 8** da ANEEL.

A ANEEL disponibiliza, via CKAN, conjuntos de dados relacionados à **continuidade do serviço de distribuição de energia elétrica**.  
Dentro desse contexto, este projeto trabalha exclusivamente com **dados de compensações financeiras**, que representam valores pagos aos consumidores quando os limites regulatórios de continuidade são ultrapassados.

### 🔎 Indicadores de compensação utilizados
- `PGUCAT`
- `PGUCBTNU`
- `PGUCBTU`
- `PGUCMTNU`
- `PGUCMTU`

Esses indicadores estão associados a diferentes tipos de compensação aplicados a conjuntos de unidades consumidoras.

---

## 🏗️ Arquitetura do projeto

```text
CKAN (ANEEL API)
        |
        v
Python (requests + pandas)
        |
        v
Parquet (particionado)
        |
        v
MinIO (energia-bronze)
```


### Principais características:
- **Ingestão paginada** via CKAN (`datastore_search`)
- **Filtragem por período** (AnoIndice = 2025)
- **Armazenamento em object storage** (MinIO)
- **Formato colunar (Parquet)**
- **Particionamento por ano e mês**
- Arquitetura **MinIO-only** (sem dependência de banco relacional)

---

## 🪣 Camada Bronze (Data Lake)

Os dados são armazenados no bucket:

*energia-bronze*

Com a seguinte estrutura de pastas:

```ckan/
└── compensacoes/
└── ano=2025/
├── mes=01/
│ └── part-xxxx.parquet
├── mes=02/
│ └── part-xxxx.parquet
└── ...
```

### 🔑 Particionamento
- **Ano:** `AnoIndice`
- **Mês:** `NumPeriodoIndice`

Esse particionamento reflete fielmente o modelo oficial dos dados da ANEEL e facilita:
- leituras seletivas
- agregações mensais
- evolução para camadas Silver e Gold

---

## ⚙️ Tecnologias utilizadas

- **Python 3**
- **Requests** – consumo da API CKAN
- **Pandas** – manipulação de dados
- **PyArrow / Parquet** – armazenamento colunar
- **MinIO** – object storage S3-compatible (local)
- **Docker / Docker Compose** – infraestrutura local
- **python-dotenv** – gerenciamento de variáveis de ambiente

---

## 📁 Estrutura do repositório

```ckan-energia-dec-fec/
│
├── etl/
│ ├── etl_ckan.py # Script principal de ingestão
│ ├── init_minio.py # Inicialização de buckets
│ └── requirements.txt
│
├── docker/
│ └── docker-compose.yml # MinIO
│
├── tmp_parquet/ # Arquivos temporários
├── logs/
├── .env # Variáveis de ambiente (não versionado)
├── .gitignore
└── README.md
```
---

## ▶️ Como executar o projeto

### 1️⃣ Subir o MinIO
```bash
docker compose -f docker/docker-compose.yml up -d
```

Acesse o console:

http://localhost:9001


## 📈 Resultado da carga (2025)

- **Ano carregado:** 2025  
- **Total de registros:** 143.780  
- **Status:** carga concluída com sucesso  
- **Persistência:** Parquet no MinIO (Camada Bronze)

---

## 🚀 Próximos passos (Roadmap)

- 🔹 **Camada Silver:** tipagem, limpeza e padronização dos dados  
- 🔹 **Camada Gold:** agregações analíticas (compensação mensal, por distribuidora e por conjunto consumidor)  
- 🔹 **Integração com Databricks Community Edition:** análises com Spark e SQL  
- 🔹 **Visualizações analíticas:** Power BI e/ou notebooks exploratórios  

---

## 📌 Observações finais

Este projeto foi desenhado para ser:

- **Reproduzível**
- **Escalável**
- **Portável para cloud** (S3 / ADLS / Databricks)

A migração para um ambiente em nuvem exigiria apenas a substituição do backend de storage, mantendo toda a lógica de ingestão, particionamento e organização dos dados.

---

*Projeto desenvolvido com foco em aprendizado prático e aplicação de boas práticas de Engenharia de Dados.*


