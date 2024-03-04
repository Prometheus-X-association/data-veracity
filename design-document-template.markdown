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

_Brief summary of use cases and features._

### Use Cases

_In-depth description of the use cases of the BB.
Explain why would one want to use this BB.
What services, features does it offer, why these are useful.
A bullet point list is recommended._

### Features

_In-depth description of BB features.
Again, an enumeration (ie bullet points) is useful._

### Target Users

_Who will be the users of the BB?
What does the BB provide to these users?_


Integrations
------------

_What other BBs does this BB interact with?
How?
Why?_


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
title: Sequence Diagram Example (from Mermaid docs)
---

sequenceDiagram
    Alice->>Bob: Hello Bob, how are you?
    alt is sick
        Bob->>Alice: Not very good
    else is well
        Bob->>Alice: I feel great
    end
    opt Extra response
        Bob->>Alice: Thanks for asking
    end
```


Configuration
-------------

_What configuration options does this BB have?
What is the configuration format?
Provide examples._


Implementation Details
----------------------

_This is optional: remove this heading if not needed.
You can add details about implementation plans and lower-level design here._
