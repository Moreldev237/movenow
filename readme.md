# MoveNow

Solution numérique innovante pour améliorer l'expérience des transports urbains locaux (motos et taxis) au Cameroun.

## Fonctionnalités

- **Commander un taxi/moto** en quelques clics
- **Géolocalisation en temps réel** avec Mapbox
- **Suivre son trajet** et partager sa position
- **Paiement mobile** (Mobile Money, Orange Money, cartes bancaires)
- **Vérification des conducteurs** (profils vérifiés et notation)
- **Gestion de flotte** dashboard pour propriétaires
- **Covoiturage optimisé** pour réduire les coûts

## Technologies

- **Frontend**: HTML, CSS, JavaScript, Tailwind CSS
- **Backend**: Django REST Framework
- **Base de données**: SQLite (développement), PostgreSQL (production)
- **Cartographie**: Mapbox GL JS

## Installation

### Backend
```bash
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver