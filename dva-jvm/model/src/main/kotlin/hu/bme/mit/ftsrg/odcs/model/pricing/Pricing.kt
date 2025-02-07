package hu.bme.mit.ftsrg.odcs.model.pricing

import kotlinx.serialization.Serializable

@Serializable
data class Pricing(
  val priceAmount: Double?,
  val priceCurrency: String?,
  val priceUnit: String?,
)
