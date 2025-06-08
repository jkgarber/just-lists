from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from incontext.auth import login_required
from incontext.db import get_db

bp = Blueprint('lists', __name__, url_prefix='/lists')

@bp.route('/')
@login_required
def index():
    db = get_db()
    lists = db.execute(
        'SELECT l.id, l.name, l.description, l.created'
        ' FROM lists l'
        ' WHERE l.creator_id = ?',
        (g.user['id'],)
    ).fetchall()
    return render_template('lists/index.html', lists=lists)


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        error = None
        if not name:
            error = 'Name is required.'
        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO lists (name, description, creator_id)'
                ' VALUES (?, ?, ?)',
                (name, description, g.user['id'])
            )
            db.commit()
            return redirect(url_for('lists.index'))

    return render_template('lists/create.html')


@bp.route('/<int:id>/edit', methods=('GET', 'POST'))
@login_required
def edit(id):
    list = get_list(id)
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        error = None
        if not name:
            error = 'Name is required.'
        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE lists SET name = ?, description = ?'
                ' WHERE id = ?',
                (name, description, id)
            )
            db.commit()
            return redirect(url_for('lists.index'))
    return render_template('lists/edit.html', list=list)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_list(id)
    db = get_db()
    # Delete item-detail relations
    # Delete related items
    # Delete related details
    # Delete list
    db.execute('DELETE FROM lists WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('lists.index'))


def get_list(id, check_creator=True):
    list = get_db().execute(
        'SELECT l.id, l.name, l.description, l.creator_id'
        ' FROM lists l'
        ' WHERE l.id = ?',
        (id,)
    ).fetchone()
    if list is None:
        abort(404, f'List with id {id} does not exist.')
    if check_creator and list['creator_id'] != g.user['id']:
        abort(403)
    return list
