package hu.bme.mit.ftsrg.odrl.model.policy

data class Set(val policy: Policy) : IPolicy by policy
