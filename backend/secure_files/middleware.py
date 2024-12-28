import time

from django.core.cache import cache
from django.conf import settings
from django.http import HttpResponse

class HttpResponseTooManyRequests(HttpResponse):
    status_code = 429

class IPRateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if 'download' in request.path.lower():
            client_ip = self.get_client_ip(request)
            if not self.check_rate_limit(client_ip):
                return HttpResponseTooManyRequests(
                    "Download rate limit exceeded. Please try again later.",
                    content_type="text/plain"
                )
        return self.get_response(request)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def check_rate_limit(self, ip):
        """
        Check if IP has exceeded rate limit
        Returns True if request is allowed, False if rate limit exceeded
        """
        window = getattr(settings, 'IP_RATE_LIMIT', {}).get('DOWNLOAD_WINDOW', 60)
        max_requests = getattr(settings, 'IP_RATE_LIMIT', {}).get('MAX_DOWNLOADS_PER_WINDOW', 2)
        
        cache_key = f'ip_rate_limit_{ip}'
        requests = cache.get(cache_key, [])
        
        # Remove old requests
        current_time = time.time()
        requests = [req_time for req_time in requests 
                   if current_time - req_time < window]
        
        if len(requests) >= max_requests:
            return False
        
        requests.append(current_time)
        cache.set(cache_key, requests, window)
        return True
    