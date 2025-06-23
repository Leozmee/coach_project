# scripts/test_api.py - Test complet de l'API Fitness Coach

import requests
import json
import time
from datetime import datetime
import sys

class APITester:
    """Testeur automatique pour l'API Fitness Coach"""
    
    def __init__(self, base_url="http://127.0.0.1:8001"):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "errors": []
        }
    
    def print_header(self, title):
        """Affiche un titre de section"""
        print(f"\n{'='*60}")
        print(f"🧪 {title}")
        print(f"{'='*60}")
    
    def print_test(self, method, endpoint, description):
        """Affiche le test en cours"""
        print(f"\n🔍 {method.upper()} {endpoint}")
        print(f"   📝 {description}")
    
    def print_result(self, success, response_data, elapsed_time):
        """Affiche le résultat d'un test"""
        self.results["total_tests"] += 1
        
        if success:
            self.results["passed"] += 1
            print(f"   ✅ SUCCÈS ({elapsed_time:.3f}s)")
            if isinstance(response_data, dict):
                # Afficher quelques champs clés
                if "message" in response_data:
                    print(f"      💬 {response_data['message']}")
                if "status" in response_data:
                    print(f"      📊 Status: {response_data['status']}")
                if "response" in response_data:
                    preview = response_data['response'][:100] + "..." if len(response_data['response']) > 100 else response_data['response']
                    print(f"      💭 Réponse: {preview}")
        else:
            self.results["failed"] += 1
            print(f"   ❌ ÉCHEC ({elapsed_time:.3f}s)")
            print(f"      🚨 Erreur: {response_data}")
    
    def test_request(self, method, endpoint, description, data=None, expected_status=200):
        """Teste une requête HTTP"""
        self.print_test(method, endpoint, description)
        
        try:
            start_time = time.time()
            
            if method.upper() == "GET":
                response = self.session.get(f"{self.base_url}{endpoint}")
            elif method.upper() == "POST":
                response = self.session.post(
                    f"{self.base_url}{endpoint}",
                    json=data,
                    headers={'Content-Type': 'application/json'}
                )
            else:
                raise ValueError(f"Méthode non supportée: {method}")
            
            elapsed_time = time.time() - start_time
            
            if response.status_code == expected_status:
                try:
                    response_data = response.json()
                    self.print_result(True, response_data, elapsed_time)
                    return response_data
                except json.JSONDecodeError:
                    self.print_result(True, response.text, elapsed_time)
                    return response.text
            else:
                error_msg = f"Status {response.status_code} (attendu {expected_status})"
                try:
                    error_data = response.json()
                    error_msg += f" - {error_data}"
                except:
                    error_msg += f" - {response.text}"
                self.print_result(False, error_msg, elapsed_time)
                self.results["errors"].append(f"{method} {endpoint}: {error_msg}")
                return None
                
        except Exception as e:
            elapsed_time = time.time() - start_time
            error_msg = f"Exception: {str(e)}"
            self.print_result(False, error_msg, elapsed_time)
            self.results["errors"].append(f"{method} {endpoint}: {error_msg}")
            return None
    
    def run_all_tests(self):
        """Lance tous les tests"""
        self.print_header("TEST COMPLET API COACH FITNESS")
        print(f"🎯 URL de base: {self.base_url}")
        print(f"⏰ Début des tests: {datetime.now().strftime('%H:%M:%S')}")
        
        # Test 1: Page d'accueil
        self.print_header("TESTS DE BASE")
        self.test_request("GET", "/", "Page d'accueil de l'API")
        
        # Test 2: Health check
        self.test_request("GET", "/health", "Vérification santé de l'API")
        
        # Test 3: Documentation
        self.test_request("GET", "/docs", "Documentation OpenAPI", expected_status=200)
        
        # Test 4: Chat simple
        self.print_header("TESTS CHAT")
        chat_data = {
            "message": "Comment faire des pompes ?"
        }
        self.test_request("POST", "/chat", "Chat simple sans profil", chat_data)
        
        # Test 5: Chat avec données complexes
        chat_complex = {
            "message": "Quel programme pour débuter la musculation ?",
            "user_data": {
                "age": 25,
                "level": "débutant"
            }
        }
        self.test_request("POST", "/chat", "Chat avec données utilisateur", chat_complex)
        
        # Test 6: Chat avec message vide
        chat_empty = {"message": ""}
        self.test_request("POST", "/chat", "Chat avec message vide", chat_empty)
        
        # Test 7: Chat avec message très long
        long_message = "Comment " + "très " * 50 + "long message de test"
        chat_long = {"message": long_message}
        self.test_request("POST", "/chat", "Chat avec message très long", chat_long)
        
        # Tests d'erreur
        self.print_header("TESTS D'ERREUR")
        
        # Test 8: Endpoint inexistant
        self.test_request("GET", "/inexistant", "Endpoint inexistant", expected_status=404)
        
        # Test 9: Méthode incorrecte
        self.test_request("GET", "/chat", "Méthode GET sur endpoint POST", expected_status=405)
        
        # Test 10: JSON malformé
        try:
            response = self.session.post(
                f"{self.base_url}/chat",
                data="json malformé",
                headers={'Content-Type': 'application/json'}
            )
            self.print_test("POST", "/chat", "JSON malformé")
            if response.status_code in [400, 422]:
                self.print_result(True, f"Erreur correctement gérée: {response.status_code}", 0.1)
                self.results["passed"] += 1
            else:
                self.print_result(False, f"Status inattendu: {response.status_code}", 0.1)
                self.results["failed"] += 1
            self.results["total_tests"] += 1
        except Exception as e:
            self.print_test("POST", "/chat", "JSON malformé")
            self.print_result(False, str(e), 0.1)
            self.results["total_tests"] += 1
        
        # Tests de performance
        self.print_header("TESTS DE PERFORMANCE")
        
        # Test 11: Mesure temps de réponse
        start_perf = time.time()
        responses = []
        for i in range(5):
            data = {"message": f"Test performance {i+1}"}
            result = self.test_request("POST", "/chat", f"Test perf #{i+1}", data)
            if result:
                responses.append(result)
        
        avg_time = (time.time() - start_perf) / 5
        print(f"\n📊 Performance moyenne: {avg_time:.3f}s par requête")
        
        # Résumé final
        self.print_summary()
    
    def print_summary(self):
        """Affiche le résumé des tests"""
        self.print_header("RÉSUMÉ DES TESTS")
        
        total = self.results["total_tests"]
        passed = self.results["passed"]
        failed = self.results["failed"]
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"📊 STATISTIQUES:")
        print(f"   Total tests: {total}")
        print(f"   ✅ Réussis: {passed}")
        print(f"   ❌ Échoués: {failed}")
        print(f"   📈 Taux de réussite: {success_rate:.1f}%")
        
        if self.results["errors"]:
            print(f"\n🚨 ERREURS DÉTECTÉES:")
            for error in self.results["errors"]:
                print(f"   - {error}")
        
        if success_rate >= 80:
            print(f"\n🎉 API EN BONNE SANTÉ ! ({success_rate:.1f}% de réussite)")
        elif success_rate >= 60:
            print(f"\n⚠️ API partiellement fonctionnelle ({success_rate:.1f}% de réussite)")
        else:
            print(f"\n🚨 API EN DIFFICULTÉ ! ({success_rate:.1f}% de réussite)")
        
        print(f"\n⏰ Tests terminés: {datetime.now().strftime('%H:%M:%S')}")

def main():
    """Point d'entrée principal"""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://127.0.0.1:8001"
    
    print("🧪 TESTEUR AUTOMATIQUE API COACH FITNESS")
    print(f"🎯 Cible: {base_url}")
    
    # Vérifier que l'API est accessible
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ API accessible, lancement des tests...")
        else:
            print(f"⚠️ API répond mais erreur {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ API non accessible ! Vérifiez qu'elle est démarrée.")
        print("💡 Lancez: python scripts/start_api.py")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erreur connexion: {e}")
        sys.exit(1)
    
    # Lancer les tests
    tester = APITester(base_url)
    tester.run_all_tests()

if __name__ == "__main__":
    main()