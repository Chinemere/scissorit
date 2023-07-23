from models import Url, User
from flask_login import current_user
import qrcode
import os



def analytics(short_url):
    url_record =Url.query.filter_by(scissored_url=short_url).first()
    if url_record:
            clicks = url_record.clicks+1
            created_time = url_record.created_at
            formatted_time = Url.getTime(created_time)
            history= [url_record.url_source, url_record.scissored_url, formatted_time, clicks]
            return history
    
    return {"error": "no such url"}



def linkhistory():
    username = current_user.username
    user = User.query.filter_by(username=username).first()

    user_links = user.url
    all_links = []
    for link in user_links:
        url_source = link.url_source
        scissored_url = link.scissored_url
        url_record =Url.query.filter_by(scissored_url=scissored_url).first()
        created_time = url_record.created_at
        formatted_time = Url.getTime(created_time)
        clicks = link.clicks
        link_info ={
             'url_source' : url_source,
             'scissored_url': scissored_url,
             'clicks': clicks,
             'created_at' : formatted_time
        }
        all_links.append(link_info)
        
    return all_links


# code to generate qrcode
def generate_qr_code(url):
    qr = qrcode.QRCode(
          version = 1,
          error_correction=qrcode.constants.ERROR_CORRECT_M,
          box_size=10,
          border=4,
          )
    qr.add_data(url)
    qr.make(fit=True)
    qr_image = qr.make_image(fill_color="black", back_color="white")
    return qr_image