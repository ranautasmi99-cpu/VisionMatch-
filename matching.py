import os
import faiss
import json
import numpy as np
from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from database import get_connection, get_item_by_id, create_notification
from search import search_multimodal, INDEX_FILE, TEXT_INDEX_FILE, IMAGE_PATHS_FILE

matching_bp = Blueprint('matching', __name__)

def find_and_notify_matches(new_item_id):
    """
    Finds strong matches for a newly reported item and notifies the owners.
    Uses existing embeddings in FAISS, avoids generating new ones.
    """
    new_item = get_item_by_id(new_item_id)
    if not new_item:
        return

    threshold = float(os.getenv("MATCH_THRESHOLD", "0.75"))
    
    # 1. We want to match opposite types
    new_status = new_item['status'].strip().lower()
    if new_status not in ['lost', 'found']:
        return
        
    normalized_path = new_item['image_path'].replace("\\", "/")

    # 2. Extract existing embeddings from FAISS
    # We must find the index of the new item in image_paths.json
    if not os.path.exists(IMAGE_PATHS_FILE):
        return
        
    with open(IMAGE_PATHS_FILE, "r") as f:
        image_paths = json.load(f)
        
    try:
        # Get the latest occurrence of this image_path
        item_index = len(image_paths) - 1 - image_paths[::-1].index(normalized_path)
    except ValueError:
        return # Not found in FAISS
        
    img_index = faiss.read_index(INDEX_FILE)
    txt_index = faiss.read_index(TEXT_INDEX_FILE)
    
    # Reconstruct vectors from FAISS to avoid Gemini call
    img_vec = img_index.reconstruct(item_index)
    txt_vec = txt_index.reconstruct(item_index)
    
    img_vec_2d = np.array([img_vec], dtype=np.float32)
    txt_vec_2d = np.array([txt_vec], dtype=np.float32)

    # 3. Search using the existing 60/25/15 scoring function
    matches = search_multimodal(
        query_category=new_item['category'],
        query_location=new_item['location'],
        query_status=new_item['status'],
        top_k=50, # Retrieve enough to filter down
        query_img_vec_2d=img_vec_2d,
        query_txt_vec_2d=txt_vec_2d
    )
    
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    notified_count = 0
    
    for match in matches:
        if notified_count >= 3:
            break
            
        if match['final_score'] < threshold:
            continue
            
        matched_item = match['item']
        if not matched_item:
            continue
            
        # Must be different users
        if matched_item['user_id'] == new_item['user_id']:
            continue
            
        # Must be opposite status
        m_status = matched_item['status'].strip().lower()
        if not ((new_status == 'lost' and m_status == 'found') or (new_status == 'found' and m_status == 'lost')):
            continue
            
        # We need a predictable order for lost_item_id and found_item_id
        if new_status == 'lost':
            lost_id = new_item_id
            found_id = matched_item['id']
        else:
            lost_id = matched_item['id']
            found_id = new_item_id
            
        # Prevent duplicates by checking match_alerts
        check_query = "SELECT id FROM match_alerts WHERE lost_item_id = %s AND found_item_id = %s"
        cursor.execute(check_query, (lost_id, found_id))
        if cursor.fetchone():
            continue
            
        # Record the alert
        insert_alert = """
            INSERT INTO match_alerts 
            (lost_item_id, found_item_id, final_score, image_score, text_score, metadata_score)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_alert, (
            lost_id, found_id, 
            match['final_score'], match['image_similarity'], 
            match['text_similarity'], match['metadata_score']
        ))
        match_alert_id = cursor.lastrowid
        connection.commit()
        
        # Link for the match page
        link = url_for('matching.match_details', match_id=match_alert_id)
        
        # Notify the owner of the OTHER item
        other_text = f"A possible match for your {m_status} {matched_item['name']} was just reported."
        cursor.execute("INSERT INTO notifications (user_id, type, text, link) VALUES (%s, %s, %s, %s)", 
                       (matched_item['user_id'], 'match', other_text, link))
                       
        # Notify the reporter of the NEW item
        new_text = f"We found a possible match for the item you reported ({new_item['name']})."
        cursor.execute("INSERT INTO notifications (user_id, type, text, link) VALUES (%s, %s, %s, %s)", 
                       (new_item['user_id'], 'match', new_text, link))
                       
        connection.commit()
        notified_count += 1
        
    cursor.close()
    connection.close()


@matching_bp.route('/match/<int:match_id>')
@login_required
def match_details(match_id):
    """
    Displays a side-by-side comparison of two matched items and their scores.
    """
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM match_alerts WHERE id = %s", (match_id,))
    alert = cursor.fetchone()
    cursor.close()
    connection.close()
    
    if not alert:
        flash("Match not found.", "error")
        return redirect(url_for('home'))
        
    lost_item = get_item_by_id(alert['lost_item_id'])
    found_item = get_item_by_id(alert['found_item_id'])
    
    if not lost_item or not found_item:
        flash("One or both items could not be found.", "error")
        return redirect(url_for('home'))
        
    # Check permissions
    if current_user.id not in [lost_item['user_id'], found_item['user_id']]:
        flash("You do not have permission to view this match.", "error")
        return redirect(url_for('home'))
        
    # Determine the "other" item to chat about
    if current_user.id == lost_item['user_id']:
        other_item = found_item
        my_item = lost_item
    else:
        other_item = lost_item
        my_item = found_item

    return render_template('match_details.html', 
                           lost_item=lost_item, 
                           found_item=found_item, 
                           alert=alert,
                           other_item=other_item,
                           my_item=my_item)
