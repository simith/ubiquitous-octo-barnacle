# Introduction

Large Language Models (LLMs) are trained on vast amounts of information, giving them a broad understanding of the world and the ability to answer a wide range of questions with a reasonable level of accuracy.

For example, if you ask an LLM about your company, it may be able to provide general information based on what it has learned from publicly available sources. But what happens when we move from general knowledge to **specific, real-time business questions**?

Imagine asking:

> *”How much revenue is at risk if Customer ABC defaults on its outstanding invoices next week?”*

Or:

> *”Which customers currently have overdue Accounts Receivable balances, and what is their total exposure?”*

The LLM cannot answer these questions reliably because the information required to answer them — your customer data, invoices, payment history, credit limits, and financial systems — is **not part of its general knowledge**.

This is where **Model Context Protocol (MCP)** becomes important.

MCP provides a standardized way for an LLM to securely connect to external systems, applications, and data sources. Instead of expecting the LLM to already know the answer, we can give it access to the **right business context at the time the question is asked**.

The LLM provides the reasoning and intelligence. MCP provides the connection to the enterprise data and tools needed to turn that intelligence into a meaningful business answer.

---

## What you will build

By the end of this tutorial you will have a working MCP Server hosted on SAP Integration Suite that any MCP-compatible AI client can discover and call.

```
AI Client  ──MCP──►  SAP Integration Suite MCP Server  ──►  SAP Backend API
```

## What you need

!!! info “Prerequisites”
    - A free SAP BTP Trial account — [create one here](https://developers.sap.com/tutorials/hcp-create-trial-account/)
    - Basic familiarity with SAP BTP Cockpit
    - An MCP-compatible AI client (Claude Desktop, Cursor, or similar)

!!! tip “Estimated time”
    Allow **60–90 minutes** to complete the full tutorial end-to-end.

