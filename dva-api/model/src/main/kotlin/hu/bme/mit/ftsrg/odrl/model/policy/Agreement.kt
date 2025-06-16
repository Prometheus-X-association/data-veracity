package hu.bme.mit.ftsrg.odrl.model.policy

import hu.bme.mit.ftsrg.odrl.model.party.Party

data class Agreement(val assigner: Party, val assignee: Party, val policy: Policy) : IPolicy by policy
