# Data veracity assurance BB – Design Document

The Data Veracity Assurance building block (_DVA_ from now on) allows data exchange participants to agree on and later prove/verify quality requirements or properties of the exchanged data.

For example, if a data producer (abbreviated _P_ from now on) provides simple sensor data to a data consumer (_C_ from now on), DVA can facilitate _P_ to prove (and _C_ to verify) that the provided data is credible (eg, temperature values are within a certain range).

DVA requires a **veracity level agreement (VLA)** between the exchange participants.
The agreement is made for a specific data exchange unit, as described by the contract.
The VLA defines a number of **veracity objectives** that each describe a **data quality aspect** (eg, _completeness_ or _accuracy_) and an **evaluation scheme** (eg, value is within a numerical range).
When the data exchange occurs, in the simplest model, P attaches a proof (or at least an attestation) regarding the exchanged data’s quality that C trusts or can verify.

<!-- Hacking a Mermaid flowchart for a knowledge graph for now -->

```mermaid
%%{init: {'theme':'neutral'}}%%

---
title: High-Level Data Veracity Concepts (Knowledge Graph / Metamodel)
---

graph TD
  xchg(["Data\n Exchange"]):::External

  va(["Veracity\n Assurance"]):::Assurance
  aov(["Attestation\n of Veracity"]):::Assurance
  pov(["Proof\n of Veracity"]):::Assurance
  voe(["Veracity Objective Evaluation"]):::Assurance
  eval(["Evaluation"]):::Assurance

  vla(["Veracity\n Level\n Agreement"]):::Agreement
  vo(["Veracity\n Objective"]):::Agreement
  qa(["Quality\n Aspect"]):::Agreement
  es(["Evaluation\n Scheme"]):::Agreement
  crit(["Criterion\n Type"]):::Agreement
  method(["Evaluation\n Method"]):::Agreement

  syntax(["Syntax\n (ISO 8000)"]):::Aspect
  timeliness(["Timeliness\n (ISO 25000)"]):::Aspect
  accuracy(["Accuracy\n (ISO 25000)"]):::Aspect
  completeness(["Completeness\n (ISO 25000)"]):::Aspect
  consistency(["Consistency\n (ISO 25000)"]):::Aspect

  validinvalid(["Valid/\n Invalid"]):::Agreement
  inrange(["In\n Range"]):::Agreement
  greaterless(["Greater Than\n Less Than"]):::Agreement

  vla-- targets exchange -->xchg
  vla-- has objective -->vo
  vo-- targets aspect -->qa
  vo-- can be evaluated using -->es
  es-- has type -->crit
  es-- has method -->method

  syntax & timeliness & accuracy & completeness & consistency-- is a -->qa
  validinvalid & inrange & greaterless-- is a -->crit

  va-- for agreement -->vla
  aov & pov-- is a -->va

  va-- has evaluation -->voe
  voe-- targets objective -->vo
  voe-- has evaluation -->eval

  classDef Agreement fill:#fcdc00,stroke:#000,color:#000
  classDef Aspect fill:#fb4b00,stroke:#000,color:#000
  classDef External fill:#73d8ff,color:#000
  classDef Assurance fill:#a4dd00,stroke:#000,color:#000
  linkStyle default stroke-width:4px
```

