package hu.bme.mit.ftsrg.vc.model

import java.time.ZonedDateTime

interface IVerifiableCredential {
  val id: String
  val type: String
  val validFrom: ZonedDateTime
  val subject: CredentialSubject
  val issuer: String
}