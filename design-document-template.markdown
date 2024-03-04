_BB Design Document Template_
=============================

_This is just a template.
Replace italic text with your own content.
Replace the title with `<BB name> Design Document`.
Using [Mermaid](http://mermaid.js.org/intro/) and/or [PlantUML](https://plantuml.com/) diagrams are recommended; see examples below.
You should also remove this paragraph._

_Summary of the BB in 1-2 concise paragraphs.
What does it do?
What are the main components?_


Use Cases & Features
--------------------

_Brief summary of use cases and features.
See [BB Info for UCs spreadsheet](https://docs.google.com/spreadsheets/d/1oKWCe0XqRJ1d-wZfKnFtZb2fS0NetFMEXX4OWSyiwDU)_

### Use Cases

_In-depth description of the use cases of the BB.
Explain why would one want to use this BB.
What services, features does it offer, why these are useful.
A bullet point list is recommended._

### Features

_In-depth description of BB features.
Again, an enumeration (ie bullet points) is useful._


Integrations
------------

_[See BB Connections Spreadsheet](https://docs.google.com/spreadsheets/d/1iNFLRofdwmrgNZ7E2JPSW0PL8xIUU4EVqIt-sMo9nlk)_

### Direct Integrations with Other BBs

_What other BBs does this BB interact with directly (without the connector)?
How?
Why?_

### Integrations via Connector

_What other BBs does this BB integrate with intermediated by the connector?
Why?_


Relevant Standards
------------------

### Data Format Standards

_Any data type / data format standards the BB adheres to_

### Mapping to Data Space Reference Architecture Models

_Mapping to [DSSC](https://dssc.eu/space/DDP/117211137/DSSC+Delivery+Plan+-+Summary+of+assets+publication) or [IDS RAM](https://docs.internationaldataspaces.org/ids-knowledgebase/v/ids-ram-4/)_


Input / Output Data
-------------------

_What data does this BB receive?
What data does this BB produce?
If possible, elaborate on the details (data format, contents, etc) and also add potential data requirements._

_Mermaid has no such feature, but you may use PlantUML to automatically visualize JSON schemata; for example:_

```plantuml
@startjson
{
   "fruit":"Apple",
   "size":"Large",
   "color": ["Red", "Green"]
}
@endjson
```

_Creating the diagram via the PlantUML JAR:_

```shell-session
$ java -jar plantuml.jar -tsvg json.puml
```

_Gives:_

![PlantUML JSON Example](diagrams/json.svg)


Requirements
------------

_High-level BB requirements with identifiers.
eg * **R1.** BB MUST communicate with [other BB]_

_See also [Requirement spreadsheets](https://drive.google.com/drive/folders/1q0FBj0OfXGlhfJBguuZOUxBG6ao2ZkRq)_


Architecture
------------

_What components make up this BB?
If applicable, insert a simple figure, eg a UML class diagram.
What is the purpose of the components and what are their relationships?_

_An example class diagram using Mermaid:_

```mermaid
---
title: Class Diagram Example (from Mermaid docs)
---

classDiagram
    Animal <|-- Duck
    Animal <|-- Fish
    Animal <|-- Zebra
    Animal : +int age
    Animal : +String gender
    Animal: +isMammal()
    Animal: +mate()
    class Duck{
        +String beakColor
        +swim()
        +quack()
    }
    class Fish{
        -int sizeInFeet
        -canEat()
    }
    class Zebra{
        +bool is_wild
        +run()
    }
```


Dynamic Behaviour
-----------------

_What is the behaviour of the BB, how does it operate?
UML sequence diagrams and/or statecharts are recommended._

_Example of a statechart using Mermaid:_

```mermaid
---
title: Statechart Example (Traffic Light)
---

stateDiagram-v2
    direction LR
    [*] --> Off
    Off --> On: turnOn
    state On {
        direction LR
        [*] --> Red
        Red --> RedYellow: timeRed
        RedYellow --> Green: timeRedYellow
        Green --> Yellow: timeGreen
        Yellow --> Red: timeYellow
    }
    On --> Off: turnOff
```

_Example sequence diagram using Mermaid:_

```mermaid
---
title: Sequence Diagram Example (Connector Data Exchange)
---

sequenceDiagram
    participant prov as Participant (Data Provider)
    participant provconn as Provider Data Space Connector
    participant contract as Contract Service
    participant catalogue as Catalogue Service
    participant consconn as Data Consumer Connector
    participant cons as Participant (Data Consumer)

    prov -) catalogue: Trigger data exchange
    catalogue -) consconn: contract & data exchange info
    consconn -) provconn: data request (w/ contract)
    provconn -) contract: Verify contract & policies
    Note over provconn: Policy verification & Access control
    provconn -) prov: Get data
    prov -) provconn: data
    provconn -) consconn: data
    Note over consconn: Policy verification & Access control
    consconn -) cons: data
```


Configuration
-------------

_What configuration options does this BB have?
What is the configuration format?
Provide examples._


Third Party Components & Licenses
---------------------------------

_Does this BB rely on any 3rd-party components?
See also [the relevant spreadsheet](https://docs.google.com/spreadsheets/d/13Lf4PfVnA_lAk-7dMeIy0QRxHnarxMcsS8EaLjyOlBA)_


Implementation Details
----------------------

_This is optional: remove this heading if not needed.
You can add details about implementation plans and lower-level design here._


OpenAPI Specification
---------------------

_In the future: link your OpenAPI spec here._