```mermaid
%%{init: {'theme':'neutral'}}%%

---
title: Data Veracity Concepts Example (xAPI Learning Traces)
---

graph LR
  xchg(["xAPI Learning\n Traces Exchange"]):::External

  aov(["Attestation\n of Veracity"]):::Assurance
  voe_syn(["Syntax\n Evaluation"]):::Assurance
  voe_rec(["Recency\n Evaluation"]):::Assurance
  eval_syn(["Valid"]):::Assurance
  eval_rec(["3 Days\n Old"]):::Assurance

  vla(["xAPI Learning Trace\n Veracity Level Agreement"]):::Agreement
  vo_syn(["Valid\n Syntax"]):::Agreement
  vo_rec(["Recency"]):::Agreement
  qa_syn(["Syntax"]):::Aspect
  qa_rec(["Timeliness"]):::Aspect
  es_syn(["Syntax\n Checking"]):::Agreement
  es_rec(["Timeliness\n Checking"]):::Agreement
  crit_syn(["Valid/\n Invalid"]):::Agreement
  crit_rec(["Greater Than\nLess Than"]):::Agreement
  method_syn(["Syntax\n Checker"]):::Agreement
  method_rec(["Value\n Comparison"]):::Agreement

  vla-- targets exchange -->xchg

  vla-- has objective -->vo_syn & vo_rec
  
  vo_syn-- targets aspect -->qa_syn
  vo_rec-- targets aspect -->qa_rec
  vo_syn-- can be evaluated using -->es_syn
  vo_rec-- can be evaluated using -->es_rec

  es_syn-- has type -->crit_syn
  es_rec-- has type -->crit_rec
  es_syn-- has method -->method_syn
  es_rec-- has method -->method_rec

  aov-- for agreement -->vla

  aov-- has evaluation -->voe_syn & voe_rec
  voe_syn-- has evaluation -->eval_syn
  voe_rec-- has evaluation -->eval_rec
  voe_syn-- targets objective --->vo_syn
  voe_rec-- targets objective --->vo_rec

  classDef Agreement fill:#fcdc00,stroke:#000,color:#000
  classDef Aspect fill:#fb4b00,stroke:#000,color:#000
  classDef External fill:#73d8ff,color:#000
  classDef Assurance fill:#a4dd00,stroke:#000,color:#000
  linkStyle default stroke-width:4px
```


## Technical Usage Scenarios & Features

With DVA, data exchange participants can be assured that the data fulfils predefined quality requirements.

### Features/Main Functionalities

Key functionalities:
1. Manage data veracity level agreements (VLAs)
2. Provide means to…
   * attest to
   * prove
   * verify
   the veracity of exchanged data
3. Log veracity verification results

Additional functionalities:
* Potentially enable proving/verifying data properties that are related to further _sensitive_ (eg, due to GDPR) data _without disclosing the sensitive data_

### Technical Usage Scenarios

#### Management of Veracity Level Agreements (VLAs)

VLAs describe exactly what data quality P ‘promises’ and/or C expects.
The format and exact contents of VLAs is further detailed later in this document.

It is among the primary functionalities of DVA to facilitate
* _striking_ VLAs (which is possibly also related to the _Contract_ module)
* _querying_ VLAs for a given data exchange
* _changing_ the terms of VLAs (if this functionality is desired)
* _revoking_ VLAs (if this functionality is desired)

DVA of course also provides the means for P to prove (or attest) and C to verify that the exchanged data fulfils the requirements set by the VLA; see below.

#### Proving, Attestation, and Verification of Veracity

There are chiefly two ways P can offer veracity assurance regarding the exchanged data:
1. By presenting a **Proof of Veracity (PoV)** to C (by sending it together with the data itself)
2. By sharing an **Attestation of Veracity (AoV)**

The latter is obviously the ‘weaker’ option, but depending on the use case, it may be enough, or _proving_ adherence to the VLA may not be possible.

A PoV is something that C can reliably _verify._
PoVs should not be possible to generate for data that does not fulfil the VLA.
<!-- TODO a simple example of a PoV? -->

AoVs are simpler because they are non-verifiable (at least not in the sense as PoVs).
Attestations rely on trust – for example, a trusted third party may give their attestation that the data is indeed in line with the VLA requirements.
It is C’s trust in the third party that assures them of the veracity of the data, not actual proof.
An even ‘weaker’ but still noteworthy option is when P attests to the veracity of the data themselves.
At the very least, they _claim_ that the data is in line with the VLA and can be later held to their claim if C discovers otherwise.

Finally, there may not even be a proof or attestation, merely a direct check of the data’s veracity by C.

DVA defines what proofs and attestations are (see later in this document) and provides means to generate PoVs, AoVs, and to verify veracity.

#### Logging of Results

DVA also keeps track of veracity verification results for traceability purposes.


## Requirements

