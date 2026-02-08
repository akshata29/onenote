param location string = resourceGroup().location
param namePrefix string
param tenantId string
param backendImage string
param mcpImage string
param searchSku string = 'standard'
param searchPartitionCount int = 1
param searchReplicaCount int = 1

var laName = '${namePrefix}-logs'
var appInsightsName = '${namePrefix}-appi'
var caeName = '${namePrefix}-cae'
var backendAppName = '${namePrefix}-api'
var mcpAppName = '${namePrefix}-mcp'
var searchName = '${namePrefix}-search'
var docIntelName = '${namePrefix}-docintel'

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

resource documentIntelligence 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: docIntelName
  location: location
  kind: 'FormRecognizer'
  sku: { 
    name: 'S0'
  }
  properties: {
    publicNetworkAccess: 'Enabled'
    customSubDomainName: docIntelName
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
            { name: 'SEARCH__SERVICE_NAME'; value: searchName }
            { name: 'DOCINT__ENDPOINT'; value: documentIntelligence.properties.endpoint }
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

output searchServiceName string = searchName
output searchEndpoint string = 'https://${searchName}.search.windows.net'
output documentIntelligenceEndpoint string = documentIntelligence.properties.endpoint
output appInsightsConnectionString string = appi.properties.ConnectionString
