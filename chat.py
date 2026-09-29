from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from database import get_conversation, create_conversation, get_user_conversations, get_conversation_by_id, insert_message, get_messages, get_item_by_id, is_blocked

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/chats')
@login_required
def my_chats():
    conversations = get_user_conversations(current_user.id)
    return render_template('chats.html', conversations=conversations)

@chat_bp.route('/chat/start/<int:item_id>', methods=['POST'])
@login_required
def start_chat(item_id):
    item = get_item_by_id(item_id)
    if not item:
        flash("Item not found.", "error")
        return redirect(request.referrer or url_for('home'))
        
    other_user_id = item['user_id']
    if other_user_id == current_user.id:
        flash("You cannot chat with yourself.", "error")
        return redirect(request.referrer or url_for('home'))
        
    if is_blocked(current_user.id, other_user_id):
        flash("You cannot start a chat with this user because one of you has blocked the other.", "error")
        return redirect(request.referrer or url_for('home'))
        
    conv = get_conversation(item_id, current_user.id, other_user_id)
    if conv:
        conv_id = conv['id']
    else:
        conv_id = create_conversation(item_id, current_user.id, other_user_id)
        
    return redirect(url_for('chat.room', conversation_id=conv_id))

@chat_bp.route('/chat/room/<int:conversation_id>')
@login_required
def room(conversation_id):
    conv = get_conversation_by_id(conversation_id)
    if not conv:
        flash("Conversation not found.", "error")
        return redirect(url_for('chat.my_chats'))
        
    # Check permissions
    if current_user.id not in [conv['user_a_id'], conv['user_b_id']]:
        flash("You don't have permission to view this chat.", "error")
        return redirect(url_for('chat.my_chats'))
        
    other_user_id = conv['user_a_id'] if current_user.id == conv['user_b_id'] else conv['user_b_id']
    item = get_item_by_id(conv['item_id'])
    
    return render_template('chat_room.html', conversation=conv, other_user_id=other_user_id, item=item)

@chat_bp.route('/api/chat/<int:conversation_id>/messages', methods=['GET'])
@login_required
def api_get_messages(conversation_id):
    conv = get_conversation_by_id(conversation_id)
    if not conv or current_user.id not in [conv['user_a_id'], conv['user_b_id']]:
        return jsonify({'error': 'Unauthorized'}), 403
        
    messages = get_messages(conversation_id)
    return jsonify({'messages': messages})

@chat_bp.route('/api/chat/<int:conversation_id>/messages', methods=['POST'])
@login_required
def api_send_message(conversation_id):
    conv = get_conversation_by_id(conversation_id)
    if not conv or current_user.id not in [conv['user_a_id'], conv['user_b_id']]:
        return jsonify({'error': 'Unauthorized'}), 403
        
    other_user_id = conv['user_a_id'] if current_user.id == conv['user_b_id'] else conv['user_b_id']
    if is_blocked(current_user.id, other_user_id):
        return jsonify({'error': 'User is blocked'}), 403
        
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'error': 'No text provided'}), 400
        
    text = data['text'].strip()
    if not text or len(text) > 500:
        return jsonify({'error': 'Message must be between 1 and 500 characters'}), 400
        
    msg_id = insert_message(conversation_id, current_user.id, text)
    
    # Create Notification
    from database import create_notification
    create_notification(
        user_id=other_user_id,
        type='message',
        text=f'New message from {current_user.name}',
        link=url_for('chat.room', conversation_id=conversation_id)
    )
    
    return jsonify({'success': True, 'message_id': msg_id})
