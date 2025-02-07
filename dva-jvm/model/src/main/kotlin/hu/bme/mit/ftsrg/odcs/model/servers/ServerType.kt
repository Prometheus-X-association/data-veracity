package hu.bme.mit.ftsrg.odcs.model.servers

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
enum class ServerType {

  @SerialName("api")
  API,

  @SerialName("athena")
  ATHENA,

  @SerialName("azure")
  AZURE,

  @SerialName("bigquery")
  BIGQUERY,

  @SerialName("clickhouse")
  CLICKHOUSE,

  @SerialName("databricks")
  DATABRICKS,

  @SerialName("denodo")
  DENODO,

  @SerialName("dremio")
  DREMIO,

  @SerialName("duckdb")
  DUCKDB,

  @SerialName("glue")
  GLUE,

  @SerialName("cloudsql")
  CLOUDSQL,

  @SerialName("db2")
  DB2,

  @SerialName("informix")
  INFORMIX,

  @SerialName("kafka")
  KAFKA,

  @SerialName("kinesis")
  KINESIS,

  @SerialName("local")
  LOCAL,

  @SerialName("mysql")
  MYSQL,

  @SerialName("oracle")
  ORACLE,

  @SerialName("postgresql")
  POSTGRESQL,

  @SerialName("postgres")
  POSTGRES,

  @SerialName("presto")
  PRESTO,

  @SerialName("pubsub")
  PUBSUB,

  @SerialName("redshift")
  REDSHIFT,

  @SerialName("s3")
  S3,

  @SerialName("sftp")
  SFTP,

  @SerialName("snowflake")
  SNOWFLAKE,

  @SerialName("sqlserver")
  SQLSERVER,

  @SerialName("synapse")
  SYNAPSE,

  @SerialName("trino")
  TRINO,

  @SerialName("vertica")
  VERTICA,

  @SerialName("custom")
  CUSTOM,
}
