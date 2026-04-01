# gui/network_checker.py
import requests

class NetworkChecker:
    """Class untuk mengecek koneksi internet"""
    
    @staticmethod
    def is_connected():
        """Cek koneksi internet dengan multiple endpoints"""
        endpoints = [
            "https://www.google.com",
            "https://www.cloudflare.com",
            "https://www.microsoft.com"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(endpoint, timeout=5)
                if response.status_code == 200:
                    return True
            except:
                continue
                
        return False
    
    @staticmethod
    def get_network_status():
        """Dapatkan status jaringan"""
        status = {
            "internet": NetworkChecker.is_connected(),
            "message": ""
        }
        
        if not status["internet"]:
            status["message"] = "⚠️ Tidak ada koneksi internet!"
        else:
            status["message"] = "✅ Koneksi internet stabil"
            
        return status