* **`[BB_08__01]`** DVA MUST define schemata for VLAs
* **`[BB_08__02]`** DVA MUST support striking VLAs (through the Catalogue?)
* **`[BB_08__03]`** DVA MUST provide multiple veracity assurance methods
* **`[BB_08__04]`** DVA MUST support veracity attestation (ie, either P or a third party attests that veracity requirements are met)
* **`[BB_08__05]`** DVA SHOULD support veracity self-attestation
* **`[BB_08__06]`** DVA SHOULD support third-party veracity attestation
* **`[BB_08__07]`** DVA SHOULD support provider-proven veracity
* **`[BB_08__08]`** DVA SHOULD support consumer-verified veracity
* **`[BB_08__09]`** DVA SHOULD interface with the Contract service
* **`[BB_08__10]`** DVA SHOULD interface with the Dataspace Connector
* **`[BB_08__11]`** DVA MUST log verification results

```mermaid
---
title: DVA Requirements
---

requirementDiagram
  requirement BB_08__01 {
    id: BB_08__01
    text: "DVA MUST define schemata for VLAs"
    risk: medium
    verifymethod: demonstration
  }
  functionalRequirement BB_08__02 {
    id: BB_08__02
    text: "DVA MUST support striking VLAs"
    risk: medium
    verifymethod: test
  }
  functionalRequirement BB_08__03 {
    id: BB_08__03
    text: "DVA MUST provide multiple veracity assurance methods"
    risk: low
    verifymethod: demonstration
  }
  functionalRequirement BB_08__04 {
    id: BB_08__04
    text: "DVA MUST support veracity attestation"
    risk: low
    verifymethod: demonstration
  }
  functionalRequirement BB_08__05 {
    id: BB_08__05
    text: "DVA SHOULD support veracity self-attestation"
    risk: low
    verifymethod: demonstration
  }
  functionalRequirement BB_08__06 {
    id: BB_08__06
    text: "DVA SHOULD support third-party veracity attestation"
    risk: low
    verifymethod: demonstration
  }
  functionalRequirement BB_08__07 {
    id: BB_08__07
    text: "DVA SHOULD support provider-proven veracity"
    risk: medium
    verifymethod: demonstration
  }
  functionalRequirement BB_08__08 {
    id: BB_08__08
    text: "DVA SHOULD support consumer-verified veracity"
    risk: medium
    verifymethod: demonstration
  }
  interfaceRequirement BB_08__09 {
    id: BB_08__09
    text: "DVA SHOULD interface with the Contract service"
    risk: low
    verifymethod: test
  }
  interfaceRequirement BB_08__10 {
    id: BB_08__10
    text: "DVA SHOULD interface with the Dataspace Connector"
    risk: medium
    verifymethod: test
  }
  functionalRequirement BB_08__11 {
    id: BB_08__11
    text: "DVA MUST log verification result"
    risk: medium
    verifymethod: test
  }

  BB_08__04 - refines -> BB_08__03
  BB_08__05 - refines -> BB_08__04
  BB_08__06 - refines -> BB_08__04
  BB_08__07 - refines -> BB_08__03
  BB_08__08 - refines -> BB_08__03
```


## Integrations

### Direct Integrations with Other BBs

_No direct integrations identified as of yet._


### Integrations via Connector

* DVA will likely have to directly integrate with the **Dataspace Connector** itself to extend data exchange flows with veracity assurance steps
* As VLAs are similar to contracts (or will become part of the contracts), DVA will likely have interactions with the **Contract** component
* Potential integrations with **Consent** as well (?)
* Most likely, DVA will integrate closely with the **Data Value Chain Tracker** BB
  * The _value_ is strongly related to the quality of the data assured by DVA


## Relevant Standards

### Data Format Standards

