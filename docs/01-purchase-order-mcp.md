# 1. Purchase Order MCP Server

This section walks you through the complete end-to-end process of building, deploying, and connecting a Purchase Order MCP Server. Every other server in this tutorial follows the same pattern — so read this one carefully.

**What you will build:**

```
AI Client  ──MCP──▶  SAP IS MCP Server  ──▶  API Artifact  ──▶  SAP Purchase Order API
```

---

## Part A — Create an Integration Package

**Why this step:** An **Integration Package** is the container that holds everything you build — API artifacts, MCP Servers, and their policies. Think of it as a project folder. You can keep all four servers in this one package.

1. In Integration Suite, go to **Design → Integrations and APIs**
2. Click **Create**

![Design — Integrations and APIs package list](images/edited/fig-03.png)

3. Fill in the package details:

    | Field | Value |
    |---|---|
    | Name | `MCP Workshop` (or any name you choose) |
    | Technical Name | Auto-populated — leave as-is |
    | Short Description | Optional |

4. Click **Save**

![Integration Package header edit form](images/edited/fig-04.png)

---

## Part B — Get the OpenAPI Spec from SAP Business Accelerator Hub

**Why this step:** SAP IS does not know the shape of the Purchase Order API on its own. An **OpenAPI specification** describes every operation, path, and field — SAP IS reads it to generate the API artifact (and later the MCP tools) automatically. You download that spec from the **SAP Business Accelerator Hub (BAH)**, SAP's public catalog of standard APIs.

