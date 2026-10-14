# RAG-Powered SEO Research & Marketing Analytics Assistant

An AI-powered marketing intelligence platform built on Databricks that combines Retrieval-Augmented Generation (RAG) with data analytics to deliver reliable SEO research and data-driven marketing insights. The assistant retrieves information from authoritative SEO documentation, generates evidence-based answers with source citations, and analyzes public search-trend data to identify emerging topics and potential content opportunities. The project integrates data ingestion, document processing, semantic search, vector embeddings, large language models (LLMs), and analytical workflows to transform unstructured research and structured marketing data into actionable insights.

> **Status:** in development

## Features

- **Cited SEO answers:** questions are answered from authoritative SEO documentation, with links to the source passages.
- **Search-trend analytics:** analysis of public search-trend data to surface rising topics and seasonality.
- **Content opportunities:** documentation knowledge combined with trend signals to suggest topics worth targeting.
- **Lakehouse-native:** ingestion, processing, indexing, serving and evaluation all run on Databricks.

## Architecture

```
 SEO docs (HTML/MD) ──► Bronze ──► Silver (clean text) ──► Chunks + embeddings ──► Vector Search index ─┐
                                                                                                        ├──► Agent (LLM + tools) ──► App / API
 Search-trend data  ──► Bronze ──► Silver ──► Gold (keyword × date × region metrics) ──► SQL tool ──────┘
```

| Layer | Components |
|---|---|
| Ingestion | Crawlers / loaders → Unity Catalog Volumes → Delta (Bronze) |
| Processing | Parsing, cleaning, chunking with source metadata (Silver) |
| Semantic search | Embedding model + Databricks Vector Search (Delta Sync index) |
| Analytics | Trend aggregations, growth/seasonality metrics (Gold) |
| Agent | Tool-calling LLM: `search_seo_docs` (retrieval with citations), `query_trends` (SQL over Gold tables) |
| Serving & evaluation | MLflow, Model Serving, Mosaic AI Agent Evaluation |
| Interface | Databricks App (chat + trend visualizations) |

## Project structure (planned)

```
src/
  ingestion/     # document and trend-data loaders
  processing/    # parsing, cleaning, chunking, embeddings
  analytics/     # trend metrics and opportunity scoring
  agent/         # tools, prompts, agent definition
  app/           # Databricks App UI
notebooks/       # exploration and demos
evals/           # evaluation datasets and scripts
resources/       # Databricks Asset Bundle resource definitions
databricks.yml
```

## Tech stack

Databricks (Delta Lake, Unity Catalog, Vector Search, Model Serving, Apps) · MLflow · Python · PySpark
