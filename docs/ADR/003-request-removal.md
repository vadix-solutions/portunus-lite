# Title

Largely removing FSM Access Requests.

## Status

* Status: its happenin
* Deciders: DVagg
* Date: 2021-10-11

## Context

In the Janus platform there were several moving parts;
* Item Requests (would influence provisioning)
* Group Requests (supported approvals)
* Access sync (which created Item/Group Requests)
* Item Request Processing (which read all access items from DB in processing state)
    * It also evaluated what they could do to move forward in their request
    * This involved evaluating conditions and rules which may have been DB related
* Group Request Processing (another batch process like Item Request Processing)
    * Chased approvals from other identities

The problem here is that the design of the requests are very difficult to optimize. We are very performant now but with 1000s users and millions of access items it would be unnecessarily bad.
Every request in progress has to be individually worked on (in terms of evaluting conditions and state). FSM was a good idea in principal there, but a dynamic graph is unnecssary for access requests which should have a well defined and correct workflow.

We got some nice optimizations to AccessSync - especially in terms of reduced DB access. Contrast of Sync against Requests is stronger now, so lets fix it.


## Decision

AccessItemRequests are being thrown out.
The work they did is better placed in the AccessSync process (which would already know what accounts exist and memberships etc).

AccessRoleRequests are being refined to AccessRoleApprovals.
They will be designed with the primary intent of supporting approval rules and tracking for access.

AccessRole and AccessRoleMembership will support API calls for requests to be easily made. Details to be worked out.

## Consequences

More API
More rewriting
ApprovalRequests need to be worked out
AccessObjects will have a task-record mixin to track owned Agent tasks
