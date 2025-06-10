import sqlite3
import os

import pytest
from incontext.db import get_db
from flask import g, session


def test_get_close_db(app):
    with app.app_context():
        db = get_db()
        assert db is get_db() # within an application context, `get_db` should return the same connection each time it's called.

    with pytest.raises(sqlite3.ProgrammingError) as e:
        db.execute('SELECT 1')

    assert 'closed' in str(e.value) # After the context, the connection should be closed.


def test_init_db_command(runner, monkeypatch):
    class Recorder:
        called = False

    def fake_init_db():
        Recorder.called = True

    monkeypatch.setattr('incontext.db.init_db', fake_init_db) # pytest's monkeypatch replaces the `init_db` function with one that does nothing but record that it was called.
    result = runner.invoke(args=['init-db']) # the runner fixture called the `init-db` command (which calls the monkeypatched `init_db` function).
    assert 'Initialized' in result.output
    assert Recorder.called


def test_data_entry(app):
    with app.app_context():
        db = get_db()
        item_count = db.execute('SELECT COUNT(id) AS count FROM items').fetchone()['count']
        assert item_count == 6
        detail_count = db.execute('SELECT COUNT(id) AS count FROM details').fetchone()['count']
        assert detail_count == 6
        idr_count = db.execute('SELECT COUNT(id) AS count FROM item_detail_relations').fetchone()['count']
        assert idr_count == 10
        list_count = db.execute('SELECT COUNT(id) AS count FROM lists').fetchone()['count']
        assert list_count == 4
        lir_count = db.execute('SELECT COUNT(id) AS count FROM list_item_relations').fetchone()['count']
        assert lir_count == 6
        ldr_count = db.execute('SELECT COUNT(id) AS count FROM list_detail_relations').fetchone()['count']
        assert ldr_count == 6
       

def test_admin_login(client, auth):
    username = 'admin'
    password = os.environ.get('IC_ADMIN_PW_RAW')
    auth.login(username, password)
    with client:
        client.get('/')
        assert session['user_id'] == 1
        assert g.user['username'] == 'admin'

