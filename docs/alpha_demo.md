
Alpha Demo Guide
================

Local Dev quickstart
^^^^^^^^^^^^^^^^^^^^

Start up docker-compose

``docker-compose up -d``

Migrate & Populate DB

``docker-compose exec django_wsgi python3 manage.py migrate``
``docker-compose exec django_wsgi python3 manage.py loaddata init_data``

Start Nginx with some certs

``sudo bash scripts/init-letsencrypt.sh``

Start up sample Unix containers

``COUNT=10 ./scripts/load_test.sh``

Login using ``admin/v4d1x_admin``

Prepare the vault
-----------------

Unseal the vault if required ``docker-compose exec vault vault operator unseal``

Initializing the vault if required

``docker-compose exec vault vault status``

``sudo chown systemd-network -R vault``
``docker-compose exec vault vault operator init``

Record the unseal keys and initial root token somewhere safe - insert the keys when unsealing the vault in future, and use the root token in below commands.

Setup portunus access to vault
******************************

1. Navigate to Vault UI
2. Create a Policy called 'portunus'

.. code-block:: json

    {
        "path": {
            "portunus/*": {
            "capabilities": [
                "create",
                "read",
                "update"
            ]
            }
        }
    }


3. Go to token/, then create new token called 'portunus'

   a. 24 hour ttl + role(portunus)
   b. docker-compose exec vault vault login
   c. VAULT_TOKEN=<THE TOKEN> docker-compose exec vault vault token create -policy=portunus

4. If the policy already exists and a new token is required:
``export VAULT_TOKEN=$(docker-compose exec -e VAULT_TOKEN=s.UWvRGi4sAjTmleEEaTnunIWN vault vault token create -policy=portunus -field token)``

Setup password policies
***********************

Reference: https://learn.hashicorp.com/tutorials/vault/password-policies?in=vault/secrets-management

Run the following

.. code-block:: bash

    tee example_policy.hcl <<EOF
    length=20
    rule "charset" {
    charset = "abcdefghijklmnopqrstuvwxyz"
    min-chars = 1
    }
    rule "charset" {
    charset = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    min-chars = 1
    }
    rule "charset" {
    charset = "0123456789"
    min-chars = 1
    }
    rule "charset" {
    charset = "!@#$%^&*"
    min-chars = 1
    }
    EOF

    vault write sys/policies/password/example policy=@example_policy.hcl

    vault read sys/policies/password/example/generate


#
vadix@ip-172-31-32-205:/opt/vadix/portunus$ docker-compose exec vault vault operator init
WARNING: The VAULT_TOKEN variable is not set. Defaulting to a blank string.
Unseal Key 1: sBZHhUl7/7pqMMV41AArH99yfFe1cGffglPY8sg2avvk
Unseal Key 2: 15PuKNzl3o8yqiZqgQ63gzZqHWPCl3S0+BJ8xf7Jf5k7
Unseal Key 3: o5fprctvRsyaGnQDsqyFUr+J7fP4/88tSL4btQSb1fYC
Unseal Key 4: s/7pUR9SOTAbzI3kJYQx2a5k2Xk77bYsdy8x8taX/64D
Unseal Key 5: 5D0tG6juRpZjmC69JXiHp4ZKq0NxpinhyPR0tBYKWcjI

Initial Root Token: s.EELorgCC2tpKUKYlnBKCMaRk
