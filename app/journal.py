from flask import flash, redirect, url_for, request
from . import db
from .models import JournalEntry
from .utils.sanitize import sanitize_html
from .user_functions import _current_user, login_required, main




@main.route("/journal/new", methods=["POST"])
@login_required
def create_journal_entry():
    user = _current_user()
    if not user:
        flash("Please log in first.", "error")
        return redirect(url_for("main.login"))

    entry = JournalEntry(
        title="New Entry",
        content="",
        user_id=user.id,
        is_favourite=False)
    db.session.add(entry)
    db.session.commit()

    return redirect(url_for("main.journal", entry_id=entry.id))

@main.route("/journal/<int:entry_id>/save", methods=["POST"])
@login_required
def save_journal_entry(entry_id):
    user = _current_user()
    if not user:
        flash("Please log in first.", "error")
        return redirect(url_for("main.login"))

    entry = JournalEntry.query.filter_by(id=entry_id, user_id=user.id).first_or_404()

    raw_title = request.form.get("title", "").strip()
    raw_content = request.form.get("content", "").strip()

    entry.title = raw_title[:120] if raw_title else "Untitled"
    entry.content = sanitize_html(raw_content)

    db.session.commit()
    flash("Journal entry saved.", "success")
    return redirect(url_for("main.journal", entry_id=entry.id))


@main.route("/journal/<int:entry_id>/toggle-favourite", methods=["POST"])
@login_required
def toggle_journal_favourite(entry_id):
    user = _current_user()
    if not user:
        flash("Please log in first.", "error")
        return redirect(url_for("main.login"))

    entry = JournalEntry.query.filter_by(id=entry_id, user_id=user.id).first_or_404()
    entry.is_favourite = not entry.is_favourite
    db.session.commit()

    return redirect(url_for("main.journal", entry_id=entry.id))

@main.route("/journal/<int:entry_id>/delete", methods=["POST"])
@login_required
def delete_journal_entry(entry_id):
    user = _current_user()
    if not user:
        flash("Please log in first.", "error")
        return redirect(url_for("main.login"))

    entry = JournalEntry.query.filter_by(id=entry_id, user_id=user.id).first_or_404()

    db.session.delete(entry)
    db.session.commit()

    flash("Journal entry deleted.", "success")
    return redirect(url_for("main.journal"))
