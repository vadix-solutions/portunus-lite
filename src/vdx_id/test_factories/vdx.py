import factory

from vdx_id.models import VdxIdUser


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = VdxIdUser

    username = factory.Sequence(lambda n: "TestUser {}".format(n))
