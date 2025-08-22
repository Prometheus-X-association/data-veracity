package hu.bme.mit.ftsrg.dva.api.db

import io.ktor.server.application.*
import org.jetbrains.exposed.v1.jdbc.Database
import org.jetbrains.exposed.v1.jdbc.SchemaUtils.create
import org.jetbrains.exposed.v1.jdbc.transactions.transaction

fun Application.configureDatabases() {
    Database.connect(
        "jdbc:postgresql://localhost:5432/dva",
        user = "postgres",
        password = "pw"
    )

    transaction {
        create(TemplatesTable, RequestLogsTable, VerifRequestLogsTable, VLAsTable)
    }
}