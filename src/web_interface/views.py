##
# © Copyright 2021 VaDiX Solutions <www.vadix.io>
##

import hashlib
import json
import logging
import re
from datetime import datetime

import celery.states
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.http.response import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from id_infra.models import ViAccessDomain
from id_infra.models.agent import AgentApiTask
from id_infra.models.servers import AccessHost
from vdx_id.celery import app
from vdx_id.models import VdxIdUser

logger = logging.getLogger("vdx_id.%s" % __name__)


def index(request):
    if request.user.is_authenticated:
        return redirect("web:dashboard")
    else:
        return render(request, "front_page.html", {})


@login_required
def dashboard(request):
    context = {}

    context["stats"] = {
        "api_tasks": AgentApiTask.objects.count(),
    }
    context["api_tasks"] = AgentApiTask.objects.all().order_by("-id")[:5:-1]

    email_hash = hashlib.md5(
        request.user.email.lower().encode("utf-8")
    ).hexdigest()
    context["gravatar_url"] = f"https://www.gravatar.com/avatar/{email_hash}"

    return render(request, "web_ui/dashboard.html", context=context)


@login_required
@require_http_methods(["GET"])
def access_data(request):
    context = {}
    context["access_domains"] = ViAccessDomain.objects.all().order_by(
        "last_collection_id"
    )
    return render(request, "web_ui/access_data.html", context=context)


@login_required
@require_http_methods(["GET"])
def access_data_chartquery(request, accdom_pk):
    coll_meta = ViAccessDomain.objects.filter(pk=accdom_pk).values(
        "collection_meta"
    )[0]
    chart_data = {
        "labels": [],
        "accounts": [],
        "access_items": [],
        "memberships": [],
    }
    for col_id, col_meta_data in coll_meta["collection_meta"].items():
        ts_match = re.search(r"_((\d+)T(\d+))", col_id)
        d = datetime.strptime(ts_match.group(1), "%Y%m%dT%H%M%S")
        chart_data["labels"].append(d.strftime("%Y-%m-%d %H:%M:%S"))
        for dtype in ["accounts", "access_items", "memberships"]:
            value = 0
            if dtype in col_meta_data:
                value = col_meta_data[dtype]["obj_count"]
            chart_data[dtype].append(value)
    return JsonResponse(chart_data)


@login_required
@require_http_methods(["GET"])
def access_data_host_modal(request, host_pk):
    host_data = {}
    host = AccessHost.objects.get(pk=host_pk)

    host_data["address"] = host.address
    host_data["collection_data"] = host.collection_data
    host_data["collection_meta"] = []

    first_n_col_keys = sorted(
        [key for key in host.collection_meta.keys() if key.startswith("COLL")],
        reverse=True,
    )[:20]
    for colkey in first_n_col_keys:
        meta_entry = {
            dtype: host.collection_meta[colkey][dtype]["count"]
            for dtype in ["accounts", "access_items", "memberships"]
        }
        meta_entry["key"] = colkey
        host_data["collection_meta"].append(meta_entry)
    host_data["last_collection_id"] = host.last_collection_id
    return JsonResponse(host_data)


@require_http_methods(["GET"])
def view_activity_map(request):
    dataset = {}
    return render(
        request, "web_ui/map_visual.html", context={"dataset": dataset}
    )


@login_required
@require_http_methods(["GET"])
def report_builder(request):
    context = {"embed_url": "/report_builder"}
    # Populate account metrics
    return render(request, "web_ui/iframe_embed.html", context=context)


@login_required
@require_http_methods(["GET"])
def sql_explorer(request):
    context = {"embed_url": "/explorer"}
    # Populate account metrics
    return render(request, "web_ui/iframe_embed.html", context=context)


@login_required
@require_http_methods(["GET"])
def flower(request):
    context = {"embed_url": "/flower"}
    # Populate account metrics
    return render(request, "web_ui/iframe_embed.html", context=context)
