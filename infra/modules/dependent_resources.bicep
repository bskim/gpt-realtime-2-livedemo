@description('AI Services account name')
param aiServicesName string

@description('Location for AI Services')
param location string

@description('gpt-realtime-2 deployment capacity (RPM). Default quota = 10.')
param capacity int = 10

resource aiServices 'Microsoft.CognitiveServices/accounts@2026-03-01' = {
  name: aiServicesName
  location: location
  kind: 'AIServices'
  sku: { name: 'S0' }
  identity: { type: 'SystemAssigned' }
  properties: {
    customSubDomainName: aiServicesName
    publicNetworkAccess: 'Enabled'
    disableLocalAuth: true
    allowProjectManagement: true
  }
}

resource realtimeDeployment 'Microsoft.CognitiveServices/accounts/deployments@2026-03-01' = {
  parent: aiServices
  name: 'gpt-realtime-2'
  sku: {
    name: 'GlobalStandard'
    capacity: capacity
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'gpt-realtime-2'
      version: '2026-05-06'
    }
  }
}

output aiServicesId     string = aiServices.id
output aiServicesName   string = aiServices.name
output aiServicesTarget string = aiServices.properties.endpoint
output deploymentName   string = realtimeDeployment.name
