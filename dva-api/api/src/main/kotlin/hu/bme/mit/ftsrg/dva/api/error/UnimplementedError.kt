package hu.bme.mit.ftsrg.dva.api.error

object UnimplementedError : Exception("This feature has not been implemented yet") {
    private fun readResolve(): Any = UnimplementedError
}