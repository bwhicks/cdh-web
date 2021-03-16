import json
from datetime import datetime
from operator import attrgetter
from unittest.mock import Mock

import pytest
from django.utils import timezone
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from wagtail.core.models import Page, Site

from cdhweb.pages.models import ContentPage, HomePage, LandingPage
from cdhweb.pages.views import LastModifiedListMixin, LastModifiedMixin


@pytest.fixture
def site(db):
    """Ensure a single Wagtail site exists for testing."""
    return Site.objects.get()


@pytest.fixture
def homepage(db, site):
    """Create a test homepage and set it as the root of the Wagtail site."""
    root = Page.objects.get(title="Root")
    home = HomePage(title="home", slug="",
                    body=json.dumps([{
                        "type": "paragraph",
                        "value": "<p>content of the home page</p>"
                    }]))
    root.add_child(instance=home)
    root.save()
    site.root_page = home
    site.save()
    return home


@pytest.fixture
def landing_page(db, homepage):
    """Create a test landing page."""
    landing = LandingPage(title="landing", slug="landing", tagline="tagline",
                          body=json.dumps([{
                              "type": "paragraph",
                              "value": "<p>content of the landing page</p>"
                          }]))
    homepage.add_child(instance=landing)
    homepage.save()
    return landing


@pytest.fixture
def content_page(db, landing_page):
    """Create a test content page."""
    content = ContentPage(title="content", slug="content",
                          body=json.dumps([{
                              "type": "paragraph",
                              "value": "<p>content of the content page</p>"
                          }]))
    landing_page.add_child(instance=content)
    landing_page.save()
    return content


class MyModel:
    # fake model with timestamp field for testing LastModified views
    def __init__(self, updated):
        self.updated = updated


class MyModelQuerySet:
    # fake queryset for testing LastModified views
    def __init__(self, objects):
        self.objects = objects

    def exists(self):
        return bool(self.objects)

    def order_by(self, key):
        self.objects.sort(key=attrgetter(key))
        return self

    def first(self):
        return self.objects[0]


class MyLastModifiedDetailView(LastModifiedMixin, DetailView):
    # fake view that uses LastModifiedMixin for testing
    template_name = ""


class MyLastModifiedListView(LastModifiedListMixin, ListView):
    # fake view that uses LastModifiedListMixin for testing
    template_name = ""


@pytest.fixture
def lmod_view():
    """create a testing LastModifiedDetailView for one object"""
    view = MyLastModifiedDetailView()
    view.get_object = Mock(return_value=MyModel(updated=timezone.now()))
    return view


@pytest.fixture
def lmod_objects():
    """a list of fake model objects with different timestamps"""
    return [
        MyModel(updated=timezone.make_aware(datetime(2017, 1, 1, 20, 5))),
        MyModel(updated=timezone.make_aware(datetime(1990, 5, 4, 2, 55))),
        MyModel(updated=timezone.now()),
    ]


@pytest.fixture
def lmod_list_view(lmod_objects):
    """create a testing LastModifiedListView with several timestamped objects"""
    view = MyLastModifiedListView()
    view.get_queryset = Mock(return_value=MyModelQuerySet(lmod_objects))
    return view