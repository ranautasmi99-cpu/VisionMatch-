import os
import shutil
import uuid
from database import insert_user, insert_item, get_user_notifications, get_connection
from search import add_image_to_index
from matching import find_and_notify_matches

# Simple test script for match alerts
def run_test():
    print("[1] Creating demo users...")
    user_a_id = insert_user("User A (Lost)", "usera@test.com", "password")
    user_b_id = insert_user("User B (Found)", "userb@test.com", "password")
    
    # Use a dummy image, but we need an actual file for Gemini to process.
    # Let's create a blank dummy image if none exists.
    os.makedirs("test_images", exist_ok=True)
    dummy_img_path = "test_images/dummy_black_wallet.jpg"
    if not os.path.exists(dummy_img_path):
        # We need a real image format. We can just create a tiny 1x1 JPG using PIL.
        from PIL import Image
        img = Image.new('RGB', (100, 100), color = 'black')
        img.save(dummy_img_path)
    
    print("[2] Creating Lost item for User A...")
    lost_path = f"test_images/lost_{uuid.uuid4()}.jpg"
    shutil.copy(dummy_img_path, lost_path)
    lost_item_id = insert_item(
        name="Black Wallet",
        description="Lost my leather black wallet",
        category="wallet",
        status="lost",
        image_path=lost_path,
        location="Library",
        item_date="2023-10-01",
        user_id=user_a_id
    )
    # Add to FAISS
    add_image_to_index(lost_path, "Black Wallet | Lost my leather black wallet | wallet")

    print("[3] Creating Found item for User B...")
    found_path = f"test_images/found_{uuid.uuid4()}.jpg"
    shutil.copy(dummy_img_path, found_path)
    found_item_id = insert_item(
        name="Black Wallet",
        description="Found a black leather wallet",
        category="wallet",
        status="found",
        image_path=found_path,
        location="Library",
        item_date="2023-10-01",
        user_id=user_b_id
    )
    add_image_to_index(found_path, "Black Wallet | Found a black leather wallet | wallet")

    print("[4] Running find_and_notify_matches for the Found item...")
    # This should find the lost item
    find_and_notify_matches(found_item_id)
    
    print("[5] Checking if User A got a notification...")
    notifs_a = get_user_notifications(user_a_id)
    found_notif = False
    for n in notifs_a:
        if n['type'] == 'match':
            print(f"  -> SUCCESS! User A got notification: {n['text']}")
            found_notif = True
            break
            
    if not found_notif:
        print("  -> FAILED: User A did not get a match notification.")
        
    print("[6] Checking scores in DB...")
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM match_alerts WHERE lost_item_id=%s AND found_item_id=%s", (lost_item_id, found_item_id))
    alert = cursor.fetchone()
    if alert:
        print(f"  -> Match recorded! Final Score: {alert['final_score']}")
    else:
        print("  -> FAILED: No match_alert row created.")
        
    print("[7] Running it a second time to confirm no duplicates...")
    find_and_notify_matches(found_item_id)
    
    cursor.execute("SELECT COUNT(*) as c FROM match_alerts WHERE lost_item_id=%s AND found_item_id=%s", (lost_item_id, found_item_id))
    count = cursor.fetchone()['c']
    if count == 1:
        print("  -> SUCCESS: No duplicate match_alert was created.")
    else:
        print(f"  -> FAILED: Expected 1 match_alert, found {count}.")
        
    notifs_a_after = get_user_notifications(user_a_id)
    if len(notifs_a_after) == len(notifs_a):
        print("  -> SUCCESS: No duplicate notification was sent to User A.")
    else:
        print("  -> FAILED: Duplicate notification was sent.")
        
    cursor.close()
    conn.close()
    
    # Cleanup dummy files
    try:
        os.remove(lost_path)
        os.remove(found_path)
    except:
        pass
        
    print("\nTest completed.")

if __name__ == "__main__":
    run_test()