1. Open the [SAP Business Accelerator Hub](https://api.sap.com/api/CE_PURCHASEORDER_0001/overview) — Purchase Order API page

![SAP Business Accelerator Hub — Purchase Order API overview](images/edited/fig-05.png)

2. In the **API Specification** section, download the spec as **OpenAPI JSON**. SAP IS imports the `.json` form reliably — do **not** use the OpenAPI YAML or OData EDMX options for this artifact.

![SAP BAH Purchase Order — API Specification section with the OpenAPI JSON download link](images/edited/fig-06.png)

3. Note the **Sandbox URL** shown on the page — you will need it in the next step:
    ```
    https://sandbox.api.sap.com
    ```

4. While on BAH, click the **Show API Key** button in the page header — it is available on **every** BAH page, so you do not need to open your profile. Copy the key; you will need it in Part D. *This key is what authenticates your calls to the SAP sandbox backend.*

!!! warning "OpenAPI version requirement"
    SAP IS requires **OpenAPI 3.0 (3.0.0–3.0.4)**. If the downloaded file starts with `"swagger": "2.0"`, it is Swagger 2.0 and must be converted before use. Check the first line of the file.

---

## Part C — Add the API Artifact

**Why this step:** The **API artifact** is SAP IS's managed proxy for the backend. It holds the connection URL, the service type, and — in the next step — the API key. The MCP Server you build later points at this artifact rather than at the backend directly, so all traffic stays governed and logged by SAP IS.

1. Inside your package, click **Edit** (if not already in edit mode)
2. Click **Add → API**

![Package Artifacts tab — Add dropdown with API option](images/edited/fig-07.png)

3. **Step 1 of the wizard — Select Runtime Profile:** Choose **Integration Cell** → click **Next**

![Add API wizard — Step 1: Select Runtime Profile](images/edited/fig-08.png)

4. **Step 2 — Select a Method:** Choose **URL or Specification** → click **Next**

![Add API wizard — Step 2: URL or Specification](images/edited/fig-09.png)

5. **Step 3 — Provide API Details:**

    | Field | Value |
    |---|---|
    | Upload file | Select the **OpenAPI JSON** file you downloaded from BAH |
    | URL | `https://sandbox.api.sap.com/s4hanacloud/sap/opu/odata4/sap/api_purchaseorder_2/srvd_a2x/sap/purchaseorder/0001` |
    | Service Type | `OData` |
    | API Base Path | `/purchaseorder/0001` |

    !!! note "Use the full backend URL"
        The **URL** must be the complete service endpoint (all the way to `.../purchaseorder/0001`), not just `https://sandbox.api.sap.com`. The **API Base Path** is the short path your calls are routed on.

6. Click **Add**

![Add API wizard — Step 3: Provide API details](images/edited/fig-10.png)

The API artifact is created with status **Not Deployed**.

7. Open the API artifact → go to the **Authorization** tab → enable **Trust Upstream MCP Authorization**, then **Save**. *This lets the MCP Server (built later) pass its caller's authorization through to this API without a second login.*

![API artifact Authorization — Policy Settings with Trust Upstream MCP Authorization enabled](images/edited/fig-11.png)

---

## Part D — Add the API Key via Content Modifier

**Why this step:** The SAP sandbox rejects any request that does not carry a valid `APIKey` header. Rather than ask the AI agent (or your client) to send it, you inject the key automatically inside the artifact using a **Content Modifier** — so the secret lives in SAP IS, never in the caller.

1. Open the API artifact and go to the **Policies** tab

![API Policies tab — policy flow diagram](images/edited/fig-12.png)

2. Click **Edit** to enter edit mode
3. Click on the step immediately after **Authorization 1** to select it as the insertion point

![Policies — Authorization step selected with Add Flow Step tooltip](images/edited/fig-13.png)

4. Click the **+** (Add Flow Step) and search for **Content Modifier** → select it

![Add Flow Step dialog — Content Modifier search result](images/edited/fig-14.png)

5. Click on the new **Content Modifier** step to configure it
6. Open the **Message Header** tab → click **Add**
7. Fill in the following:

    | Field | Value |
    |---|---|
    | Action | `Create` |
    | Name | `APIKey` |
    | Source Type | `Constant` |
    | Source Value | *Your API key from SAP BAH* |

![Content Modifier — APIKey header configured](images/edited/fig-15.png)

8. Click **Save**

---

## Part E — Deploy the API Artifact

1. Click **Deploy** in the toolbar
2. Confirm deployment to the **Integration Cell** runtime

![Deploy confirmation dialog](images/edited/fig-16.png)

3. Wait until **Runtime Status** shows **STARTED**

![API artifact deployed — Runtime Status: STARTED](images/edited/fig-17.png)

!!! note "Warning badges on policy steps"
    If you see a warning badge on a step in the Policies tab, this is a design-time check and does not block deployment. You can safely proceed.

---

## Part F — Add the MCP Server Artifact

1. Go back to your package. Click **Edit** → **Add → MCP Server**

![Package Artifacts tab — Add dropdown with MCP Server highlighted](images/edited/fig-18.png)

2. **Step 1 — Select Source Type:** Choose **API** → click **Next**

![Add MCP Server wizard — Step 1: Source Type API](images/edited/fig-19.png)

3. **Step 2 — Provide MCP Details:**
    - Click **Select an API** and choose the Purchase Order API you just deployed

    ![Select API dialog — Purchase Order API listed](images/edited/fig-20.png)

    - Fill in the remaining fields:

    | Field | Example value |
    |---|---|
    | Name | `PurchaseOrder_MCP` |
    | MCP Path | `/purchaseordermcp` |
    | Version | `1.0.0` |
    | Runtime Profile | `Integration Cell` |

    ![Add MCP Server wizard — Step 2: MCP details form](images/edited/fig-21.png)

4. **Step 3 — Create Tools:** Select the API operations to expose as MCP tools.

    Select the **GET** operations only — e.g. list purchase orders, get a purchase order by key, get line items.

    !!! warning "This backend is read-only"
        **Do not select POST, PATCH, or DELETE operations.** The SAP sandbox backend does not permit write operations, so those tools would fail at call time even though the wizard lets you pick them. Expose GET operations only.

    ![Add MCP Server wizard — Step 3: Select tools](images/edited/fig-22.png)

5. Click **Add**

!!! tip "Auto-wired Policies"
    When an MCP Server is created from an API artifact, the Policies HTTP connection is **automatically configured** to route through the API artifact. You do not need to manually set up authentication in the Policies tab for this server type. This is different from Sections 3 and 4 (Spotify and Twilio), where you must configure it manually.

6. **Add the Developer Hub scope.** Open the new **PurchaseOrder_MCP** artifact → **Authorization** tab → **Policy Setting** → **Scope**, and add the scope:

    ```
    uaa.resource
    ```

    Then **Save**.

    !!! info "Why `uaa.resource`?"
        This is the scope carried by the access token that Developer Hub issues for your subscription (you create those credentials in Part I). Adding it here tells the MCP Server to accept tokens minted by Developer Hub. Without it, authenticated calls from your agent are rejected even though the token is valid.

![MCP Server Authorization — Policy Settings with scope API.invoke and uaa.resource](images/edited/fig-23.png)

---

## Part G — Deploy the MCP Server

1. Open the new MCP Server artifact
2. Review the **Overview** tab — note the **MCP URL** (you will need this later)

![MCP Server Overview — details and MCP URL](images/edited/fig-24.png)

3. Click **Deploy** and confirm

![MCP Server — Deploy confirmation dialog](images/edited/fig-25.png)

4. Wait until **Runtime Status** shows **STARTED**

![MCP Server deployed — Runtime Status: STARTED](images/edited/fig-26.png)

---

## Part H — Publish to Developer Hub

The **Developer Hub** is SAP's API catalog. Publishing your MCP Server here lets AI agents discover and subscribe to it, and generates the OAuth2 credentials your agent will use.

**Navigate to Developer Hub:**

1. In the Integration Suite header bar, click the **Explore our ecosystem** icon
2. Click **Developer Hub**

![Integration Suite — Explore our ecosystem: publish to Developer Hub](images/edited/fig-27.png)

**Create a Product:**

3. In the Developer Hub, go to **Admin Center → Manage Content**
4. Click the **Business Systems** tab — your Integration Suite subaccount appears as a registered business system
5. Click on your business system to open it

![Developer Hub — Manage Content: Business Systems tab](images/edited/fig-28.png)

6. Go to the **MCP Servers** tab — your deployed MCP Server is listed here
7. Check the box next to your MCP Server to select it

!!! note "Trial vs. enhanced tenants"
    On a **trial** Integration Suite tenant this tab is labelled **MCP Servers**. On an **enhanced (production)** tenant the same content lives under the **APIs and AI Artifacts** tab. The steps are otherwise identical.

![Developer Hub — Business System: MCP Servers tab with MCP Server selected](images/edited/fig-29.png)

8. Click **Create Product** and enter a name, ID, and description of your choice

![Developer Hub — Create Product dialog](images/edited/fig-30.png)

9. Click **Publish** → confirm in the dialog that appears

![Developer Hub — publish request confirmation dialog](images/edited/fig-31.png)

10. Navigate to **Scheduled Requests** and wait until the status changes to **Success**

![Developer Hub — Scheduled Requests showing publish status](images/edited/fig-32.png)

---

## Part I — Subscribe and Get Credentials

AI agents authenticate using credentials generated from a **subscription** to your product.

1. Click the **Developer Hub** logo to return to the home page
2. Find and click your published product

![Developer Hub — products catalog homepage](images/edited/fig-33.png)

3. Go to the **MCP Servers** tab to see the MCP Server inside the product
4. Click **Subscribe** on the MCP Server card → select **Create New Subscription for Agent**

![Developer Hub — Create New Subscription for Agent dialog](images/edited/fig-34.png)

5. Enter a name and short description → click **Create**

**Retrieve your credentials:**

6. Click the **Developer Hub** logo → find your product → click **Associated Subscriptions**
7. Click your subscription name to open it
8. The credentials page shows:

    | Credential | What it is |
    |---|---|
    | **Token URL** | OAuth2 endpoint your client calls to get a bearer token |
    | **Key** | Client ID |
    | **Secret** | Client Secret |

![Developer Hub — Agent subscription credentials page](images/edited/fig-35.png)

!!! warning "Keep your credentials confidential"
    The **Key**, **Secret**, and any bearer token are live credentials. Store them only in your local `mcp.json`, and never paste them into screenshots, chat, or shared files.

---

## Part J — Quick Smoke Test

Before moving on, confirm the MCP Server is responding correctly with a quick `curl` test.

!!! tip "No terminal? Hand it to an AI assistant"
    You don't have to run these commands by hand. You can paste the requests below — along with your credentials — into an AI assistant such as **Claude** or **GitHub Copilot** and ask it to execute them. It will run the calls and report the results the same way.

Replace the placeholders with your actual values:

```bash
# Step 1: Get a bearer token
curl -s -X POST "YOUR_TOKEN_URL" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -u "YOUR_KEY:YOUR_SECRET" \
  -d "grant_type=client_credentials"
```

Save the `access_token` from the response, then:

```bash
# Step 2: Initialize the MCP connection and list tools
curl -s -X POST "YOUR_MCP_URL" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
```

!!! warning "The Accept header is required"
    SAP Integration Suite's MCP gateway requires **both** `application/json` and `text/event-stream` in the Accept header. Without it you will receive `400 Bad Request: Accept must contain both 'application/json' and 'text/event-stream'`.

A successful response looks like:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "tools": [
      { "name": "get_PurchaseOrder", "description": "Get entities from PurchaseOrder", ... },
      ...
    ]
  }
}
```

If you see tools listed — your Purchase Order MCP Server is responding. ✅

Finally, **call one of the GET tools** to prove the whole chain works end-to-end — MCP gateway → API artifact → SAP backend. Pick a tool name from the `tools/list` response (e.g. `get_PurchaseOrder`) and call it:

```bash
# Step 3: Call a GET tool to fetch real data
curl -s -X POST "YOUR_MCP_URL" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"get_PurchaseOrder","arguments":{}}}'
```

A successful call returns real purchase-order records in the `result.content` field. If you get data back, the end-to-end path is live. ✅

!!! note "`initialize` first in a real client"
    `tools/list` and `tools/call` work directly here because the gateway accepts them statelessly for a smoke test. A full MCP client should still send the `initialize` request first — see [Section 5](05-ai-agent.md).

---

## Checklist

- [ ] Integration Package created
- [ ] OpenAPI JSON spec downloaded from SAP BAH (OpenAPI 3.0)
- [ ] API artifact created with the full backend URL and base path
- [ ] **Trust Upstream MCP Authorization** enabled on the API artifact
- [ ] Content Modifier configured with `APIKey` header
- [ ] API artifact deployed (STARTED)
- [ ] MCP Server artifact created from API artifact with **GET** tools selected
- [ ] `uaa.resource` scope added to the MCP Server's Authorization
- [ ] MCP Server deployed (STARTED)
- [ ] Product published in Developer Hub (Scheduled Requests shows Success)
- [ ] Agent subscription created and credentials (Token URL, Key, Secret) saved

Next: [Business Partner MCP Server →](02-business-partner-mcp.md)
