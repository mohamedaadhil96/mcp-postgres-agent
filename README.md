# Autonomous Database Management Agent (ADMA)

**Powered by Model Context Protocol (MCP) & PostgreSQL**

An autonomous agent interface designed to manage DVD rental operations without human intervention. By exposing high-level operational tools via MCP, this server transforms a standard PostgreSQL database into an agent-accessible workspace, enabling LLMs to autonomously execute complex business workflows.

> **"Don't just query the database—manage the business."**

## 🤖 Core Capabilities

### 1. Autonomous Operations
Unlike passive query tools, ADMA is built for **action**. It can autonomously:
-   **Execute Transactions**: Process rentals usage `rent_movie` with built-in availability checks.
-   **Close Loops**: Handle returns via `return_movie` and update inventory status instantly.
-   **Resolve Entities**: Fuzzy search for films and customers to map natural language to specific IDs (`search_movies`, `get_customer_history`).

### 2. Intelligent State Awareness
The agent doesn't just read data; it understands **availability**.
-   Before renting, it proactively verifies stock levels (`get_available_inventory`).
-   It prevents invalid states (e.g., trying to rent an already-rented item).

### 3. Operational Analytics
Empowers the agent to optimize business decisions.
-   **Revenue Optimization**: `analyze_revenue` allows the agent to identify high-performing categories.
-   **Customer Profiling**: `get_customer_history` enables personalized interaction contexts.

## 🏗️ Agentic Architecture

```mermaid
graph TD
    UserReq["👤 User Request<br/>'Rent The Matrix to John Doe'"] --> Agent["🤖 Autonomous Agent"]

    subgraph Phase1["Phase 1: Entity Resolution (Read)"]
        Agent -->|1. Search customer<br/>search_term: Doe| TC1["search_customers"]
        TC1 -->|"Results include:<br/>customer_id: 35<br/>name: John Doe"| Agent

        Agent -->|2. Search movie<br/>search_term: Matrix| TC2["search_movies"]
        TC2 -->|"Found:<br/>film_id: 92<br/>title: The Matrix"| Agent
    end

    subgraph Phase2["Phase 2: Availability Check (Read)"]
        Agent -->|3. Get available copies<br/>film_id: 92| TC3["get_available_inventory"]
        TC3 -->|"Available inventory:<br/>ID 402, store 1<br/>ID 403, store 1"| Agent
    end

    subgraph Phase3["Phase 3: Parameter Selection & Execution (Write)"]
        AgentDecision["Agent selects first available copy<br/>and default staff_id = 1"]

        Agent --> AgentDecision
        AgentDecision -->|4. Rent movie<br/>customer_id: 35<br/>inventory_id: 402<br/>staff_id: 1| TC4["rent_movie"]
        TC4 -->|"Success:<br/>Rental ID: 1092"| Agent
    end

    DB["PostgreSQL<br/>(Sakila Database)"]

    TC1 -.-> DB
    TC2 -.-> DB
    TC3 -.-> DB
    TC4 -->|Commit| DB

    %% Styling
    style Agent fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    style UserReq fill:#fff3e0,stroke:#e65100,stroke-dasharray: 5 5
    style Phase1 fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    style Phase2 fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    style Phase3 fill:#ffebee,stroke:#b71c1c,stroke-width:2px
    style AgentDecision fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style DB fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px
```

## 🛠️ Toolset for Autonomy

The server exposes a suite of **deterministic tools** designed for reliable agent consumption:

| Tool Category | Tool Name | Agentic Purpose |
| :--- | :--- | :--- |
| **Discovery** | `search_movies` | Resolving vague user requests to concrete Film IDs. |
| **Discovery** | `search_customers` | Resolving user names to Customer IDs. |
| **Context** | `get_customer_history` | Understanding user context before acting. |
| **Logistics** | `get_available_inventory` | Verifying physical constraints before commitment. |
| **Action** | `rent_movie` | **State Mutation**: Committing a business transaction. |
| **Action** | `return_movie` | **State Mutation**: Closing a business lifecycle. |
| **Insight** | `analyze_revenue` | High-level feedback loop for optimization. |

## 🚀 Deployment

### Prerequisites
-   Python 3.12+
-   PostgreSQL instance (DVD Rental schema)
-   [MCP Client](https://github.com/modelcontextprotocol) (e.g., Claude Desktop or Cursor)

### Quick Start

1.  **Configure Environment**:
    Create a `.env` file with your DB credentials:
    ```env
    PG_HOST=localhost
    PG_PORT=5432
    PG_DB=dvdrental
    PG_USER=postgres
    PG_PASSWORD=secure_password
    ```

2.  **Install Agent Server**:
    ```bash
    pip install "mcp[cli]" psycopg2-binary python-dotenv
    ```

3.  **Activate Agent**:
    ```bash
    python main.py
    ```

## 🔒 Safety Protocols

Even autonomous agents need guardrails. ADMA implements strict safety measures:
-   **Scoped Mutations**: Agents can only modify data through strict logic gates (`rent`/`return`), preventing arbitrary data corruption.
-   **Read-Only Fallback**: Arbitrary SQL execution (`run_select_query`) is strictly confined to `SELECT` statements.

---

*Transform your database from a storage engine into an intelligent team member.*

