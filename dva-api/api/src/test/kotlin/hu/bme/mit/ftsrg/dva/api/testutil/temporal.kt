package hu.bme.mit.ftsrg.dva.api.testutil

import kotlin.time.Clock
import kotlin.time.ExperimentalTime
import kotlin.time.Instant

@OptIn(ExperimentalTime::class)
object FixedClock : Clock {
    override fun now(): Instant = Instant.parse("2025-01-01T12:00:00Z")
}