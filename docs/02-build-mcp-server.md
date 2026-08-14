# 2. Build the MCP Server

Now we create the Integration Suite artifacts that turn the backend API into an MCP endpoint.

## Architecture

```text
Integration Package
        │
        ├── API Artifact
        │      │
        │      └── HTTP Proxy → Backend API
        │
        └── MCP Server Artifact
               │
               └── exposes API capabilities as MCP tools
```

---

## 2.1 Create an Integration Package

Open SAP Integration Suite from the BTP subscription.

![SAP Integration Suite home dashboard](../images/step-16.png)

Navigate to:

**Design → Integrations and APIs**

![Integration Suite Design — Integrations and APIs package list](../images/step-17.png)

Create a new package.

Recommended fields:

| Property | Value |
|---|---|
| Name | Your package name |
| Technical Name | Auto-filled or your chosen technical name |
| Short Description | Brief description |
| Version | `1.0.0` |
| Vendor | Optional |

![Create integration package — header form](../images/step-18.png)

Save the package.

The new package initially contains no artifacts.

![New package Artifacts tab — no data](../images/step-19.png)

---

## 2.2 Create the API Artifact

Inside the package:

1. Select **Edit**.
2. Select **Add**.
3. Choose **API**.

![Add menu — select artifact type](../images/step-21.png)

4. Select **Integration** as the runtime profile.

![Add API — select runtime profile](../images/step-22.png)

5. Select **URL or Specification**.

![Add API — select a method](../images/step-24.png)

6. Upload the API specification obtained from SAP Business Accelerator Hub.
7. Complete the remaining API details.

![Add API — provide API details](../images/step-25.png)

8. Open the **Policies** tab to review the default flow.
9. Deploy the API.

![Deploy API artifact — confirm dialog](../images/step-29.png)

The default policy flow is:

```text
Client
  ↓
HTTPS
  ↓
Authentication
  ↓
Authorization
  ↓
Request Reply
  ↓
HTTP
  ↓
Target
```

After deployment, wait until:

```text
Status: Deployed
Runtime Status: STARTED
```

![API artifact deployed — Status: Deployed, Runtime Status: STARTED](../images/step-31.png)

Record the API proxy URL.

### Why this matters

The API artifact is the HTTP-facing proxy layer. The MCP Server artifact uses this API layer as the underlying target that will be exposed as structured MCP tools.

---

## 2.3 Create the MCP Server Artifact

Inside the same package:

1. Select **Actions → Create**.
2. Choose **MCP Server**.

![Add MCP Server — Step 1: Select Source Type](../images/step-33.png)

3. Select the deployed API artifact as the source.

![Add MCP Server — Select an API from the available list](../images/step-37.png)

4. Enter a name, for example:

```text
<PackageName>_mcpServer
```

![Add MCP Server — Provide MCP details form](../images/step-36.png)

5. Fill in the details and create the artifact.

![Add MCP Server — MCP details filled](../images/step-39.png)

The MCP Server artifact contains:

- **Overview**
- **MCP Configuration**
- **Policies**

![MCP Server artifact — Overview tab](../images/step-42.png)

The artifact header displays the MCP endpoint.

It follows the pattern:

```text
https://<tenant>.integration.cloud.sap/<path>
```

The package should now contain two artifacts:

```text
<API name>          → API
<MCP Server name>   → MCP Server
```

![Integration package with both API and MCP Server artifacts](../images/step-43.png)

---

## What you have built

You now have the two key layers:

**API Artifact**

Provides the HTTP proxy and target connection.

**MCP Server Artifact**

Wraps the API capability and exposes it to MCP-compatible AI clients as structured tools.

Next: [Add governance and deploy →](03-govern-and-deploy.md)
