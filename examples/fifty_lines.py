"""The entire TODO app, idiomatically, in one file.

This is the honest baseline the rest of the repository is measured against: a
working create / list / toggle / delete TODO in plain Django. No domain layer,
no ports, no unit of work, no event store — because a to-do list does not need
them. See docs/fifty-lines-vs-this.md for the side-by-side.

Run it (no migrations step needed — it creates its one table on first run):

    python examples/fifty_lines.py runserver
"""

import sys

from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY="fifty-lines-demo",  # throwaway demo key
        ROOT_URLCONF=__name__,
        ALLOWED_HOSTS=["*"],
        INSTALLED_APPS=["__main__"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": "fifty.sqlite3"}},
        MIDDLEWARE=[],
    )

import django  # noqa: E402

django.setup()

from django.core.management import execute_from_command_line  # noqa: E402
from django.db import connection, models  # noqa: E402
from django.http import HttpResponse, HttpResponseRedirect  # noqa: E402
from django.urls import path  # noqa: E402


class Task(models.Model):
    title = models.CharField(max_length=200)
    done = models.BooleanField(default=False)

    def __str__(self):
        return self.title


# One table, created on first run — the whole "persistence layer".
with connection.schema_editor() as editor:
    if Task._meta.db_table not in connection.introspection.table_names():
        editor.create_model(Task)


def index(request):
    items = "".join(
        f'<li><a href="/toggle/{t.pk}/">{"✓" if t.done else "○"}</a> '
        f"{'<s>' + t.title + '</s>' if t.done else t.title} "
        f'<a href="/delete/{t.pk}/">✕</a></li>'
        for t in Task.objects.all()
    )
    return HttpResponse(
        f"<h1>TODO</h1><ul>{items}</ul>"
        '<form method="post" action="/add/">'
        '<input name="title" placeholder="New task" autofocus><button>Add</button></form>'
    )


def add(request):
    if title := request.POST.get("title", "").strip():
        Task.objects.create(title=title)
    return HttpResponseRedirect("/")


def toggle(request, pk):
    task = Task.objects.get(pk=pk)
    task.done = not task.done
    task.save()
    return HttpResponseRedirect("/")


def delete(request, pk):
    Task.objects.filter(pk=pk).delete()
    return HttpResponseRedirect("/")


urlpatterns = [
    path("", index),
    path("add/", add),
    path("toggle/<int:pk>/", toggle),
    path("delete/<int:pk>/", delete),
]

if __name__ == "__main__":
    execute_from_command_line(sys.argv)
