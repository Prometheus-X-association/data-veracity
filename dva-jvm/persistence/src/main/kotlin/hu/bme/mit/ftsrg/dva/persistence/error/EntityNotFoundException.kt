package hu.bme.mit.ftsrg.dva.persistence.error

class EntityNotFoundException(message: String? = null, cause: Throwable? = null) :
  IllegalStateException(message, cause) {
  constructor(cause: Throwable) : this(null, cause)
}