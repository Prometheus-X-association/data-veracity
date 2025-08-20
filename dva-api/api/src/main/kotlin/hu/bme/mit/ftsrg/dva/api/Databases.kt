package hu.bme.mit.ftsrg.dva.api

import hu.bme.mit.ftsrg.dva.api.db.DVARequestLogTable
import hu.bme.mit.ftsrg.dva.api.db.DVAVerificationRequestLogTable
import hu.bme.mit.ftsrg.dva.api.db.TemplatesTable
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
        create(TemplatesTable, DVARequestLogTable, DVAVerificationRequestLogTable)
    }
}