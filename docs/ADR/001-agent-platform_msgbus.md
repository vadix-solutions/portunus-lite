# Agent-Platform interface Technologies


* Status: proposed <!-- optional -->
* Deciders: DVagg <!-- optional -->
* Date: 2021-02-25 <!-- optional -->

## Context and Problem Statement

Agents must communicate with the rest of the identity platform, covering both MSG-bus broker and object storage for collections.
This was performed entirely with MongoDB but support was questionable.

## Decision Drivers <!-- optional -->

* Technical Complexity
* Technology suitability
* Solution at scale (DR/HA/Geo-Sharding etc)
* If it worked

## Considered Options

* Broker = Redis | RabbitMQ
* ObjStore = Redis | RabbitMQ | MongoDB

## Decision Outcome

Chosen option: Redis for all

Earlier considered: MongoDB for ObjStore, RabbitMQ for Broker
Background: RabbitMQ needed to use redis for backend results (error).

Redis was then needed as a broker anyway, and then Mongo was only used for data store
We were leveraging JSON storage in Mongo but we weren't doing anything with the data once it was there
Because we only put it there for the platform to read, Redis was reviewed for that too.
We found a way of storing all data in Redis, now using only one component rather than 3 (monitoring utilities improved as a result)

### Positive Consequences <!-- optional -->

* Redis being used for all celery task/messaging allows better monitoring/control
* Redis has HA
* Fewer ports required

### Negative Consequences <!-- optional -->

## Links <!-- optional -->

* [ADR Template][https://raw.githubusercontent.com/joelparkerhenderson/architecture_decision_record/master/adr_template_madr.md]
