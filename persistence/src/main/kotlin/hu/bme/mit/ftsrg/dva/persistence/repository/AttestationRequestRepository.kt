package hu.bme.mit.ftsrg.dva.persistence.repository

import hu.bme.mit.ftsrg.dva.dto.aov.AttestationRequestDTO

interface AttestationRequestRepository : QueueRepository<AttestationRequestDTO, String>