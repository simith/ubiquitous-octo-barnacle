# 5. End-to-End Checklist

Use this page as the quick validation sheet when running the tutorial.

## BTP

- [ ] SAP BTP Trial account created
- [ ] `trial` subaccount opened
- [ ] Integration Suite subscribed
- [ ] Subscription status is `Subscribed`

## Access

- [ ] Required role collections assigned
- [ ] Logged out/in after role assignment

## Authentication

- [ ] `Process Integration Runtime` instance created
- [ ] `integration-flow` plan selected
- [ ] Service key created
- [ ] `clientid` captured
- [ ] `clientsecret` captured
- [ ] `tokenurl` captured

## Backend

- [ ] Destination created
- [ ] Backend URL configured
- [ ] Authentication configured
- [ ] API key configured if required
- [ ] **Check Connection** succeeds

## API

- [ ] Integration Package created
- [ ] API artifact created
- [ ] API specification uploaded
- [ ] API deployed
- [ ] Runtime status is `STARTED`
- [ ] API proxy URL captured

## MCP

- [ ] MCP Server artifact created
- [ ] MCP URL captured
- [ ] IP Filter configured
- [ ] Surge Protection configured
- [ ] Quota configured
- [ ] No red validation badges
- [ ] MCP Server deployed
- [ ] Runtime status is `STARTED`

## AI Client

- [ ] MCP URL entered
- [ ] OAuth2 configured
- [ ] Client ID entered
- [ ] Client secret entered securely
- [ ] Token URL entered
- [ ] Client connected
- [ ] MCP tools visible
- [ ] Test query successfully invokes a tool

## Success

You have completed the tutorial when an MCP-compatible AI client can discover and call the tools exposed by the deployed SAP Integration Suite MCP Server.

---

## What the original tutorial covers

The supplied tutorial describes this end-to-end sequence:

1. BTP Trial Account
2. Integration Suite Subscription
3. Role Collections
4. OAuth2 Service Instance & Key
5. Destination
6. Integration Package
7. API Artifact
8. MCP Server Artifact
9. Governance Policies
10. Deployment
11. AI Client Connection

This repository reorganizes those same steps into a GitHub-oriented documentation flow. fileciteturn0file0L549-L563
