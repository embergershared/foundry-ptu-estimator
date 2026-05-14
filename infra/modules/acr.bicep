// Module: Provisions an Azure Container Registry with optional AcrPull RBAC.
param name string
param location string
param tags object
@allowed([
  'Basic'
  'Standard'
  'Premium'
])
param sku string = 'Basic'
param acrPullPrincipalId string = ''

resource acr 'Microsoft.ContainerRegistry/registries@2023-11-01-preview' = {
  name: name
  location: location
  tags: tags
  sku: {
    name: sku
  }
  properties: {
    adminUserEnabled: false
  }
}

resource acrPullRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (acrPullPrincipalId != '') {
  name: guid(acr.id, acrPullPrincipalId, 'AcrPull')
  scope: acr
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d')
    principalId: acrPullPrincipalId
    principalType: 'ServicePrincipal'
  }
}

output id string = acr.id
output name string = acr.name
output loginServer string = acr.properties.loginServer
