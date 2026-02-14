"""
NLP Engine for MoveNow Chatbot - Intent recognition and entity extraction
"""

import re
from typing import Dict, Tuple, Optional, Any
from dataclasses import dataclass, field


@dataclass
class Intent:
    """Detected user intent"""
    name: str
    confidence: float
    entities: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)


class NLPEngine:
    """French/English NLP engine for offline operation"""
    
    def __init__(self):
        self.language = 'fr'
        
        # Intent patterns
        self.intent_patterns = {
            'book_ride': [r'reserver|réserver|commander|book|taxi|ride'],
            'cancel_booking': [r'annuler|cancel|supprimer'],
            'track_driver': [r'où|ou|suivre|track|localiser|arriver|position'],
            'get_price': [r'prix|tarif|cout|couter|price|cost|fare|combien'],
            'trip_history': [r'historique|courses|past|mes'],
            'report_issue': [r'problème|probleme|plainte|issue|problem|report'],
            'create_account': [r'inscrire|inscription|créer|compte|sign up|register'],
            'become_driver': [r'chauffeur|driver|devenir|rejoindre|become'],
            'contact_support': [r'contact|parler|agent|humain|assistance|support|help'],
            'faq': [r'faq|aide|question|comment|pourquoi|help|how|why'],
            'greeting': [r'^bonjour|^salut|^coucou|^hello|^hi|^hey'],
            'goodbye': [r'au revoir|bye|à bientôt|goodbye|see you'],
            'thanks': [r'merci|thanks|thank you'],
            'payment': [r'paiement|payer|espèces|carte|mobile|payment|cash|card'],
        }
    
    def process(self, text: str, context: Optional[Dict] = None) -> Intent:
        """Process user input and return detected intent"""
        cleaned = self._clean(text)
        self._detect_lang(cleaned)
        entities = self._extract(cleaned)
        intent_name, confidence = self._recognize(cleaned, context)
        
        return Intent(
            name=intent_name,
            confidence=confidence,
            entities=entities,
            context=context or {}
        )
    
    def _clean(self, text: str) -> str:
        text = text.lower().strip()
        text = re.sub(r'\s+', ' ', text)
        return re.sub(r'[.!?]+$', '', text)
    
    def _detect_lang(self, text: str):
        french = ['bonjour', 'merci', 'oui', 'non', 'je', 'nous']
        english = ['hello', 'thanks', 'yes', 'no', 'i', 'we']
        f_count = sum(1 for w in french if w in text)
        e_count = sum(1 for w in english if w in text)
        self.language = 'fr' if f_count > e_count else 'en'
    
    def _extract(self, text: str) -> Dict:
        entities = {}
        if match := re.search(r'(à|a|au)\s+([A-Z][a-zéèêëàâäùûüôöîï]+)', text):
            entities['location'] = match.group(2)
        if re.search(r'moto|motorcycle', text):
            entities['vehicle_type'] = 'moto'
        elif re.search(r'voiture|car', text):
            entities['vehicle_type'] = 'voiture'
        elif re.search(r'vip|luxe|premium', text):
            entities['vehicle_type'] = 'vip'
        if match := re.search(r'(\+?237\s?\d{9})', text):
            entities['phone'] = match.group(1)
        return entities
    
    def _recognize(self, text: str, context: Optional[Dict]) -> Tuple[str, float]:
        scores = {}
        for intent, patterns in self.intent_patterns.items():
            score = sum(1 for p in patterns if re.search(p, text))
            if score > 0:
                scores[intent] = score
        
        if not scores:
            return 'unknown', 0.0
        
        best = max(scores, key=scores.get)
        confidence = min(scores[best] / 2.0, 1.0)
        return best, confidence


