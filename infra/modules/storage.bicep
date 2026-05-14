// Module: Provisions a storage account and private blob container for diagnostics.
param name string
param location string
param tags object
param containerName string = 'foundry-diagnostics'
// Azure Monitor Diagnostic Settings storage archives require shared-key access for writes.
param allowSharedKeyAccess bool = true

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: name
  location: location
  tags: tags
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    allowBlobPublicAccess: false
    minimumTlsVersion: 'TLS1_2'
    allowSharedKeyAccess: allowSharedKeyAccess
  }
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  parent: storageAccount
  name: 'default'
  properties: {}
}

resource container 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  parent: blobService
  name: containerName
  properties: {
    publicAccess: 'None'
  }
}

output id string = storageAccount.id
output name string = storageAccount.name
output containerName string = container.name
output primaryBlobEndpoint string = storageAccount.properties.primaryEndpoints.blob
