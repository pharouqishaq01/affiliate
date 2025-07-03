import requests
import random
import time
import datetime
from campaigns import campaigns

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

# Determine which message to use
hour = datetime.datetime.utcnow().hour
messages = campaigns.get('messages', [])
rotation_index = hour % len(messages)
message = messages[rotation_index]
  # Rotates 0, 1, 2 throughout the day

for campaign in campaigns:
    print(f"\n📢 Starting campaign: {campaign['name']}")
    token = get_page_access_token(campaign['page_id'], campaign['user_access_token'])

    if not token:
        print(f"❌ Skipping campaign {campaign['name']} due to token issue.")
        continue

    images = campaign.get('default_images', [])
    place_ids = campaign.get('place_ids', [])
    messages = campaign.get('messages', [])

    if not images or not place_ids or not messages:
        print(f"⚠️ Skipping campaign {campaign['name']} due to missing data.")
        continue

    message = messages[rotation_index % len(messages)]
    image = random.choice(images)
    place = random.choice(place_ids)

    print(f"📸 Posting image: {image} | 📍 Place: {place} | 💬 Message: {message}")
    post_with_location(campaign['page_id'], token, image, place, message)
    time.sleep(1)

print("✅ All campaigns finished.")