* VLAs will likely be encoded in [YAML](https://yaml.org/).
* In all likelihood, DVA will parse and/or serialize into [JSON](https://www.json.org/) or [JSON-LD](https://json-ld.org/) files for interoperability.
* For configuration, DVA will use [TOML](https://toml.io/en/).

### Other Standards

There are ISO standards that define data-quality-related concepts:
* [ISO 8000-61:2016](https://www.iso.org/standard/63086.html) – Data Quality – Part 61: Data quality management: Process reference model
* [ISO/IEC 25000:2014](https://www.iso.org/standard/64764.html) – Systems and software engineering – Systems and software Quality Requirements and Evaluation (SQuaRE)

Other possibly relevant standards and specifications:
* [Data Contracts](https://datacontract.com/), which are very similar to VLAs, have a [standard](https://github.com/bitol-io/open-data-contract-standard)

### Mapping to Data Space Reference Architecture Models

**DSSC:** see the [Value-Added Services](https://dssc.eu/space/BVE/357076468/Value-Added+Services) building block.

**IDS RAM:** see [4.3.6 Data Quality](https://docs.internationaldataspaces.org/ids-knowledgebase/v/ids-ram-4/perspectives-of-the-reference-architecture-model/4_perspectives/4_3_governance_perspective/4_3_7_data_quality) in the Governance Perspective.


## Input / Output Data

### Data Veracity Level Agreements (VLAs)

Initial mockup VLAs based on [data contracts](https://github.com/bitol-io/open-data-contract-standard):

```yaml
---
id: urn:vla:example:vrtraces
meta:
  title: VR Learning Traces VLA Example
  version: 0.1.0
  description: |
    A simple Veracity Level Agreement (VLA) example based on the
    VR Learning Traces building block.
  exchange: cdef77c9-4016-45bb-868d-6f014e17ed2d


models:
  trace:
    description: A VR learning trace
    type: xapi
    xapi_extensions:
      - http://example.com/exercises/b9e16535-4fc9-4c66-ac87-3ad7ce515f5c/sensors/score


objectives:

  - name: xapi_syntax
    description: Data is a valid xAPI JSON file
    aspect: syntax
    evaluation:
      method:
        id: syntax_check
        args:
          checker: xapi
      type: valid_invalid

  - name: 1w_freshness
    description: Learning trace is not too old
    aspect: timeliness
    evaluation:
      method:
        id: timestamp_comparison
        args:
          timestamp: xapi_timestamp
          within: 1w
      type: in_range

  - name: new_user
    description: No data has been supplied about this actor in the past
    aspect: uniqueness
    evaluation:
      method:
        id: uniqueness_check
        args:
          target: actor.id
      type: valid_invalid
```

```yaml
---
id: urn:vla:example:moodle
meta:
  title: Moodle Learning Traces VLA Example
  version: 0.1.0
  description: |
    A simple Veracity Level Agreement (VLA) example for Moodle-like xAPI
    data
  exchange: bb54352d-3da4-4b6d-a4db-3639003f5f99


models:
  trace:
    description: xAPI trace
    type: xapi


objectives:

  - name: is_dases
    description: Trace is within the subset defined by Gaia-X DaSES
    aspect: schema
    evaluation:
      method:
        id: xapi_schema_dases
      type: valid_invalid
```


## Architecture

<!-- Abusing Mermaid's flowcharts... -->

```mermaid
---
title: Data Veracity Assurance High-Level Architecture
---

graph LR
  api>"fa:fa-plug\n Public API"]:::API
  ctrl["fa:fa-gear\n Internal Controller"]:::Controller
  att["fa:fa-stamp\n Attestation Service"]:::Service
  prov["fa:fa-file-circle-check\n Proving Service"]:::Service
  verif["fa:fa-check-double\n Verification Service"]:::Service
  log["fa:fa-file-lines\n Logging Service"]:::Service
  pers[("fa:fa-database\n Log Persistence")]:::Misc
  third["fa:fa-square-up-right Third Party Attester"]:::Misc
  gen["Built-in Proof Generator"]:::Misc
  gen_ext["External Proof Generator"]:::Misc

  api --> ctrl
  ctrl --> att & prov & verif & log
  att --> third
  prov --> gen & gen_ext
  log --> pers

  classDef default color:#000
  classDef API fill:lightgreen
  classDef Controller fill:cyan
  classDef Service fill:orange
  classDef Misc fill:grey
```


## Dynamic Behaviour

The sequence diagrams below describe possible DVA additions to the basic Connector flows.

_(To be discussed with Félix)_

```mermaid
---
title: Data Exchange with Attestation of Veracity (AoV)
---

sequenceDiagram
    participant p as Provider
    participant pc as Provider Connector
    participant con as Contract Service
    participant evs as External Veracity Attestation Service
    participant cat as Catalogue Service
    participant cc as Consumer Connector
    participant c as Consumer

    p -) cat: Trigger data exchange
    cat -) cc: data exchange info (w/ veracity level agreement)
    cc -) pc: data request (w/ contract + veracity level agreement)
    pc -) con: Verify contract & policies + veracity agreement
    Note over pc: Policy verification & Access control
    pc -) p: Get data
    p -) pc: data

    alt self-attestation
        pc -) pc: Get attestation of veracity
        pc -) cc: data + attestation
    else third-party attestation
        pc -) evs: Get attestation of veracity
        evs -) pc: attestation
        pc -) cc: data + attestation
    else no agreement / attestation
        pc -) cc: data
    end

    Note over cc: Policy verification & Access control
    cc -) c: data
```

```mermaid
---
title: Data Exchange with Proof of Veracity (PoV)
---

sequenceDiagram
    participant p as Provider
    participant pc as Provider Connector
    participant con as Contract Service
    participant evs as External Veracity Proving Service
    participant cat as Catalogue Service
    participant cc as Consumer Connector
    participant c as Consumer

    p -) cat: Trigger data exchange
    cat -) cc: data exchange info (w/ veracity level agreement)
    cc -) pc: data request (w/ contract + veracity level agreement)
    pc -) con: Verify contract & policies + veracity agreement
    Note over pc: Policy verification & Access control
    pc -) p: Get data
    p -) pc: data

    alt provider-proven veracity
        pc -) evs: Get Proof of Veracity
        evs -) pc: proof
        pc -) cc: data + proof
        cc -) cc: Verify proof
    else consumer-verified veracity
        pc -) cc: data
        alt local verification
            cc -) cc: Verify data veracity
        else external verification
            cc -) evs: Verify data veracity
        end
    else no agreement / verification
        pc -) cc: data
    end

    Note over cc: Policy verification & Access control
    cc -) c: data
```


## Configuration & Deployment Settings

One of the main questions is how many DVA instances there are in a data space.
For example, there may be a single centralized DVA instance that can be contacted by the connectors during data exchange.
However, a likely more advantageous approach is to have a decentralized configuration with several DVA instances.
There may be a DVA instance at the participating organizations – eg, P can use their own DVA instance to generate the proof or attestation that will be passed together with the data to C.
Likewise, C may use their ‘local’ DVA instance to perform the verification.

Going further, all the DVA instances may form a blockchain.
Using privacy-preserving features (such as private data in Hyperledger Fabric) it is possible for only the data exchange participants to see the proofs generated, while other data space participants merely see a record of the proof having been generated on the blockchain (as a commitment).


## Third Party Components & Licenses

_TBD_


## Implementation Details

_TBD_


## OpenAPI Specification

The current specification can be found in [`spec/openapi.yaml`](https://github.com/Prometheus-X-association/data-veracity/blob/main/spec/openapi.yaml).


## Test Specification

### Test Plan

The primary objective of testing will be to validate the correct handling of exchanged data compliant and non-compliant with the quality aspects established in the VLA.
Several data examples (including correct and incorrect samples) will be used for these tests.
Various data quality aspects will be targeted and case studies will be conducted using different data types used in the main project use cases, like VR traces (xAPI), Moodle learning traces (xAPI), and skills (ontology/terminology).

The integration with the _Dataspace Connector_ component will be tested thoroughy to verify that the necessary interactions are indeed possible and that error cases are handled properly (eg, when no data is received during a data exchange or data _is_ received but without a PoV/AoV even though it would be required).

While DVA will not directly integrate with the _Contract_ component, it should be tested that DVA can recognize VLA fragments defined in the contracts and that it is possible to extend existing contracts with VLA fragments.
In the end, this functionality will be provided by (or at least _via_) the _Catalogue_, not this BB.

Furthermore, interactions with other components, such as the _Data Value Chain Tracker (DVCT)_ will be validated through testing, as these potentially involve new interactions, protocols, and interfaces.

The DVA BB test acceptance critieria are, informally, and without striving for completeness:
* VLAs can be struck and parsed from contracts.
* DVA correctly handles data fulfilling the criteria in the corresponding VLA as well as data that is non-compliant.
* DVA can successfully communicate with the _Dataspace Connector_ and be a part of the data exchange flow.
* AoVs and PoVs can be created via DVA.
* No PoVs can be created for data that does not fulfil the VLA.

### Unit tests

### Integration Tests


## Abbreviations Used

| Abbreviation | Expansion |
| :--- | :--- |
| DVA | data veracity assurance building block |
| VLA | veracity level agreement |
| P | data producer |
| C | data consumer |
| PoV | proof of veracity |
| AoV | attestation of veracity |
