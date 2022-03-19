.. _technical-details:

Terminology
^^^^^^^^^^^^^^^^^

Portunus is largely made of two high-level systems;
the first is related to infrastructure, and the second is Role Based Access Control (RBAC).

The infrastructure system is made up of Agents, AccessHosts, and interfaces (allowing agents to communicate with hosts).
It is responsible for the external hosts managed by Portunus.

The RBAC system involves AccessDomains (groups of hosts), accounts and so on.
It is responsible for managing the access of accounts and access on remote hosts through Agents.

Infrastructure Terminology
--------------------------

AccessHost
    Represents one host discovered by a particular Agent
HostScanDefinition
    Define a network segment for an Agent to scan for hosts
Agent
    Represents a single Agent of Portunus, usually deployed remotely
AgentInterface
    This is a coded interface specifying how Agents communicate to external hosts (AccessHosts).
AccessDomain
    A collection of AccessHosts which should all have the same access (account/memberships)

RBAC Terminology
----------------

AccessDomain:
    Represents a collection of AccessHosts where Access should be consistent.
    i.e. Every access-account in an AccessDomain should exist across all Hosts in that domain, and have the same access-item memberships (entitlements)

    Must be associated to a particular ViAgentInterface, which should not change.
    Any number of AccessHosts can be associated to any single AccessDomain.

    AccessDomains can run "Collections" which retrieve access information (i.e. accounts and memberships) from the associated AccessHosts using the ViAgentInterface
AccessItems:
    These represent atomic elements of access sometimes referred to as "entitlements". What these are depends on the ViAgentInterface and its implementation.
    On Unix for example, these would be Unix Groups. On PostgreSQL it could be roles or even individual permissions.
Accounts:
    These represent accounts within an AccessDomain. On Unix these would be user accounts.
AccessItemMemberships:
    These represent memberships of Accounts to AccessItems in the AccessDomain. On Unix these would be group memberships.
AccessRoles:
    These represent logical collections of AccessItems and other AccessRoles.
    If an AccessRole includes AccessItems, it only includes them from one single AccessDomain.
    An AccessRole can contain any other AccessRoles other than itself.
    AccessRoles can be associated with Rules (policies governing how access can be approved).
Rules:
    Rules define a mechanism of approving an access role membership.
    They can require another User (e.g. manager) to approve, or they can be purely programatic tests of other parameters (e.g. Users geographic location or other granted access)
RuleApproval:
    This is a record representing the approval for a particular (Rule, AccessRole, and User). Only particular Users are permitted to approve/reject the approval - this is determined by the combination of Rule/AccessRole/User.
RoleMembershipRequest:
    This is a request for Explicit membership of an AccessRole for a User.
    When a RoleMembershipRequest is created, an instance of a RuleApproval is generated for every Rule in all Access included by the intended AccessRole.

    For a RoleMembershipRequest to be Approved, each created RuleApproval must be approved.
RoleMemberships:
    These represent a user of the system being a member of a logical collection of Access.
    RoleMemberships can exist in two forms; Explicit and Implicit.

    Explicit membership is granted through a RoleMembershipRequest and must be approved.
    Only Explicit memberships define the access that a User should have (including all accounts and item-memberships for those accounts).

    Implicit Memberships are calculated by the collected data from the AccessDomain.

    So a User will have explicit memberships for all AccessRoles they are approved to be members of.
    Once access is fully provisioned, they will have an Implicit membership of all roles included by the Roles they are explicit members of.
