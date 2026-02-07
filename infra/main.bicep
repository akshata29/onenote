param location string = resourceGroup().location
param namePrefix string
param tenantId string
param backendImage string
param mcpImage string
param openAiName string
param searchSku string = 'standard'
param searchPartitionCount int = 1
param searchReplicaCount int = 1

var storageName = toLower(replace('${namePrefix}stor', '-', ''))
var kvName = '${namePrefix}-kv'
var laName = '${namePrefix}-logs'
var appInsightsName = '${namePrefix}-appi'
var caeName = '${namePrefix}-cae'
var backendAppName = '${namePrefix}-api'
var mcpAppName = '${namePrefix}-mcp'
var searchName = '${namePrefix}-search'

resource kv 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: kvName
  location: location
  properties: {
    tenantId: tenantId
    sku: { family: 'A'; name: 'standard' }
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 90
    publicNetworkAccess: 'Enabled'
  }
}

resource storage 'Microsoft.Storage/storageAccounts@2023-04-01' = {
  name: storageName
  location: location
  kind: 'StorageV2'
  sku: { name: 'Standard_LRS' }
  properties: {
    allowBlobPublicAccess: false
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
  }
}

resource la 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: laName
  location: location
  sku: { name: 'PerGB2018' }
}

resource appi 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: la.id
  }
}

resource search 'Microsoft.Search/searchServices@2023-11-01' = {
  name: searchName
  location: location
  sku: { name: searchSku }
  properties: {
    replicaCount: searchReplicaCount
    partitionCount: searchPartitionCount
    publicNetworkAccess: 'enabled'
    disableLocalAuth: false
    authenticationConfiguration: { aadAuthFailureMode: 'http401WithBearerChallenge' }
  }
}

resource cae 'Microsoft.App/managedEnvironments@2024-02-02-preview' = {
  name: caeName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: la.properties.customerId
        sharedKey: listKeys(la.id, la.apiVersion).primarySharedKey
      }
    }
  }
}

resource backend 'Microsoft.App/containerApps@2024-02-02-preview' = {
  name: backendAppName
  location: location
  properties: {
    managedEnvironmentId: cae.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 8000
        transport: 'auto'
      }
      secrets: [
        { name: 'client-secret'; value: '' }
        { name: 'search-api-key'; value: '' }
        { name: 'openai-api-key'; value: '' }
      ]
      registries: []
    }
    template: {
      containers: [
        {
          name: 'api'
          image: backendImage
          env: [
            { name: 'APP_INSIGHTS_CONNECTION_STRING'; value: appi.properties.ConnectionString }
            { name: 'KEY_VAULT_URL'; value: kv.properties.vaultUri }
            { name: 'SEARCH_ENDPOINT'; value: 'https://${searchName}.search.windows.net' }
          ]
        }
      ]
      scale: { minReplicas: 1; maxReplicas: 3 }
    }
  }
}

resource mcp 'Microsoft.App/containerApps@2024-02-02-preview' = {
  name: mcpAppName
  location: location
  properties: {
    managedEnvironmentId: cae.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 3000
        transport: 'auto'
      }
    }
    template: {
      containers: [
        {
          name: 'mcp'
          image: mcpImage
          env: [
            { name: 'GRAPH_CLIENT_ID'; value: '' }
            { name: 'GRAPH_TENANT_ID'; value: tenantId }
          ]
        }
      ]
      scale: { minReplicas: 1; maxReplicas: 2 }
    }
  }
}

output keyVaultUri string = kv.properties.vaultUri
output storageAccount string = storage.name
output searchEndpoint string = 'https://${searchName}.search.windows.net'
output appInsightsConnectionString string = appi.properties.ConnectionString
