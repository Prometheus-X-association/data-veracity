package hu.bme.mit.ftsrg.dva.api

import io.ktor.server.application.*
import org.jetbrains.exposed.v1.jdbc.Database

fun Application.configureDatabases() {
    Database.connect(
        "jdbc:postgresql://localhost:5432/dva",
        user = "postgres",
        password = "pw"
    )
}