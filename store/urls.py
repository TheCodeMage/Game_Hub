
from django.urls import path

from . import views


app_name = "store"

urlpatterns = [
    path("", views.home, name="home"),
    path("games/", views.catalog, name="catalog"),
    path("games/<slug:slug>/", views.game_detail, name="game_detail"),
]
