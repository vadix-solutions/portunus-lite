This is the template in [Documenting architecture decisions - Michael Nygard](http://thinkrelevance.com/blog/2011/11/15/documenting-architecture-decisions).
You can use [adr-tools](https://github.com/npryce/adr-tools) for managing the ADR files.

# Title

Work deferral mechanism

## Status

* Status: proposed
* Deciders: DVagg
* Date: 2021-09-24

## Context

Work sometimes needs to be deferred - like removing an access item from a group when it could potentially impact 1000 users.
Measuring if the work is safe or needs to be deferred is fine - but storing the task in a way where it could be done later is not.

## Decision

By ensuring that the platform is COMPLETELY utilized through REST API, we can capture any operation as a REST API call and safely record it in JSON.
The JSON can be easily stored in the database with a set of rules/policies that must pass some criteria before being triggered (i.e. API call is made) by a user, or automatically by the platform.

## Consequences

I have to write a lot more API
Also routing probably needs to be done
