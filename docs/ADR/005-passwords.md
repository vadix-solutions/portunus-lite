# Title

How passwords are managed by Portunus

## Status

* Status: wip
* Deciders: DVagg
* Date: 2021-11-22

## Context

Passwords will need to be managed.
Tools such as Vault are seeing widespread adoption, so we are going to use that.

## Decision

* Portunus will offload management of passwords (at least everything except Django platform accounts) to Vault.
* Operators can then customize ACL in Vault for management of secrets.
* Secrets will be stored in the vault following a reasonable tree structure.
    users/admin/accounts/1.u_ADMIN
        { "password": "something" }
    access_domains/secrets
        { "ssh_password": "something" }
* Users will be able to reset their own passwords.
    * Password policies in vault will be respected
* Updating an account password involes the following:
    * New password generated - policy accepted
    * Password written to vault under users path
    * Password used as kwarg to set_password API call distributed to endpoints

## Behaviours

* Periodic rotation of accounts can be scheduled in Portunus
