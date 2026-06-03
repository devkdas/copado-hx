# Agentforce Action — Copado Headless DevOps

This directory contains all files needed to expose **copado-hx** commands as **Agentforce Agent Actions** — callable by any Salesforce Agentforce agent (Einstein Copilot, custom agents, or multi-agent orchestrations).

## Files

| File | Type | Purpose |
|------|------|---------|
| `CopadoHxActions.cls` | Apex Class | 5 `@InvocableMethod` actions: commit, promote, deploy, getStories, getJobStatus |
| `CopadoHxActions.cls-meta.xml` | Metadata | Apex class configuration (API v61.0) |
| `CopadoHxNamedCredential.namedCredential-meta.xml` | Named Credential | Secure callout endpoint for Copado Actions API |
| `CopadoHxActionPlugin.genAiPlugin-meta.xml` | GenAiPlugin | Registers the 5 Apex methods as Agentforce agent actions |

## What Each Action Does

| Action | `@InvocableMethod` | Inputs | Calls |
|--------|---------------------|--------|-------|
| **Commit** | `commit()` | storyId, message | Actions API `RunJobTemplate` (`sfdx_commit_1`) |
| **Promote** | `promote()` | storyId, environment, validateOnly | Actions API `RunJobTemplate` (`sfdx_promote_1`) |
| **Deploy** | `deploy()` | storyId, environment | Actions API `RunJobTemplate` (`sfdx_deploy_1`) |
| **Get Stories** | `getStories()` | pipeline, status | SOQL `copado__User_Story__c` |
| **Get Job Status** | `getJobStatus()` | jobExecutionId | SOQL `copado__JobExecution__c` |

## Prerequisites

- Salesforce org with **Agentforce** enabled (any edition)
- **Copado** installed in the org (CI/CD pipelines configured)
- **Actions API webhook key** from Copado Account Summary > Copado Actions API tab

## Installation

### 1. Deploy metadata to Salesforce

```bash
# Using Salesforce CLI
sf project deploy start -d agentforce/ -o myOrg
```

Or use a deployment package in Setup > Deployment Settings.

### 2. Configure the Named Credential

After deployment, go to **Setup > Named Credentials** and edit `CopadoHx_API`:

- **Endpoint**: `https://app-api.copado.com`
- Leave authentication as `NoAuthentication`
- The webhook key is passed as a query parameter by the Apex class

### 3. Activate in Agentforce Builder

1. Navigate to **Setup > Agentforce Builder**
2. Create or edit an agent / topic
3. Add the 5 custom actions to the agent's action library
4. Each action has a `description` field that the Atlas Reasoning Engine uses to decide when to call it
5. Test the actions using Agentforce Testing Center

## Agent Script Example (Optional)

For deterministic multi-step workflows, add an Agent Script to your topic:

```yaml
topic: "copado_devops"
instructions: |
  You are a Copado DevOps agent. You can commit, promote, and deploy user stories.
  Never deploy to PROD without asking the human first.
  Always check job status after triggering an action.

actions:
  - copado_commit
  - copado_promote
  - copado_deploy
  - copado_get_stories
  - copado_get_job_status
```

## Security

- **Named Credential** ensures the Actions API endpoint is configured centrally
- **Sharing rules** apply — the agent respects the user's field-level security
- **No credentials in Apex** — the webhook key is passed via `callout:CopadoHx_API` Named Credential
- **`with sharing`** on the class ensures Salesforce sharing rules are enforced
- **`String.escapeSingleQuotes()`** prevents SOQL injection in dynamic queries

## Testing

Deploy to a sandbox or Developer Edition with Agentforce enabled:

```bash
sf project deploy start -d agentforce/ -o mySandbox
sf org open -o mySandbox
# → Agentforce Builder → Add actions → Test
```

## Limitations

- Requires Salesforce org with **Agentforce license**
- Requires **Copado** to be installed in the org
- The Actions API webhook key must be registered as a Named Credential parameter
