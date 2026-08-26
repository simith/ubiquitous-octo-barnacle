# 1. Prerequisites & Environment Setup

This section prepares the SAP BTP environment required for the MCP Server.

## 1.1 Create an SAP BTP Trial Account

> **Need a step-by-step walkthrough?** Follow the official SAP tutorial:
> [Create a Free Account on SAP BTP Trial](https://developers.sap.com/tutorials/hcp-create-trial-account/)

Sign in at [https://cockpit.hanatrial.ondemand.com/](https://cockpit.hanatrial.ondemand.com/) with your SAP Universal ID. A default `trial` subaccount is created automatically.

---

## 1.2 Subscribe to SAP Integration Suite

> **Need a step-by-step walkthrough?** Follow the official SAP tutorial:
> [Set Up SAP Integration Suite Trial](https://developers.sap.com/tutorials/cp-starter-isuite-onboard-subscribe)

In the BTP Cockpit, open **Services → Service Marketplace**, search for **Integration Suite**, and create a subscription with the `trial` plan.

Once subscribed, navigate to **Services → Instances and Subscriptions** and confirm Integration Suite shows **Subscribed**.

![Instances and Subscriptions — Integration Suite subscribed](images/step-01.png)

---

## 1.3 Assign Initial Role and Open Integration Suite

Before you can open Integration Suite, assign the provisioning role:

1. Go to **Security → Users** and select your user.
2. Click **Assign Role Collection**.
3. Select **Integration_Provisioner** and click **Assign Role Collection**.
4. **Log out and log back in** to apply the role.
5. Go to **Services → Instances and Subscriptions** and click **Integration Suite**.

**Activate IS capabilities:** Inside Integration Suite, click **Manage capability → Add capability** and activate both:

- **Build Integration Scenarios** (Cloud Integration)
- **Manage APIs** (API Management)

Save and wait for activation to complete, then log out and back in.

---

## 1.4 Assign Full Role Collections

After activating capabilities, assign the full role set so all IS navigation items are visible:

1. Go to **Security → Users**, select your user, and click **Assign Role Collection**.

| Role Collection | Description |
|---|---|
| `APIManagement.SelfService.Administrator` | API Portal Onboarding |
| `APIPortal.Administrator` | API Portal Admin |
| `AuthGroup.API.Admin` | Manages users and applications in Developer Hub |
| `AuthGroup.Content.Admin` | Manages content in Developer Hub |
| `AuthGroup.ContentAuthor` | Manages content |
| `AuthGroup.SelfService.Admin` | Self Service Admin in Developer Hub |
| `AuthGroup.Site.Admin` | Manages site updates in Developer Hub |
| `Integration_Provisioner` | Provisioning and basic IS configuration |
| `PI_Administrator` | SAP Process Integration — Administrator |
| `PI_Business_Expert` | SAP Process Integration — Business Expert |
| `PI_Integration_Developer` | SAP Process Integration — Developer |
| `Subaccount Administrator` | Administrative access to the subaccount |

![Assign Role Collection dialog — selecting roles](images/step-02.png)

![All role collections assigned for the user](images/step-03.png)

**Log out and log back in** after assigning all roles.

---

## 1.5 Open Integration Suite

Click **Integration Suite** in **Instances and Subscriptions**.

> **Tip:** If Discover, Design, or other navigation items are not visible, open Integration Suite in a new **incognito / private browsing window**.

![SAP Integration Suite Home page](images/step-04.png)

---

## Environment ready

- [ ] BTP Trial account created
- [ ] Integration Suite subscribed
- [ ] Integration_Provisioner role assigned and activated
- [ ] IS capabilities activated (API Management, Cloud Integration)
- [ ] Full role collections assigned
- [ ] IS accessible with full side navigation

Next: [Build the MCP Server →](02-build-mcp-server.md)
