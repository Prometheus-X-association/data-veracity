package hu.bme.mit.ftsrg.odrl.model.constraint

enum class LeftOperand {
  ABSOLUTE_POSITION,
  ABSOLUTE_SIZE,
  ABSOLUTE_SPATIAL_POSITION,
  ABSOLUTE_TEMPORAL_POSITION,
  COUNT,
  DATE_TIME,
  DELAY_PERIOD,
  DELIVERY_CHANNEL,
  ELAPSED_TIME,
  EVENT,
  FILE_FORMAT,
  INDUSTRY,
  LANGUAGE,
  MEDIA,
  METERED_TIME,
  PAY_AMOUNT,
  PERCENTAGE,
  PRODUCT,
  PURPOSE,
  RECIPIENT,
  RELATIVE_POSITION,
  RELATIVE_SIZE,
  RELATIVE_SPATIAL_POSITION,
  RELATIVE_TEMPORAL_POSITION,
  RESOLUTION,
  SPATIAL,
  SPATIAL_COORDINATES,
  SYSTEM_DEVICE,
  TIME_INTERVAL,
  UNIT_OF_COUNT,
  VERSION,
  VIRTUAL_LOCATION,

  @Deprecated(
    "The device and systemDevice identifiers have been deprecated by the standard in favour of systemDevice",
    ReplaceWith("LeftOperand.SYSTEM_DEVICE")
  )
  DEVICE,

  @Deprecated(
    "The device and systemDevice identifiers have been deprecated by the standard in favour of systemDevice",
    ReplaceWith("LeftOperand.SYSTEM_DEVICE")
  )
  SYSTEM,
}