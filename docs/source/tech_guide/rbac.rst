
RBAC the Portunus way
^^^^^^^^^^^^^^^^^^^^^

Portunus does a few things differently to what you may expect.


High level RBAC
---------------

Here are high-level actions of Portunus for RBAC.

Requesting Access:
    Users can create a RoleMembershipRequest to request their User be granted the access defined by an AccessRole (with all it includes).
Approving Access:
    All RuleApprovals generated for a RoleMembershipRequest must be approved.
    This then creates an AccessRoleMembership.
Removing Access:
    Remove access by removing an explicit membership of an AccessRole.
    The Explicit membership of any AccessRoles inherited by the 'removed' AccessRole are not affected by this operation.
Synchronizing Access:
    When a RoleMembership is changed for a user, they are marked as OutOfSync.
    Portunus will periodically review any Users OutOfSync and will determine the membership they should have by reviewing all Explicit Memberships.

    To synchronize access, the Accounts and AccessItem Memberships for each User are calculated.
    Missing accounts and memberships are provisioned (i.e. an Agent will provision to remote hosts). Any extra accounts and memberships are deprovisioned.
Expiring Access:
    Because memberships have an expiry, explicit memberships will automatically be removed.
    Approvers/Managers can renew the lease of a Membership, and will be notified prior to expiry.


RBAC behaviour
--------------

Removing an Account/Item:
    If you remove an account or access-item, all associated memberships are immediately marked as deprovisioned.
    Deprovisioning of the memberships is not requested, but is assumed to occur either directly or indirectly by the agent removing the account/item.
    In the case of Oracle DBs for example, this may need to be coded in the interface, to ensure that it removes memberships before removing the account.
Access Request:
    Each rule can return True/None/False for Approved/Pending/Rejected
    Even rules that don't involve a user reviewing the access (e.g. data check)
Policies:
    Rules are policies.
    Roles can have policies.
    Policies on all access can be periodically reviewed.
    This is nice because implicit memberships will be created and policy reviewed.
