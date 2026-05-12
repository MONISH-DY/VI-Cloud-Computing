terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }

    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

# Azure Provider Configuration
provider "azurerm" {
  features {}
}

# Resource Group
resource "azurerm_resource_group" "vault_rg" {
  name     = "CloudVault-RG"
  location = "Central India"
}

# Storage Account for Blobs
resource "azurerm_storage_account" "storage" {
  name                     = "cloudvaultstore${random_string.suffix.result}"
  resource_group_name      = azurerm_resource_group.vault_rg.name
  location                 = azurerm_resource_group.vault_rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

# Azure Kubernetes Service (AKS)
resource "azurerm_kubernetes_cluster" "aks" {
  name                = "cloudvault-aks"
  location            = azurerm_resource_group.vault_rg.location
  resource_group_name = azurerm_resource_group.vault_rg.name
  dns_prefix          = "cloudvault"

  default_node_pool {
    name       = "default"
    node_count = 1
    vm_size    = "Standard_DS2_v2"
  }

  identity {
    type = "SystemAssigned"
  }
}

# Application Insights
resource "azurerm_application_insights" "appinsights" {
  name                = "cloudvault-insights"
  location            = azurerm_resource_group.vault_rg.location
  resource_group_name = azurerm_resource_group.vault_rg.name
  application_type    = "web"
}

resource "random_string" "suffix" {
  length  = 6
  special = false
  upper   = false
}

output "storage_connection_string" {
  value     = azurerm_storage_account.storage.primary_connection_string
  sensitive = true
}
