from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from incontext.auth import login_required
from incontext.db import get_db

bp = Blueprint('details', __name__, url_prefix='/details')

def get_creator_details():
    db = get_db()
    details = db.execute(
        'SELECT d.id, d.name, d.description, d.created, d.creator_id, u.username'
        ' FROM details d JOIN users u ON d.creator_id = u.id'
        ' WHERE d.creator_id = ?'
        ' ORDER BY created',
        (g.user['id'],)
    ).fetchall()
    return details

@bp.route('/')
@login_required
def index():
    details = get_creator_details()
    return render_template('details/index.html', details=details)

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
            cur = db.cursor()
            cur.execute(
                'INSERT INTO details (name, description, creator_id)'
                ' VALUES (?, ?, ?)',
                (name, description, g.user['id'])
            )
            detail_id = cur.lastrowid
            creator_items = cur.execute(
                'SELECT id FROM items'
                ' WHERE creator_id = ?',
                (g.user['id'],)
            ).fetchall()
            for item in creator_items:
                cur.execute(
                    'INSERT INTO item_detail_relations (item_id, detail_id, content)'
                    'VALUES (?, ?, ?)',
                    (item['id'], detail_id, '')
                )
            db.commit()
            return redirect(url_for('details.index'))

    return render_template('details/create.html')

@bp.route('/<int:id>/edit', methods=('GET', 'POST'))
@login_required
def edit(id):
    detail = get_detail(id)
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
                'UPDATE details SET name = ?, description = ?'
                ' WHERE id = ?',
                (name, description, id)
            )
            db.commit()
            return redirect(url_for('details.index'))

    return render_template('details/edit.html', detail=detail)


def get_detail(id, check_creator=True):
    detail = get_db().execute(
        'SELECT d.id, d.name, d.description, d.created, d.creator_id'
        ' FROM details d'
        ' WHERE d.id = ?',
        (id,)
    ).fetchone()

    if detail is None:
        abort(404, f"Detail with id {id} doesn't exist.")

    if check_creator and detail['creator_id'] != g.user['id']:
        abort(403)

    return detail

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_detail(id)
    db = get_db()
    db.execute('DELETE FROM details WHERE id = ?', (id,))
    db.execute('DELETE from item_detail_relations WHERE detail_id = ?', (id,))
    db.commit()
    return redirect(url_for('details.index'))
