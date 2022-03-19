##
# © Copyright 2021 VaDiX Solutions <www.vadix.io>
##

from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("dashboard", views.dashboard, name="dashboard"),
    path("access_data", views.access_data, name="access_data"),
    path(
        "access_data/chart_data/<int:accdom_pk>/",
        views.access_data_chartquery,
        name="access_data_chartquery",
    ),
    path(
        "access_data/host_model/<int:host_pk>/",
        views.access_data_host_modal,
        name="access_data_host_modal",
    ),
    path("map_visual", views.view_activity_map, name="map_visual"),
    path("reports", views.report_builder, name="report_builder"),
    path("sql_explorer", views.sql_explorer, name="sql_explorer"),
    path("task_flower", views.flower, name="flower"),
]
