// Module: Diagnostic Settings on the existing Foundry account -> Log Analytics + Storage.
param foundryAccountName string
param diagnosticSettingName string = 'foundry-tpu-est-diag'
param logAnalyticsWorkspaceId string
param storageAccountId string

resource foundry 'Microsoft.CognitiveServices/accounts@2024-10-01' existing = {
  name: foundryAccountName
}

resource diagnosticSetting 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: diagnosticSettingName
  scope: foundry
  properties: {
    workspaceId: logAnalyticsWorkspaceId
    storageAccountId: storageAccountId
    logs: [
      {
        categoryGroup: 'allLogs'
        enabled: true
      }
      {
        categoryGroup: 'audit'
        enabled: true
      }
    ]
    metrics: [
      {
        category: 'AllMetrics'
        enabled: true
      }
    ]
  }
}

output diagnosticSettingId string = diagnosticSetting.id
output diagnosticSettingName string = diagnosticSetting.name
