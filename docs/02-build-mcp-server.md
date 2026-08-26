# 2. Build the API and MCP Server

This section creates the API artifact and MCP Server artifact inside SAP Integration Suite.

## 2.1 Create an Integration Package

1. In Integration Suite, open **Design → Integrations and APIs**.
2. Click **Create** to create a new Integration Package.

![Design — Integrations and APIs package list](images/step-05.png)

3. Fill in the package details:
   - **Name:** `Purchase Order` (or your chosen name)
   - **Technical Name:** auto-populated
   - **Short Description:** optional

![Integration Package header edit form](images/step-06.png)

4. Click **Save**.

---

## 2.2 Add an API Artifact

### Get the API specification from SAP Business Accelerator Hub

Open the [SAP Business Accelerator Hub](https://api.sap.com/api/CE_PURCHASEORDER_0001/overview) and locate the **Purchase Order** API.

![SAP Business Accelerator Hub — Purchase Order API overview](images/step-10.png)

Note the **Sandbox URL** and download the **OpenAPI YAML file** from the **API Specification** section on the hub. You will use both in the next step.

### Add the API artifact

1. Inside your package, click **Edit** if not already in edit mode.
2. Click **Add → API**.

![Package Artifacts tab — Add dropdown with API option](images/step-07.png)

3. **Step 1 — Select Runtime Profile:** Choose **Integration Cell** and click **Next**.

![Add API wizard — Step 1: Select Runtime Profile](images/step-08.png)

4. **Step 2 — Select a Method:** Choose **URL or Specification** and click **Next**.

![Add API wizard — Step 2: URL or Specification](images/step-09.png)

5. **Step 3 — Provide API Details:**
   - Upload the **OpenAPI YAML file** downloaded from the SAP Business Accelerator Hub.
   - **URL:** `https://sandbox.api.sap.com`
   - **Service Type:** `OData`
   - **API Base Path:** `/s4hanacloud/sap/opu/odata4/sap/api_purchaseorder_2/srvd_a2x/sap/purchaseorder/0001`
   - Click **Add**.

![Add API wizard — Step 3: Provide API details](images/step-11.png)

The API artifact is created with status **Not Deployed**.

![API artifact created — Overview tab, Not Deployed](images/step-12.png)

---

## 2.3 Add a Content Modifier to Pass the API Key

The SAP sandbox requires an `APIKey` header. Add a **Content Modifier** step to inject it automatically.

1. Open the API artifact and go to the **Policies** tab.

![API Policies tab — policy flow diagram](images/step-13.png)

2. Click **Edit** to enter edit mode. Select the step after **Authorization 1** to add after it.

![Policies — Authorization step selected with Add Flow Step tooltip](images/step-14.png)

3. Click the **+** (Add Flow Step) and search for **Content Modifier**. Select it.

![Add Flow Step dialog — Content Modifier search result](images/step-15.png)

4. In the **Content Modifier** configuration, open the **Message Header** tab and click **Add**:

   | Field | Value |
   |---|---|
   | Action | `Create` |
   | Name | `APIKey` |
   | Source Type | `Constant` |
   | Source Value | *your API key from the SAP Business Accelerator Hub* |

![Content Modifier — APIKey header configured](images/step-16.png)

---

## 2.4 Deploy the API

1. Click **Deploy** in the toolbar.

![Policy flow — Deploy button visible](images/step-17.png)

2. Confirm deployment to the **Integration Cell** runtime.

![Deploy confirmation dialog](images/step-18.png)

> **Note:** If a warning badge appears on a step, this is a design-time constraint and does not block runtime. You can safely proceed with deployment.

3. Wait until the Runtime Status shows **STARTED**.

![API artifact deployed — Runtime Status: STARTED](images/step-19.png)

---

## 2.5 Add an MCP Server Artifact

1. Inside your package, click **Edit** then **Add → MCP Server**.

![Package Artifacts tab — Add dropdown with MCP Server highlighted](images/step-20.png)

2. **Step 1 — Select Source Type:** Choose **API** and click **Next**.

![Add MCP Server wizard — Step 1: Source Type API](images/step-21.png)

3. **Step 2 — Provide MCP Details:**
   - Click **Select an API** and choose your deployed Purchase Order API.

![Select API dialog — Purchase Order API listed](images/step-22.png)

   - Fill in values of your choice:

   | Field | Example |
   |---|---|
   | Name | `Purchase_Order_mcpServer` |
   | MCP Path | `/mcp` |
   | Version | `1.0.0` |
   | Runtime Profile | `Integration Cell` |

![Add MCP Server wizard — Step 2: MCP details form](images/step-23.png)

4. **Step 3 — Create Tools:** Select the API resources to expose as MCP tools. Choose the operations your AI client will need, then click **Add**.

![Add MCP Server wizard — Step 3: Select tools](images/step-24.png)

---

## 2.6 Deploy the MCP Server

1. Open the new MCP Server artifact. Review the **Overview** tab to confirm the MCP URL and runtime settings.

![MCP Server Overview — details and MCP URL](images/step-25.png)

2. Go to the **Policies** tab.

![MCP Server Policies tab — policy flow diagram](images/step-26.png)

3. Click **Deploy**.

![MCP Server — Deploy confirmation dialog](images/step-27.png)

4. Wait until Runtime Status shows **STARTED**.

![MCP Server deployed — Runtime Status: STARTED](images/step-28.png)

---

## MCP Server ready

- [ ] Integration Package created
- [ ] API artifact created from BAH specification
- [ ] Content Modifier configured with APIKey header
- [ ] API artifact deployed (STARTED)
- [ ] MCP Server artifact created with tools selected
- [ ] MCP Server deployed (STARTED)

Next: [Publish to Developer Hub →](03-govern-and-deploy.md)
