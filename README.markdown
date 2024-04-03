# Data Veracity Assurance BB Design Document

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

### Features/Main Functionalities

Key functionalities:
1. Manage data veracity level agreements
2. Provide means to verify the veracity of exchanged data
3. Log results of verification

DVA also potentially enables proving/verifying such properties about the shared data that are related to additional, sensitive (eg due to GDPR) data, without disclosing them (possibly using zero-knowledge proofs).

### Technical Usage Scenarios

With DVA, data exchange participants can be assured that the data fulfils predefined quality requirements.

#### Management of Veracity Level Agreements

<!-- TODO -->

#### Proving & Attestation of Veracity

<!-- TODO -->

#### Logging of Results

<!-- TODO -->


## Requirements

* **`[BB_08__01]`** DVA MUST define schemata for Data Veracity Agreements
* **`[BB_08__02]`** DVA MUST support striking Data Veracity Agreements through the Catalogue
* **`[BB_08__03]`** DVA MUST provide multiple veracity assurance methods
* **`[BB_08__03]`** DVA MUST support veracity attestation (ie either provider or a third party attests that veracity requirements are met
* **`[BB_08__04]`** DVA SHOULD support veracity self-attestation
* **`[BB_08__05]`** DVA SHOULD support third-party veracity attestation
* **`[BB_08__06]`** DVA SHOULD support provider-proven veracity
* **`[BB_08__07]`** DVA SHOULD support consumer-verified veracity
* **`[BB_08__08]`** DVA SHOULD interface with the Contract service
* **`[BB_08__09]`** DVA SHOULD interface with the Connector


## Integrations

### Direct Integrations with Other BBs

_No direct integrations identified as of yet._


### Integrations via Connector

* DVA will likely have to directly integrate with the **Connector** itself to extend data exchange flows with veracity assurance steps
* As veracity level agreements are similar to contracts (or will become part of the contracts), DVA will have interactions with the **Contract** component
* Potential integrations with **Consent** as well (?)
* Most likely, DVA will integrate closely with the **Data Value Chain Tracker** BB
  * The _value_ is strongly related to the quality of the data assured by DVA


## Relevant Standards

### Data Format Standards

<!-- TODO -->

### Mapping to Data Space Reference Architecture Models

<!-- TODO -->


## Input / Output Data

### Data Veracity Level Agreements

_No concrete schema has been defined yet, please refer to conceptual model for what may be included in an agreement._


## Architecture

<!-- TODO -->


## Dynamic Behaviour

The sequence diagrams below describe possible DVA additions to the basic Connector flows.

_To be discussed with Félix_

```mermaid
---
title: Data Exchange with Attestation of Veracity
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
title: Data Exchange with Proof of Veracity
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

<!-- TODO -->


## Third Party Components & Licenses

<!-- TODO -->


## Implementation Details

<!-- TODO -->


## OpenAPI Specification

<!-- TODO -->


## Test Specification

<!-- TODO -->

### Test Plan

### Unit tests

### Integration Tests
