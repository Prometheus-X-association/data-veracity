package hu.bme.mit.ftsrg.dva.persistence.repository

import hu.bme.mit.ftsrg.dva.dto.AttestationRequest

interface AttestationRequestRepository : QueueRepository<AttestationRequest, String>