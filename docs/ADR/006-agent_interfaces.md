# Title

How interfaces are managed by Portunus

## Status

* Status: AGREED
* Deciders: DVagg
* Date: 2021-11-22

## Context

Interfaces for different endpoints need to be deployed on Agents.
We used to deploy on Agents directly and then read metadata in heartbeats.
We should deploy via platform instead.

## Decision


## Behaviours

* Users can deploy code directly to the agent as part of a CD pipeline
    * They should make an API call to update the recorded code signature for the interface
