targetScope = 'subscription'

@minLength(2)
@maxLength(12)
@description('Short name used to derive all resource names')
param aiServicesName string = 'rt2demo'

@description('Azure region — gpt-realtime-2 supports GlobalStandard (eastus2 recommended)')
param location string = 'eastus2'

@description('gpt-realtime-2 deployment capacity (RPM). Default quota = 10.')
param capacity int = 10

param tags object = {}

var uniqueSuffix      = substring(uniqueString(subscription().id, aiServicesName), 0, 4)
var resourceGroupName = 'rg-${aiServicesName}-01'
var accountName       = 'ais${aiServicesName}${uniqueSuffix}'
var projectName       = 'proj-${aiServicesName}-${uniqueSuffix}'

resource rg 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: resourceGroupName
  location: location
  tags: tags
}

module deps 'modules/dependent_resources.bicep' = {
  name: 'dependent-resources'
  scope: rg
  params: {
    aiServicesName: accountName
    location: location
    capacity: capacity
  }
}

module project 'modules/foundry_project.bicep' = {
  name: 'foundry-project'
  scope: rg
  params: {
    aiServicesName: accountName
    projectName: projectName
    location: location
  }
  dependsOn: [deps]
}

output AZURE_OPENAI_ENDPOINT   string = deps.outputs.aiServicesTarget
output AZURE_OPENAI_DEPLOYMENT string = deps.outputs.deploymentName
