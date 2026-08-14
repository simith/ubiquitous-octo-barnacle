# 3. Govern & Deploy the MCP Server

The MCP Server is now created. Before exposing it to an AI client, configure governance policies and deploy it.

## 3.1 Open the Policies tab

Open the MCP Server artifact and select **Policies**.

![MCP Server Policies tab — default flow](images/step-46.png)

The default flow is:

```text
Agent
  ↓
MCP
  ↓
Authentication
  ↓
Authorization
  ↓
Request Reply
```

Authentication is pre-configured by the platform and is the first step.

---

## 3.2 Add an IP Filter

Select **Add Flow Step** between Authentication and Authorization.

![MCP Server Policies — Add Flow Step button](images/step-48.png)

Choose **IP Filter** from the Traffic Management section.

![Add Flow Step menu — IP Filter](images/step-50.png)

Place it after **Authentication** and before **Surge Protection**.

Configure:

| Setting | Value |
|---|---|
| Default Rule | `Deny` |
| Type | `X-Forwarded-For` |
| Additional rule | `Allow` |
| IP Address | `<your-ip>/32` |

A single IP should use CIDR notation with `/32`.

![IP Filter configured — Default Rule: Deny, Allow rule with IP address](images/step-52.png)

Save the policy.

![Policy flow with IP Filter added](images/step-53.png)

> Be careful with IP filtering if your client IP changes. A rule that allows only one source IP can prevent your AI client from reaching the server after a network change.

---

## 3.3 Add Surge Protection

Select:

**Add Flow Step → Traffic Management → Surge Protection**

Place it after the IP Filter.

![Add Flow Step menu — Surge Protection](images/step-55.png)

Configure:

```text
Calls:         20
Duration:      1
Duration Unit: Seconds
```

Save.

![Policy flow — IP Filter and Surge Protection added](images/step-60.png)

---

## 3.4 Add a Quota

Select:

**Add Flow Step → Traffic Management → Quota**

Place it after Surge Protection.

![Add Flow Step menu — Quota](images/step-62.png)

Configure:

```text
Allow: 50
Per:   Day
```

Save.

![Quota policy configured — 50 per day](images/step-66.png)

---

## 3.5 Verify the final policy flow

The tutorial's final flow is:

```text
Authentication
      ↓
IPFilter
      ↓
SurgeProtection
      ↓
Quota
      ↓
Authorization
      ↓
Request Reply
```

Before deployment:

- [ ] No policy step shows a red validation badge
- [ ] IP Filter is configured
- [ ] Surge Protection is configured
- [ ] Quota is configured
- [ ] Changes are saved

---

## 3.6 Deploy the MCP Server

In the MCP Server artifact:

1. Click **Save**.
2. Verify that there are no red validation badges.
3. Click **Deploy**.
4. Wait for:

```text
Status: Deployed
Runtime Status: STARTED
```

![MCP Server deployed — Runtime Status: STARTED, MCP URL active](images/step-75.png)

The MCP URL shown at the top of the artifact is now active.

Copy the MCP URL. You'll use it in the AI client configuration.

### If deployment fails

Start with the policy flow.

A red validation badge indicates a configuration problem. Resolve the policy error, save again, and redeploy.

---

## Deployment complete

You should now have:

```text
MCP URL
OAuth2 token URL
OAuth2 client ID
OAuth2 client secret
```

Keep the credentials private.

Next: [Connect an AI client →](04-connect-ai-clients.md)
