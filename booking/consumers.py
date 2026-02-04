import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.gis.geos import Point
from core.models import Trip, Driver

class TripTrackingConsumer(AsyncWebsocketConsumer):
    """Consumer WebSocket pour le suivi des courses"""
    
    async def connect(self):
        self.trip_id = self.scope['url_route']['kwargs']['trip_id']
        self.room_group_name = f'trip_{self.trip_id}'
        
        # Vérifier l'authentification
        if self.scope['user'].is_anonymous:
            await self.close()
            return
        
        # Vérifier les permissions
        trip = await self.get_trip()
        if not trip:
            await self.close()
            return
        
        if not await self.has_permission(trip):
            await self.close()
            return
        
        # Rejoindre le groupe
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Envoyer l'état initial
        initial_data = await self.get_initial_data(trip)
        await self.send(text_data=json.dumps({
            'type': 'initial',
            'data': initial_data
        }))
    
    async def disconnect(self, close_code):
        # Quitter le groupe
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Recevoir des messages du client"""
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'location_update':
            # Mettre à jour la position
            lat = data['lat']
            lng = data['lng']
            
            await self.update_trip_location(lat, lng)
            
            # Diffuser la mise à jour
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'location_message',
                    'lat': lat,
                    'lng': lng,
                    'user_id': self.scope['user'].id,
                }
            )
        
        elif message_type == 'trip_status':
            # Mettre à jour le statut
            status = data['status']
            await self.update_trip_status(status)
            
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'status_message',
                    'status': status,
                    'user_id': self.scope['user'].id,
                }
            )
        
        elif message_type == 'message':
            # Message de chat
            message = data['message']
            
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'user_id': self.scope['user'].id,
                    'user_name': self.scope['user'].get_full_name(),
                }
            )
    
    async def location_message(self, event):
        """Envoyer la mise à jour de position aux clients"""
        await self.send(text_data=json.dumps({
            'type': 'location_update',
            'lat': event['lat'],
            'lng': event['lng'],
            'user_id': event['user_id'],
        }))
    
    async def status_message(self, event):
        """Envoyer la mise à jour de statut aux clients"""
        await self.send(text_data=json.dumps({
            'type': 'status_update',
            'status': event['status'],
            'user_id': event['user_id'],
        }))
    
    async def chat_message(self, event):
        """Envoyer le message de chat aux clients"""
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'user_id': event['user_id'],
            'user_name': event['user_name'],
            'timestamp': event.get('timestamp'),
        }))
    
    @database_sync_to_async
    def get_trip(self):
        """Récupérer la course"""
        try:
            return Trip.objects.get(id=self.trip_id)
        except Trip.DoesNotExist:
            return None
    
    @database_sync_to_async
    def has_permission(self, trip):
        """Vérifier les permissions"""
        user = self.scope['user']
        return (
            user == trip.passenger or
            (user.is_driver and user.driver_profile == trip.driver)
        )
    
    @database_sync_to_async
    def get_initial_data(self, trip):
        """Récupérer les données initiales"""
        tracking_data = {
            'trip_id': trip.id,
            'status': trip.status,
            'pickup': {
                'address': trip.pickup_address,
                'lat': trip.pickup_location.y,
                'lng': trip.pickup_location.x,
            },
            'dropoff': {
                'address': trip.dropoff_address,
                'lat': trip.dropoff_location.y,
                'lng': trip.dropoff_location.x,
            },
            'current_location': None,
            'driver': None,
            'passenger': None,
        }
        
        if trip.current_location:
            tracking_data['current_location'] = {
                'lat': trip.current_location.y,
                'lng': trip.current_location.x,
            }
        
        if trip.driver:
            tracking_data['driver'] = {
                'id': trip.driver.id,
                'name': trip.driver.user.get_full_name(),
                'rating': trip.driver.rating,
                'vehicle': {
                    'plate': trip.driver.vehicle_plate,
                    'model': trip.driver.vehicle_model,
                    'color': trip.driver.vehicle_color,
                }
            }
        
        if trip.passenger:
            tracking_data['passenger'] = {
                'id': trip.passenger.id,
                'name': trip.passenger.get_full_name(),
            }
        
        return tracking_data
    
    @database_sync_to_async
    def update_trip_location(self, lat, lng):
        """Mettre à jour la position de la course"""
        try:
            trip = Trip.objects.get(id=self.trip_id)
            
            # Vérifier que c'est le chauffeur qui met à jour
            if self.scope['user'].is_driver and self.scope['user'].driver_profile == trip.driver:
                trip.current_location = Point(lng, lat)
                trip.save(update_fields=['current_location'])
                
                # Mettre à jour aussi la position du chauffeur
                trip.driver.update_location(lat, lng)
        except Trip.DoesNotExist:
            pass
    
    @database_sync_to_async
    def update_trip_status(self, status):
        """Mettre à jour le statut de la course"""
        try:
            trip = Trip.objects.get(id=self.trip_id)
            
            # Vérifier les permissions
            user = self.scope['user']
            if (
                (user == trip.passenger and status in ['cancelled']) or
                (user.is_driver and user.driver_profile == trip.driver and 
                 status in ['arrived', 'started', 'completed'])
            ):
                trip.status = status
                trip.save()
        except Trip.DoesNotExist:
            pass

class DriverLocationConsumer(AsyncWebsocketConsumer):
    """Consumer WebSocket pour la position des chauffeurs"""
    
    async def connect(self):
        if self.scope['user'].is_anonymous or not self.scope['user'].is_driver:
            await self.close()
            return
        
        self.driver_id = self.scope['user'].driver_profile.id
        self.room_group_name = f'driver_{self.driver_id}'
        
        # Rejoindre le groupe personnel
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        # Rejoindre le groupe des chauffeurs disponibles
        if self.scope['user'].driver_profile.is_available:
            await self.channel_layer.group_add(
                'available_drivers',
                self.channel_name
            )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        # Quitter les groupes
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        await self.channel_layer.group_discard(
            'available_drivers',
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Recevoir des messages du chauffeur"""
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'location_update':
            # Mettre à jour la position
            lat = data['lat']
            lng = data['lng']
            
            await self.update_driver_location(lat, lng)
            
            # Diffuser aux clients concernés
            await self.broadcast_location(lat, lng)
        
        elif message_type == 'availability_update':
            # Mettre à jour la disponibilité
            available = data['available']
            await self.update_driver_availability(available)
            
            if available:
                await self.channel_layer.group_add(
                    'available_drivers',
                    self.channel_name
                )
            else:
                await self.channel_layer.group_discard(
                    'available_drivers',
                    self.channel_name
                )
        
        elif message_type == 'booking_request':
            # Traiter une demande de réservation
            booking_id = data['booking_id']
            response = data['response']  # accept ou reject
            
            result = await self.handle_booking_request(booking_id, response)
            await self.send(text_data=json.dumps({
                'type': 'booking_response',
                'result': result,
            }))
    
    async def booking_request(self, event):
        """Recevoir une demande de réservation"""
        await self.send(text_data=json.dumps({
            'type': 'booking_request',
            'booking': event['booking'],
            'passenger': event['passenger'],
            'estimated_fare': event['estimated_fare'],
            'pickup_address': event['pickup_address'],
            'distance': event['distance'],
        }))
    
    @database_sync_to_async
    def update_driver_location(self, lat, lng):
        """Mettre à jour la position du chauffeur"""
        driver = self.scope['user'].driver_profile
        driver.update_location(lat, lng)
    
    @database_sync_to_async
    def update_driver_availability(self, available):
        """Mettre à jour la disponibilité du chauffeur"""
        driver = self.scope['user'].driver_profile
        driver.is_available = available
        driver.save(update_fields=['is_available'])
    
    @database_sync_to_async
    def handle_booking_request(self, booking_id, response):
        """Traiter une demande de réservation"""
        from booking.models import BookingRequest
        
        try:
            booking_request = BookingRequest.objects.get(
                id=booking_id,
                driver=self.scope['user'].driver_profile,
                status='sent'
            )
            
            if response == 'accept':
                return booking_request.accept()
            elif response == 'reject':
                return booking_request.reject()
            
            return False
        
        except BookingRequest.DoesNotExist:
            return False
    
    async def broadcast_location(self, lat, lng):
        """Diffuser la position aux clients concernés"""
        # Cette méthode serait appelée pour informer les passagers
        # en attente d'un chauffeur à proximité
        pass