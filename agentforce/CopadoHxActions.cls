global with sharing class CopadoHxActions {

    // ─── Commit ────────────────────────────────────────────────────────────

    global class CommitInput {
        @InvocableVariable(required=true description='User Story ID (18-char Salesforce ID or US-xxxxx name)')
        global String storyId;
        @InvocableVariable(required=false description='Commit message')
        global String message;
    }

    global class CommitOutput {
        @InvocableVariable(description='Job Execution ID')
        global String jobExecutionId;
        @InvocableVariable(description='Status of the commit operation')
        global String status;
    }

    @InvocableMethod(label='Commit Metadata' description='Commits metadata changes from a user story via Copado Actions API. Use when the user wants to save changes to a user story branch.')
    global static List<CommitOutput> commit(List<CommitInput> inputs) {
        List<CommitOutput> results = new List<CommitOutput>();
        for (CommitInput input : inputs) {
            CommitOutput out = new CommitOutput();
            try {
                Map<String, Object> data = new Map<String, Object>();
                data.put('storyId', input.storyId);
                data.put('commitMessage', input.message != null ? input.message : 'feat: update via Agentforce');
                data.put('runAfterInstantiation', true);
                String body = buildPayload('sfdx_commit_1', data);
                String raw = callActionsApi(body);
                out.jobExecutionId = extractId(raw);
                out.status = 'In Progress';
            } catch (Exception e) {
                out.status = 'Error: ' + e.getMessage();
            }
            results.add(out);
        }
        return results;
    }

    // ─── Promote ───────────────────────────────────────────────────────────

    global class PromoteInput {
        @InvocableVariable(required=true description='User Story ID')
        global String storyId;
        @InvocableVariable(required=false description='Target environment (default: UAT)')
        global String environment;
        @InvocableVariable(required=false description='Set to true for validation-only deployment')
        global Boolean validateOnly;
    }

    global class PromoteOutput {
        @InvocableVariable(description='Job Execution ID')
        global String jobExecutionId;
        @InvocableVariable(description='Status of the promote operation')
        global String status;
    }

    @InvocableMethod(label='Promote User Story' description='Promotes a user story to the next environment via Copado Actions API. Supports --validate for dry-run.')
    global static List<PromoteOutput> promote(List<PromoteInput> inputs) {
        List<PromoteOutput> results = new List<PromoteOutput>();
        for (PromoteInput input : inputs) {
            PromoteOutput out = new PromoteOutput();
            try {
                Map<String, Object> data = new Map<String, Object>();
                data.put('storyId', input.storyId);
                data.put('targetEnvironment', input.environment != null ? input.environment : 'UAT');
                data.put('runAfterInstantiation', true);
                if (input.validateOnly == true) {
                    data.put('validateOnly', true);
                }
                String body = buildPayload('sfdx_promote_1', data);
                String raw = callActionsApi(body);
                out.jobExecutionId = extractId(raw);
                out.status = 'In Progress';
            } catch (Exception e) {
                out.status = 'Error: ' + e.getMessage();
            }
            results.add(out);
        }
        return results;
    }

    // ─── Deploy ────────────────────────────────────────────────────────────

    global class DeployInput {
        @InvocableVariable(required=true description='User Story ID')
        global String storyId;
        @InvocableVariable(required=false description='Target environment (default: PROD)')
        global String environment;
    }

    global class DeployOutput {
        @InvocableVariable(description='Job Execution ID')
        global String jobExecutionId;
        @InvocableVariable(description='Status of the deploy operation')
        global String status;
    }

    @InvocableMethod(label='Deploy to Production' description='Deploys a user story to production via Copado Actions API. This is a destructive action — use only after validation and human approval.')
    global static List<DeployOutput> deploy(List<DeployInput> inputs) {
        List<DeployOutput> results = new List<DeployOutput>();
        for (DeployInput input : inputs) {
            DeployOutput out = new DeployOutput();
            try {
                Map<String, Object> data = new Map<String, Object>();
                data.put('storyId', input.storyId);
                data.put('targetEnvironment', input.environment != null ? input.environment : 'PROD');
                data.put('runAfterInstantiation', true);
                String body = buildPayload('sfdx_deploy_1', data);
                String raw = callActionsApi(body);
                out.jobExecutionId = extractId(raw);
                out.status = 'In Progress';
            } catch (Exception e) {
                out.status = 'Error: ' + e.getMessage();
            }
            results.add(out);
        }
        return results;
    }

    // ─── Get User Stories ─────────────────────────────────────────────────

    global class StoryFilter {
        @InvocableVariable(required=false description='Pipeline ID to filter by')
        global String pipeline;
        @InvocableVariable(required=false description='Status to filter by (e.g. In Progress, Completed)')
        global String status;
    }

    global class UserStory {
        @InvocableVariable(description='Salesforce record ID')
        global String Id;
        @InvocableVariable(description='User story name (e.g. US-0000024)')
        global String Name;
        @InvocableVariable(description='Status of the user story')
        global String copado_Status__c;
        @InvocableVariable(description='Pipeline the story belongs to')
        global String copado_Pipeline__c;
    }

    @InvocableMethod(label='Get User Stories' description='Retrieves user stories from the Copado pipeline. Returns Id, Name, Status, and Pipeline for each story.')
    global static List<List<UserStory>> getStories(List<StoryFilter> filters) {
        List<List<UserStory>> results = new List<List<UserStory>>();
        for (StoryFilter filter : filters) {
            List<UserStory> stories = new List<UserStory>();
            try {
                String query = 'SELECT Id, Name, copado__Status__c, copado__Pipeline__c FROM copado__User_Story__c';
                List<String> conditions = new List<String>();
                if (filter.pipeline != null) {
                    conditions.add('copado__Pipeline__c = \'' + String.escapeSingleQuotes(filter.pipeline) + '\'');
                }
                if (filter.status != null) {
                    conditions.add('copado__Status__c = \'' + String.escapeSingleQuotes(filter.status) + '\'');
                }
                if (!conditions.isEmpty()) {
                    query += ' WHERE ' + String.join(conditions, ' AND ');
                }
                query += ' ORDER BY LastModifiedDate DESC LIMIT 50';
                for (SObject s : Database.query(query)) {
                    UserStory us = new UserStory();
                    us.Id = (String)s.get('Id');
                    us.Name = (String)s.get('Name');
                    us.copado_Status__c = (String)s.get('copado__Status__c');
                    us.copado_Pipeline__c = (String)s.get('copado__Pipeline__c');
                    stories.add(us);
                }
            } catch (Exception e) {
                System.debug('Error querying stories: ' + e.getMessage());
            }
            results.add(stories);
        }
        return results;
    }

    // ─── Get Job Status ───────────────────────────────────────────────────

    global class JobStatusRequest {
        @InvocableVariable(required=true description='Job Execution ID to check')
        global String jobExecutionId;
    }

    global class JobStatus {
        @InvocableVariable(description='Job Execution ID')
        global String Id;
        @InvocableVariable(description='Current status (In Progress, Completed, Failed, etc.)')
        global String copado_Status__c;
        @InvocableVariable(description='Pipeline stage')
        global String copado_Pipeline_Stage__c;
    }

    @InvocableMethod(label='Get Job Status' description='Checks the execution status of a Copado job by its ID. Returns current status and pipeline stage.')
    global static List<List<JobStatus>> getJobStatus(List<JobStatusRequest> requests) {
        List<List<JobStatus>> results = new List<List<JobStatus>>();
        for (JobStatusRequest req : requests) {
            List<JobStatus> statuses = new List<JobStatus>();
            try {
                String q = 'SELECT Id, copado__Status__c, copado__Pipeline_Stage__c FROM copado__JobExecution__c WHERE Id = \''
                    + String.escapeSingleQuotes(req.jobExecutionId) + '\' LIMIT 1';
                for (SObject s : Database.query(q)) {
                    JobStatus js = new JobStatus();
                    js.Id = (String)s.get('Id');
                    js.copado_Status__c = (String)s.get('copado__Status__c');
                    js.copado_Pipeline_Stage__c = (String)s.get('copado__Pipeline_Stage__c');
                    statuses.add(js);
                }
            } catch (Exception e) {
                System.debug('Error querying job status: ' + e.getMessage());
            }
            results.add(statuses);
        }
        return results;
    }

    // ─── Private Helpers ──────────────────────────────────────────────────

    private static String buildPayload(String templateName, Map<String, Object> data) {
        Map<String, Object> payload = new Map<String, Object>();
        payload.put('templateName', templateName);
        payload.put('runAfterInstantiation', true);
        payload.put('dataJson', JSON.serialize(data));
        return JSON.serialize(new Map<String, Object>{'payload' => payload});
    }

    private static String callActionsApi(String body) {
        HttpRequest req = new HttpRequest();
        req.setEndpoint('callout:CopadoHx_API/json/v1/webhook/mcwebhook/RunJobTemplate');
        req.setMethod('POST');
        req.setHeader('Content-Type', 'application/json');
        req.setTimeout(120000);
        req.setBody(body);

        Http http = new Http();
        HttpResponse res = http.send(req);

        if (res.getStatusCode() >= 400) {
            throw new CopadoHxActionException(
                'Actions API error (' + res.getStatusCode() + '): ' + res.getBody().left(500)
            );
        }
        return res.getBody();
    }

    private static String extractId(String rawJson) {
        try {
            Map<String, Object> m = (Map<String, Object>)JSON.deserializeUntyped(rawJson);
            String id = (String)m.get('Id');
            if (id != null) return id;
            Map<String, Object> data = (Map<String, Object>)m.get('data');
            if (data != null) return (String)data.get('id');
            return rawJson.left(40);
        } catch (Exception e) {
            return rawJson.left(40);
        }
    }

    global class CopadoHxActionException extends Exception {}
}
