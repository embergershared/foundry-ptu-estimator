targetScope = 'subscription'

param environmentName string
param location string = 'swedencentral'
param resourceGroupName string = 'rg-${environmentName}'
param foundryResourceGroupName string
param foundryAccountName string
param foundryEndpoint string
param modelDeployment string = 'gpt-5.4'
param tags object = {
  'azd-env-name': environmentName
  app: 'foundry-tpu-est'
}

var resourceToken = uniqueString(subscription().id, environmentName, location)
var logAnalyticsWorkspaceName = 'log-${environmentName}'
var storageAccountName = 'st${take(replace(replace(resourceToken,'-',''),'_',''),20)}'
var acrName = 'cr${take(replace(replace(resourceToken,'-',''),'_',''),48)}'
var managedIdentityName = 'id-${environmentName}'
var containerAppsEnvironmentName = 'cae-${environmentName}'
var containerAppsJobName = 'caj-${environmentName}'
var workerImageName = 'worker'

resource appResourceGroup 'Microsoft.Resources/resourceGroups@2024-11-01' = {
  name: resourceGroupName
  location: location
  tags: tags
}

module logAnalytics 'modules/log-analytics.bicep' = {
  name: 'logAnalytics'
  scope: appResourceGroup
  params: {
    name: logAnalyticsWorkspaceName
    location: location
    tags: tags
  }
}

module storage 'modules/storage.bicep' = {
  name: 'storage'
  scope: appResourceGroup
  params: {
    name: storageAccountName
    location: location
    tags: tags
  }
}

module managedIdentity 'modules/managed-identity.bicep' = {
  name: 'managedIdentity'
  scope: appResourceGroup
  params: {
    name: managedIdentityName
    location: location
    tags: tags
  }
}

module acr 'modules/acr.bicep' = {
  name: 'acr'
  scope: appResourceGroup
  params: {
    name: acrName
    location: location
    tags: tags
    acrPullPrincipalId: managedIdentity.outputs.principalId
  }
}

module acaEnvironment 'modules/aca-environment.bicep' = {
  name: 'acaEnvironment'
  scope: appResourceGroup
  params: {
    name: containerAppsEnvironmentName
    location: location
    tags: tags
    logAnalyticsWorkspaceCustomerId: logAnalytics.outputs.customerId
    logAnalyticsWorkspaceResourceId: logAnalytics.outputs.id
  }
}

module acaJob 'modules/aca-job.bicep' = {
  name: 'acaJob'
  scope: appResourceGroup
  params: {
    name: containerAppsJobName
    location: location
    tags: tags
    containerAppsEnvironmentId: acaEnvironment.outputs.id
    userAssignedIdentityId: managedIdentity.outputs.id
    userAssignedIdentityClientId: managedIdentity.outputs.clientId
    acrLoginServer: acr.outputs.loginServer
    imageName: workerImageName
    foundryEndpoint: foundryEndpoint
    modelDeployment: modelDeployment
    minTokens: 30000
    maxTokens: 700000
    maxJitterSeconds: 179
    authRetrySeconds: 60
    logLevel: 'INFO'
  }
}

module foundryRbac 'modules/foundry-rbac.bicep' = {
  name: 'foundryRbac'
  scope: resourceGroup(foundryResourceGroupName)
  params: {
    foundryAccountName: foundryAccountName
    miPrincipalId: managedIdentity.outputs.principalId
  }
}

module foundryDiagnostics 'modules/foundry-diagnostics.bicep' = {
  name: 'foundryDiagnostics'
  scope: resourceGroup(foundryResourceGroupName)
  params: {
    foundryAccountName: foundryAccountName
    logAnalyticsWorkspaceId: logAnalytics.outputs.id
    storageAccountId: storage.outputs.id
  }
  dependsOn: [
    foundryRbac
  ]
}

output AZURE_RESOURCE_GROUP string = appResourceGroup.name
output AZURE_LOCATION string = location
output AZURE_CONTAINER_REGISTRY_NAME string = acr.outputs.name
output AZURE_CONTAINER_REGISTRY_ENDPOINT string = acr.outputs.loginServer
output AZURE_CONTAINER_APPS_ENVIRONMENT_ID string = acaEnvironment.outputs.id
output AZURE_CONTAINER_APP_JOB_NAME string = acaJob.outputs.name
output AZURE_CLIENT_ID string = managedIdentity.outputs.clientId
output LOG_ANALYTICS_WORKSPACE_NAME string = logAnalytics.outputs.name
output STORAGE_ACCOUNT_NAME string = storage.outputs.name
output FOUNDRY_ENDPOINT string = foundryEndpoint
output MODEL_DEPLOYMENT string = modelDeployment
