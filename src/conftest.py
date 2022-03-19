##
# © Copyright 2021 VaDiX Solutions <www.vadix.io>
##

import uuid

import pytest
from django.core.management import call_command
from pytest_factoryboy import register

from vdx_id.test_factories.infra import AccessDomainFactory
from vdx_id.test_factories.rbac import AccessRoleFactory
from vdx_id.test_factories.vdx import UserFactory

register(AccessDomainFactory)
register(AccessRoleFactory)
register(UserFactory)


@pytest.fixture
def test_password():
    return "strong-test-pass"


# Celery config to be used with integration tests
# TODO: Configure this to suit test environment
@pytest.fixture(scope="session")
def celery_config():
    return {"broker_url": "amqp://", "result_backend": "rpc"}


@pytest.fixture
def create_user(db, django_user_model, test_password):
    def make_user(**kwargs):
        kwargs["password"] = test_password
        if "username" not in kwargs:
            kwargs["username"] = str(uuid.uuid4())
        return django_user_model.objects.create_user(**kwargs)

    return make_user


@pytest.fixture
def auto_login_user(db, client, create_user, test_password):
    def make_auto_login(user=None):
        if user is None:
            user = create_user()
        client.login(username=user.username, password=test_password)
        return client, user

    return make_auto_login


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient

    return APIClient()


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command("loaddata", "init_data.json")
