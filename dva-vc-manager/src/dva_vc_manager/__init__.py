"""
DVA Verifiable Credential Manager.

A decentralized internal DVA service, hosted at each participant.

Owns:

* The Ed25519 signing key for that participant (loaded from a file or generated
  on first boot)
* The ``did:key`` whitelist of trusted attesters (consulted during verification)
* The W3C VC 2.0 JSON-LD payload shape used for the Attestation of
  Veracity (AoV)
"""

__version__ = "0.1.0"
