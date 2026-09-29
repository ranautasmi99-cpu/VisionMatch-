from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from database import get_user_notifications, get_unread_notification_count, mark_notification_read

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/notifications')
@login_required
def index():
    notifs = get_user_notifications(current_user.id)
    return render_template('notifications.html', notifications=notifs)

@notifications_bp.route('/notifications/read/<int:notif_id>')
@login_required
def read(notif_id):
    link = mark_notification_read(notif_id, current_user.id)
    if link:
        return redirect(link)
    flash("Notification not found.", "error")
    return redirect(url_for('notifications.index'))

@notifications_bp.route('/api/notifications/unread_count')
@login_required
def unread_count():
    count = get_unread_notification_count(current_user.id)
    return jsonify({'count': count})
