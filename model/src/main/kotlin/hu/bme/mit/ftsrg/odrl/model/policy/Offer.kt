package hu.bme.mit.ftsrg.odrl.model.policy

import hu.bme.mit.ftsrg.odrl.model.party.Party

data class Offer(val assigner: Party, val policy: Policy) : IPolicy by policy
