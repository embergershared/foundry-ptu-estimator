// Module: Provisions a cron-scheduled Azure Container Apps Job.
param name string
param location string
param tags object
param containerAppsEnvironmentId string
param userAssignedIdentityId string
param userAssignedIdentityClientId string
param acrLoginServer string
param imageName string
param imageTag string = 'latest'
param foundryEndpoint string
param modelDeployment string
@minValue(1)
param minTokens int = 30000
@minValue(1)
param maxTokens int = 700000
@minValue(0)
@maxValue(599)
param maxJitterSeconds int = 179
@minValue(0)
param authRetrySeconds int = 60
param apiVersion string = '2025-05-01'
@allowed([
  'DEBUG'
  'INFO'
  'WARNING'
  'ERROR'
])
param logLevel string = 'INFO'
param cpu string = '1.0'
param memory string = '2.0Gi'
param cronExpression string = '*/3 * * * *'
@minValue(1)
param replicaTimeoutSeconds int = 600
@minValue(0)
param replicaRetryLimit int = 0
@minValue(1)
param parallelism int = 1

resource containerAppJob 'Microsoft.App/jobs@2024-03-01' = {
  name: name
  location: location
  tags: tags
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${userAssignedIdentityId}': {}
    }
  }
  properties: {
    environmentId: containerAppsEnvironmentId
    configuration: {
      triggerType: 'Schedule'
      replicaTimeout: replicaTimeoutSeconds
      replicaRetryLimit: replicaRetryLimit
      scheduleTriggerConfig: {
        cronExpression: cronExpression
        parallelism: parallelism
        replicaCompletionCount: parallelism
      }
      registries: [
        {
          server: acrLoginServer
          identity: userAssignedIdentityId
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'tpu-est'
          image: '${acrLoginServer}/${imageName}:${imageTag}'
          resources: {
            cpu: json(cpu)
            memory: memory
          }
          env: [
            {
              name: 'FOUNDRY_ENDPOINT'
              value: foundryEndpoint
            }
            {
              name: 'MODEL_DEPLOYMENT'
              value: modelDeployment
            }
            {
              name: 'AZURE_CLIENT_ID'
              value: userAssignedIdentityClientId
            }
            {
              name: 'MIN_TOKENS'
              value: string(minTokens)
            }
            {
              name: 'MAX_TOKENS'
              value: string(maxTokens)
            }
            {
              name: 'MAX_JITTER_SECONDS'
              value: string(maxJitterSeconds)
            }
            {
              name: 'AUTH_RETRY_SECONDS'
              value: string(authRetrySeconds)
            }
            {
              name: 'API_VERSION'
              value: apiVersion
            }
            {
              name: 'LOG_LEVEL'
              value: logLevel
            }
          ]
        }
      ]
    }
  }
}

output id string = containerAppJob.id
output name string = containerAppJob.name
