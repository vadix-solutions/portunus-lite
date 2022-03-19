##
# © Copyright 2021 VaDiX Solutions <www.vadix.io>
##

import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestWebUrls:
    def test_home(self, client):
        url = reverse("web:index")
        response = client.get(url)
        assert response.status_code == 200

    @pytest.mark.parametrize(
        "acm_page_name",
        [
            ("home",),
            ("view_access_domains",),
            ("report_builder",),
            ("sql_explorer",),
        ],
    )
    def test_acm_unauth_views_redirect(self, acm_page_name, client):
        url = reverse("web:%s" % acm_page_name)
        login_url = reverse("login")
        response = client.get(url, follow=True)
        assert len(response.redirect_chain) > 0, (
            "Url %s not redirecting" % acm_page_name
        )
        last_redirect, code = response.redirect_chain[-1]
        assert code == 302
        assert last_redirect.startswith(login_url)

    @pytest.mark.parametrize(
        "acm_page_name",
        [
            ("home",),
            ("view_access_domains",),
            ("report_builder",),
            ("sql_explorer",),
        ],
    )
    def test_acm_auth_views(self, acm_page_name, auto_login_user):
        client, user = auto_login_user()
        url = reverse("web:%s" % acm_page_name)
        response = client.get(url, follow=True)
        assert response.status_code == 200
