variable "project" {
  description = "ID del proyecto de GCP"
  default     = "pv-energy-493918"
  type        = string
}

variable "region" {
  description = "Región de los recursos"
  default     = "us-central1"
  type        = string
}

variable "location" {
  description = "Ubicación geográfica general para BigQuery y Cloud Storage"
  default     = "US"
  type        = string
}

variable "bq_dataset_name" {
  description = "Nombre del dataset en BigQuery"
  default     = "pv_analytics_dataset"
  type        = string
}

variable "gcs_bucket_name" {
  description = "Nombre del bucket en Cloud Storage"
  default     = "data-lake-pv-energy-493918"
  type        = string
}
