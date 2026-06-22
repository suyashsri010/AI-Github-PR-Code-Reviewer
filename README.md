graph TB
    %% Configuration & Styles
    %% Standardizing clean, modern block aesthetics for GitHub Readmes
    classDef external fill:#2f3640,stroke:#718093,stroke-width:2px,color:#fff;
    classDef gateway fill:#00a8ff,stroke:#0097e6,stroke-width:2px,color:#fff;
    classDef worker fill:#9c88ff,stroke:#8c7ae6,stroke-width:2px,color:#fff;
    classDef core fill:#e1b12c,stroke:#fbc531,stroke-width:2px,color:#fff;
    classDef storage fill:#4cd137,stroke:#44bd32,stroke-width:2px,color:#fff;
    classDef cognitive fill:#6c5ce7,stroke:#a29bfe,stroke-width:2px,color:#fff;

    %% --- EXTERNAL ENTITIES ---
    subgraph EXT ["🌐 External Ecosystem"]
        direction LR
        GH["🐙 GitHub API & Webhooks<br/>App Installation Context"]:::external
        LLM["🤖 LangGraph AI Engine<br/>[OpenAI / Anthropic Context]"]:::external
    end

    %% --- INGRESS LAYER ---
    subgraph INGRESS ["🛡️ Ingress & Security Layer"]
        ALB["🔒 AWS Application Load Balancer<br/>[SSL Termination & Routing]"]:::gateway
    end

    %% --- COMPUTE LAYER (AWS EKS) ---
    subgraph EKS ["🐳 AWS EKS Cluster (Compute Node)"]
        
        subgraph MS ["⚡ FastAPI Microservices"]
            GW["App: Gateway<br/>Port: 8000"]:::gateway
            ORCH["App: Orchestrator<br/>Port: 8002"]:::gateway
            REV["App: Reviewer<br/>Port: 8003"]:::gateway
        end

        subgraph CELERY ["⚙️ Distributed Asynchronous Workers"]
            WW["🐝 Webhook Worker<br/>Queue: 'webhook'"]:::worker
        end

        subgraph GRAPH ["🧠 Cognitive Engine"]
            LG["⚡ LangGraph State Machine<br/>State: {diff, patterns, findings}"]:::cognitive
        end
    end

    %% --- STATE & STORAGE LAYER ---
    subgraph DATA_LAYER ["💾 State & Storage Layer"]
        REDIS[("🔴 Redis Broker / Backend<br/>[Task Queue & State Cache]")]:::storage
        DB[("🐘 PostgreSQL Database<br/>[Async SQLAlchemy / Connection Pool]")]:::storage
    end

    %% --- CORE REQUEST LIFECYCLE FLOW ---
    GH -- "1. POST /webhook<br/>[PR Event Payload]" --> ALB
    ALB -- "2. Forward Traffic" --> GW
    
    %% Gateway operations
    GW -- "3. INSERT INTO pull_requests<br/>(status='pending')" --> DB
    GW -- "4. celery.send_task('analyze_pr')<br/>[Payload + installation_id]" --> REDIS
    
    %% Worker consumption
    REDIS -- "5. Fetch Task Context" --> WW
    WW -- "6. POST /analyze<br/>[Async HTTPX Client]" --> ORCH

    %% Orchestrator processing
    ORCH -- "7. Fetch Raw Diff / Code Changes" --> GH
    ORCH -- "8. SELECT FROM patterns<br/>(Context Injection)" --> DB
    ORCH -- "9. build_graph().invoke()" --> LG
    LG <--> LLM
    LG -- "10. Return Findings JSON" --> ORCH
    ORCH -- "11. INSERT INTO findings<br/>[Commit Transaction]" --> DB

    %% Reviewer Delivery & Fallback Protection
    ORCH -- "12. POST /post-review<br/>[Payload + installation_id]" --> REV
    
    %% Token Exchange & Posting
    REV -- "13. Dynamic Auth & Post Inline Reviews<br/>[Fallback to Global Summary on 422]" --> GH
    REV -- "14. UPDATE pull_requests<br/>(status='reviewed')" --> DB

    %% Component Inter-dependencies styling
    style EKS fill:#f5f6fa,stroke:#dcdde1,stroke-width:2px;
    style EXT fill:#f5f6fa,stroke:#dcdde1,stroke-width:2px;
    style DATA_LAYER fill:#fafafa,stroke:#dcdde1,stroke-width:2px;
