output "resource_group_name" {
  value = azurerm_resource_group.vault_rg.name
}

output "storage_account_name" {
  value = azurerm_storage_account.storage.name
}

output "application_insights_name" {
  value = azurerm_application_insights.appinsights.name
}

output "aks_cluster_name" {
  value = azurerm_kubernetes_cluster.aks.name
}

output "storage_connection_string" {
  value     = azurerm_storage_account.storage.primary_connection_string
  sensitive = true
}