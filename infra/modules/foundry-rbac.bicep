// Module: Grants Cognitive Services User on the existing Foundry account to a user-assigned MI.
param foundryAccountName string
param miPrincipalId string

resource foundry 'Microsoft.CognitiveServices/accounts@2024-10-01' existing = {
  name: foundryAccountName
}

resource cognitiveServicesUserRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(foundry.id, miPrincipalId, 'CognitiveServicesUser')
  scope: foundry
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'a97b65f3-24c7-4388-baec-2e87135dc908')
    principalId: miPrincipalId
    principalType: 'ServicePrincipal'
  }
}

output roleAssignmentId string = cognitiveServicesUserRoleAssignment.id
output foundryAccountId string = foundry.id
