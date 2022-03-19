import logging

import factory
import pytest

from id_infra.models import ViAccessDomain, ViAgent, ViAgentInterface
from vdx_id.test_factories.vdx import UserFactory

logger = logging.getLogger("vdx_id.%s" % __name__)

pytestmark = pytest.mark.django_db


class AgentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ViAgent

    agent_name = factory.Sequence(lambda n: "TestAgent {}".format(n))
    public_key = "I.O.U 1 key"


class AgentInterfaceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ViAgentInterface

    interface_id = factory.Sequence(lambda n: "TestInterface {}".format(n))
    code_fingerprint = "0"


class AccessDomainFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ViAccessDomain

    name = factory.Sequence(lambda n: "TestAccDom {}".format(n))
    interface = factory.SubFactory(AgentInterfaceFactory)
    owner = factory.SubFactory(UserFactory)
