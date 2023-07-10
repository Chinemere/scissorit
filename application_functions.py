from models import Url

def analytics(short_url):
    url_record =Url.query.filter_by(scissored_url=short_url).first()
    if url_record:
            created_time = url_record.created_at
            formatted_time = Url.getTime(created_time)
            history= [url_record.url_source, url_record.scissored_url, formatted_time, url_record.clicks]
            return history
    
    return {"error": "no such url"}