class ResponseGenerator:
    """Generate responses based on detected intents"""
    
    def __init__(self):
        self.language = 'fr'
        self.responses = {
            'fr': {
                'book_ride': ("Je peux vous aider à réserver! Quel est votre lieu de départ?", [
                    {'label': 'Voir les tarifs', 'payload': 'get_price'},
                ]),
                'get_price': ("Pour un tarif, donnez-moi votre départ et destination.", [
                    {'label': 'Aéroport', 'payload': 'airport'},
                    {'label': 'Centre ville', 'payload': 'city'},
                ]),
                'track_driver': ("Pour suivre votre chauffeur, donnez-moi votre numéro de course.", [
                    {'label': 'Mes courses', 'payload': 'trip_history'},
                ]),
                'cancel_booking': ("Voulez-vous vraiment annuler votre réservation?", [
                    {'label': 'Oui, annuler', 'payload': 'confirm_cancel'},
                    {'label': 'Non', 'payload': 'book_ride'},
                ]),
                'trip_history': ("Voir 'Mes courses' dans votre application.", [
                    {'label': 'Réserver', 'payload': 'book_ride'},
                ]),
                'become_driver': ("Pour devenir chauffeur, postulez via l'application!", [
                    {'label': 'Postuler', 'payload': 'driver_apply'},
                ]),
                'contact_support': ("Appelez-nous au +237 686 865 451 ou WhatsApp.", [
                    {'label': 'Appeler', 'payload': 'call'},
                ]),
                'greeting': ("Bonjour! Je suis l'assistant MoveNow. Comment puis-je aider?", [
                    {'label': 'Réserver', 'payload': 'book_ride'},
                    {'label': 'Tarifs', 'payload': 'get_price'},
                    {'label': 'Aide', 'payload': 'faq'},
                ]),
                'thanks': ("De rien! Autre chose?", [
                    {'label': 'Réserver', 'payload': 'book_ride'},
                ]),
                'goodbye': ("Au revoir! Bonne journée avec MoveNow! 👋", []),
                'unknown': ("Désolé, je n'ai pas compris. Choisissez une option:", [
                    {'label': 'Réserver', 'payload': 'book_ride'},
                    {'label': 'Tarifs', 'payload': 'get_price'},
                    {'label': 'Aide', 'payload': 'faq'},
                    {'label': 'Agent', 'payload': 'contact_support'},
                ]),
            },
            'en': {
                'book_ride': ("I can help you book! What's your pickup location?", [
                    {'label': 'View prices', 'payload': 'get_price'},
                ]),
                'get_price': ("To get a fare, give me your pickup and dropoff.", [
                    {'label': 'Airport', 'payload': 'airport'},
                    {'label': 'City center', 'payload': 'city'},
                ]),
                'track_driver': ("To track your driver, give me your trip number.", [
                    {'label': 'My trips', 'payload': 'trip_history'},
                ]),
                'contact_support': ("Call us at +237 686 865 451 or WhatsApp.", []),
                'greeting': ("Hello! I'm the MoveNow assistant. How can I help?", [
                    {'label': 'Book ride', 'payload': 'book_ride'},
                    {'label': 'Prices', 'payload': 'get_price'},
                ]),
                'thanks': ("You're welcome! Anything else?", [
                    {'label': 'Book ride', 'payload': 'book_ride'},
                ]),
                'goodbye': ("Goodbye! Have a great day! 👋", []),
                'unknown': ("Sorry, I didn't understand. Choose an option:", [
                    {'label': 'Book ride', 'payload': 'book_ride'},
                    {'label': 'Prices', 'payload': 'get_price'},
                    {'label': 'Help', 'payload': 'faq'},
                ]),
            }
        }
    
    def generate(self, intent: Intent, context: Dict = None) -> Dict:
        """Generate response based on intent"""
        lang = self.language
        templates = self.responses.get(lang, self.responses['fr'])
        
        if intent.name in templates:
            text, quick_replies = templates[intent.name]
        else:
            text, quick_replies = templates.get('unknown', self.responses['fr']['unknown'])
        
        return {
            'text': text,
            'quick_replies': quick_replies,
            'intent': intent.name,
            'confidence': intent.confidence
        }
    
    def set_language(self, lang: str):
        if lang in ['fr', 'en']:
            self.language = lang

