import requests
import random
import time
from datetime import datetime, UTC
from campaigns import campaigns  # Import campaigns from campaigns.py

def get_page_access_token(page_id, user_token):
    url = f'https://graph.facebook.com/v20.0/{page_id}?fields=access_token&access_token={user_token}'
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json().get('access_token')
    except requests.RequestException as e:
        print(f"❌ Error retrieving access token for page {page_id}: {e}")
        return None

def post_with_location(page_id, token, image_url, place_id, message):
    # Step 1: Upload the photo as unpublished
    photo_url = f'https://graph.facebook.com/v20.0/{page_id}/photos'
    photo_payload = {
        'access_token': token,
        'url': image_url,
        'published': 'false'
    }
    photo_response = requests.post(photo_url, data=photo_payload)
    if photo_response.status_code != 200:
        print(f"❌ Failed to upload photo: {photo_response.text}")
        return

    photo_id = photo_response.json().get('id')
    if not photo_id:
        print("❌ No photo ID returned.")
        return

    # Step 2: Create feed post with attached media and location
    feed_url = f'https://graph.facebook.com/v20.0/{page_id}/feed'
    feed_payload = {
        'access_token': token,
        'message': message,
        'place': place_id,
        'attached_media': [{'media_fbid': photo_id}]
    }
    feed_response = requests.post(feed_url, json=feed_payload)
    if feed_response.status_code == 200:
        print(f"✅ Post successful at place {place_id}")
    else:
        print(f"❌ Failed to post to feed: {feed_response.status_code} {feed_response.text}")

# === MAIN LOOP ===

hour = datetime.now(UTC).hour  # ✅ Timezone-aware, future-proof

for campaign in campaigns:
    print(f"\n📢 Starting campaign: {campaign['name']}")
    token = get_page_access_token(campaign['page_id'], campaign['user_access_token'])

    if not token:
        print(f"❌ Skipping campaign {campaign['name']} due to token issue.")
        continue

    messages = campaign.get('messages', [])
    images = campaign.get('default_images', [])
    default_place_ids = campaign.get('default_place_id')

    if not messages or not images:
        print(f"⚠️ Skipping {campaign['name']} due to missing messages or images.")
        continue

    rotation_index = hour % len(messages)
    message_data = messages[rotation_index]

    # Support legacy plain-text messages
    if isinstance(message_data, str):
        message_data = {"text": message_data}

    message_text = message_data.get('text')

    # Determine place IDs (as a list)
    place_ids = message_data.get('place_id') or default_place_ids
    if isinstance(place_ids, str):
        place_ids = [place_ids]  # convert to list if string

    if not place_ids or not isinstance(place_ids, list):
        print(f"⚠️ No valid place IDs for message. Skipping.")
        continue

    # Post to each place
    for place_id in place_ids:
        image = random.choice(images)
        print(f"📸 Posting image: {image} | 📍 Place: {place_id} | 💬 Message: {message_text}")
        post_with_location(campaign['page_id'], token, image, place_id, message_text)
        time.sleep(1)

print("✅ All campaigns finished.")
