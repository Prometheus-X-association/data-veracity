package hu.bme.mit.ftsrg.dva.persistence.error

class EntityExistsException(message: String? = null, cause: Throwable? = null) : IllegalStateException(message, cause) {
  constructor(cause: Throwable) : this(null, cause)
}