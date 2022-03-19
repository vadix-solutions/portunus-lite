# Title

How access is managed by Portunus

## Status

* Status: accepted
* Deciders: DVagg
* Date: 2021-10-22

## Context

We manage access, and how that happens can get complicated quickly.
Sure adding it is easy, but what about approvals? What about if you remove access? What about if you have acess, request a group that encompasses one you already have, then remove the larger?

## Decision

Here are the components of Portunus for RBAC.

ViInfraServer:
    Represents one server discovered in a particular ServerGroup
ViServerGroups:
    Define how to find ViInfraServers using a set of basic rules (network scanning)
ViAgent:
    Represents a single Agent of Portunus, usually deployed somewhat remotely.
    Can find ViInfraServers using a ViServerGroup. These servers are linked to the discovering agent and the ServerGroup definition.
    By associating the ViInfraServer to the agent, we record how to reach the ViInfraServer
ViAgentInterface:
    This represents a code interface available to one or more Agents. There are usually multiple interfaces per agent, and agents can have the same interface.
    Interfaces define how agents make requests to endpoints (ViInfraServers).
AccessObject:
    An AccessObject is an abstract term to represent the components of access management on remote infrastructure. These include Accounts, AccessItems (i.e. entitlements) and AccessItemMemberships.
    Each of these are expected to be created/removed and otherwise manipulated as appropriate on the remote endpoints of an AccessDomain.
ViAccessDefinitions:
    Name is WIP.
    Defines the capabilities of a particular class of Access object (Account/Item/Memebership) - tied to the AccessDomain of those objects should not change.
    Defines the template used for creating new instances of these objects.
    Defined by an interface and tied to a particular version of interface.
    Can be copied and modified.
AccessDomains:
    Represent a collection of Servers where Access should be consistent.
    i.e. Every access-account in an AccessDomain should exist across each server in that domain, and have the same access-item memberships (entitlements)
    Must be associated to a particular ViAgentInterface, which should not change.
    Sets the particular ViAccessDefinitions to be used for managing each AccessObject type (account/item/membership).
    Any number of ViInfraServers can be associated to any single AccessDomain.
    An AccessDomain must be associated to one ViAgentInterface. This defines how the actual servers behind an AccessDomain are communicated with via the Agents.
    Each AccessDomain will be mapped to a ViAccessDefinition for each type of AccessObject (account/item/membership).
    These AccessDefinitions define the template for how NEW objects are created, and ALSO define the actions of the object and how they map to AgentInterface calls, including how parameters are resolved.
    AccessDomains can run "Collections" which retrieve access information (corresponding to access objects) from the associated ViInfraServers via the assigned ViAgentInterface
AccessItems:
    These represent atomic elements of access sometimes referred to as "entitlements". What these are depends on the ViAgentInterface and its implementation. On Unix for example, these would be Unix Groups. On PostgreSQL it could be roles or even individual permissions.
Accounts:
    These represent accounts within an AccessDomain (which by definition should be shared across all assigned servers). On Unix these would be user accounts.
AccessItemMemberships:
    These represent memberships of Accounts to AccessItems in the AccessDomain. On Unix these would be group memberships.
AccessRoles:
    These represent logical collections of AccessItems and other AccessRoles.
    If an AccessRole includes AccessItems, it must only include them from one single AccessDomain.
    An AccessRole can contain any other AccessRoles regardless of AccessDomain.
    An AccessRole can not include another Group if it would create a cyclic relationship of AccessRoles to each other.
    AccessRoles can be associated to any number of Rules.
Rules:
    Rules define a mechanism of approving an access group membership.
    They can require another User (e.g. manager) to approve, or they can be purely programatic tests of other parameters (e.g. Users geographic location or other granted access)
RuleApproval:
    This is a record representing the approval for a particular (Rule, AccessRole, and User). Only particular Users are permitted to approve/reject the approval - this is determined by the combination of Rule/AccessRole/User.
AccessRoleMemberships:
    These represent a user of the system being a member of a logical collection of Access.
    GroupMemberships can exist in two forms; Explicit and Implicit.
    Explicit membership is granted through a GroupMembershipRequest and must be approved. Only Explicit memberships define the access that a User should have (including all accounts and item-memberships for those accounts).
    Implicit Memberships are created corresponding to the collected data from the AccessDomain (the membership is implied by the collected access).
    So a User will have explicit memberships for all AccessRoles they are approved to be members of. Once access is fully provisioned, they will have an Implicit membership of all groups included by the Groups they are explicit members of (explicit member groups will also have an implicit membership then).
    AccessRoleMemberships have an expiry by default. The expiry is set by the GroupMembershipRequest. The expiry in the request is configurable, and by default will be a value set per User, which in turn is given a default value configured in the platform settings.
    AccessRoleMemberships can be set to 'indefinite'
GroupMembershipRequest:
    This is a record for membership requested between a User and an AccessRole.
    When created, all AccessRoles included by the requested AccessRole are inspected, and all Rules associated to all included AccessRoles are returned.
    A RuleApproval is then created for each unique AccessRole/Rule combination for the requesting User.
    For a GroupMembershipRequest to be Approved, each created RuleApproval must be approved.
    For example, if AccessRole (AG) AG-A includes AG-B and AG-C, and each of them have an approval rule (AR-1) associated with them, the GroupMembership will be approved when ['AR-1 for AG-A', 'AR-1 for AG-B'] are approved.

## Consequences

Here are the Actions of Portunus for RBAC.

Requesting Access:
    Users can create a GroupMembershipRequest to request their User be granted the access defined by an AccessRole (with all it includes).
Approving Access:
    All RuleApprovals generated for a GroupMembershipRequest must be approved.
    This then creates an AccessRoleMembership.
Removing Access:
    Remove access by removing an explicit membership of an AccessRole.
    The Explicit membership of any AccessRoles inherited by the 'removed' AccessRole are not affected by this operation.
Synchronizing Access:
    When a GroupMembership is changed for a user, they are marked as OutOfSync.
    Portunus will periodically review any Users OutOfSync and will determine the membership they should have by reviewing all Explicit Memberships.
    All AccessItems included by Explicit Memberships are measured for each User, and any required Accounts are determined.
    Required Accounts are provisioned using the corresponding AccessDefinition for the AccessDomain they exist in.
    If the required account for an AccessItemMembership exists, the membership is provisioned.
    Accounts that are not required, can be removed automatically.
    Memberships that are not required are removed automatically.
Expiring Access:
    Because memberships have an expiry, the explicit membership will automatically fade away unless set to Indefinite. This is done to pre-empt Access-Reviews and solve it at a more fundamental level.
    Approvers/Managers can renew the lease of a Membership, and will be notified prior to expiry.


## Behaviours

Removing an Account/Item:
    If you remove an account or access-item, all associated memberships are immediately marked as deprovisioned.
    Deprovisioning of the memberships is not requested, but is assumed to occur either directly or indirectly by the agent removing the account/item.
    In the case of Oracle DBs for example, this may need to be coded in the interface, to ensure that it removes memberships before removing the account.
Access Request:
    Each rule can return True/None/False for Approved/Pending/Rejected
    Even rules that don't involve a user reviewing the access (e.g. data check)
Policies:
    Rules are policies.
    Groups can have policies.
    Policies on all access can be periodically reviewed.
    This is nice because implicit memberships will be created and policy reviewed.
