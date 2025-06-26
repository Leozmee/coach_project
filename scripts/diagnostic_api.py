# scripts/diagnose_api.py - Script de diagnostic pour l'erreur 500

import requests
import json
import traceback
from datetime import datetime

def test_api_endpoints():
    """Test tous les endpoints de l'API pour diagnostiquer l'erreur 500"""
    
    base_url = "http://127.0.0.1:8001"
    
    print("🔍 DIAGNOSTIC API COACH FITNESS")
    print("=" * 50)
    
    endpoints_to_test = [
        {"url": "/", "method": "GET", "description": "Page d'accueil"},
        {"url": "/health", "method": "GET", "description": "Health check"},
        {"url": "/models", "method": "GET", "description": "Modèles disponibles"},
        {"url": "/stats", "method": "GET", "description": "Statistiques"},
        {"url": "/test", "method": "GET", "description": "Test des modèles"},
    ]
    
    for endpoint in endpoints_to_test:
        print(f"\n🧪 Test {endpoint['description']}: {endpoint['url']}")
        print("-" * 40)
        
        try:
            if endpoint['method'] == 'GET':
                response = requests.get(f"{base_url}{endpoint['url']}", timeout=10)
            
            print(f"📡 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ SUCCESS")
                try:
                    data = response.json()
                    print(f"📄 Response keys: {list(data.keys()) if isinstance(data, dict) else 'Non-dict response'}")
                    
                    # Health check spécifique
                    if endpoint['url'] == '/health':
                        print(f"🤖 Status: {data.get('status', 'unknown')}")
                        print(f"🔧 Device: {data.get('device', 'unknown')}")
                        print(f"🧠 Current Model: {data.get('current_model', 'unknown')}")
                        if 'models' in data:
                            for model_key, model_info in data['models'].items():
                                loaded = "✅" if model_info.get('loaded', False) else "❌"
                                print(f"   {loaded} {model_info.get('name', model_key)}")
                    
                    # Models check spécifique
                    elif endpoint['url'] == '/models':
                        print(f"🤖 Current Model: {data.get('current_model', 'unknown')}")
                        if 'models' in data:
                            for model_key, model_info in data['models'].items():
                                loaded = "✅" if model_info.get('loaded', False) else "❌"
                                print(f"   {loaded} {model_info.get('name', model_key)}")
                    
                except Exception as e:
                    print(f"⚠️ Erreur parsing JSON: {e}")
                    print(f"📄 Raw response: {response.text[:200]}...")
            
            elif response.status_code == 500:
                print("❌ ERROR 500 - Internal Server Error")
                print(f"📄 Error response: {response.text[:500]}...")
                
                # Essayer de parser l'erreur JSON
                try:
                    error_data = response.json()
                    print(f"🚨 Error details: {error_data}")
                except:
                    pass
            
            else:
                print(f"⚠️ Unexpected status: {response.status_code}")
                print(f"📄 Response: {response.text[:200]}...")
        
        except requests.exceptions.ConnectionError:
            print("❌ CONNECTION ERROR - API non accessible")
            print("💡 Vérifiez que l'API est lancée avec: python scripts/start_api.py")
            break
        
        except requests.exceptions.Timeout:
            print("⏰ TIMEOUT - L'API met trop de temps à répondre")
        
        except Exception as e:
            print(f"❌ UNEXPECTED ERROR: {e}")
            print(f"🔍 Traceback: {traceback.format_exc()}")
    
    # Test d'un appel chat simple
    print(f"\n🧪 Test Chat endpoint")
    print("-" * 40)
    
    try:
        chat_data = {
            "message": "Hello test",
            "profile": None,
            "model_type": None
        }
        
        response = requests.post(
            f"{base_url}/chat",
            json=chat_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"📡 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Chat SUCCESS")
            try:
                data = response.json()
                print(f"🤖 Model used: {data.get('model_used', 'unknown')}")
                print(f"⚡ Response time: {data.get('response_time', 0):.2f}s")
                print(f"💬 Response preview: {data.get('response', '')[:100]}...")
            except Exception as e:
                print(f"⚠️ Error parsing chat response: {e}")
        else:
            print("❌ Chat FAILED")
            print(f"📄 Error: {response.text[:300]}...")
            
    except Exception as e:
        print(f"❌ Chat test error: {e}")

def check_service_logs():
    """Suggestions pour vérifier les logs"""
    print(f"\n📋 SUGGESTIONS DE DIAGNOSTIC")
    print("=" * 50)
    print("1. 🔍 Vérifiez les logs de l'API dans votre terminal")
    print("2. 🔧 Redémarrez l'API: Ctrl+C puis python scripts/start_api.py")
    print("3. 🧪 Testez l'API individuellement: curl http://127.0.0.1:8001/health")
    print("4. 📁 Vérifiez que le modèle local existe: models/coach-sportif-french/")
    print("5. 🌐 Testez la connectivité HuggingFace")

if __name__ == "__main__":
    test_api_endpoints()
    check_service_logs()