@description('Parent AI Services account name')
param aiServicesName string

@description('Foundry project name')
param projectName string

@description('Foundry project friendly description')
param projectDescription string = 'GPT-Realtime-2 Demo Project'

@description('Location')
param location string

// Reference the existing AI Services account (Foundry account)
resource aiServices 'Microsoft.CognitiveServices/accounts@2026-03-01' existing = {
  name: aiServicesName
}

// Azure AI Foundry project — replaces the old MachineLearningServices Hub+Project model
resource foundryProject 'Microsoft.CognitiveServices/accounts/projects@2026-03-01' = {
  parent: aiServices
  name: projectName
  location: location
  kind: 'AIServices'
  identity: { type: 'SystemAssigned' }
  properties: {
    description: projectDescription
  }
}

output projectId   string = foundryProject.id
output projectName string = foundryProject.name
