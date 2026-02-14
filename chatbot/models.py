from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
import uuid


class Conversation(models.Model):
    """Represents a chat session between a user and the chatbot"""
    
    class StatusChoices(models.TextChoices):
        ACTIVE = 'active', _('Active')
        COMPLETED = 'completed', _('Completed')
        ARCHIVED = 'archived', _('Archived')
    
    conversation_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='chatbot_conversations'
    )
    
    # Session info (for anonymous users)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.ACTIVE
    )
    
    # Context (stores conversation context as JSON)
    context = models.JSONField(default=dict, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    
    # User feedback
    is_satisfied = models.BooleanField(null=True, blank=True)
    feedback_comment = models.TextField(blank=True)
    
    class Meta:
        verbose_name = _("Conversation")
        verbose_name_plural = _("Conversations")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['conversation_id']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        user_info = self.user.email if self.user else f"Anonymous ({self.session_key[:8]})"
        return f"Chat #{self.conversation_id} - {user_info}"
    
    def get_message_count(self):
        """Get total message count"""
        return self.messages.count()
    
    def is_active(self):
        """Check if conversation is still active"""
        return self.status == self.StatusChoices.ACTIVE
    
    def end_conversation(self):
        """Mark conversation as completed"""
        from django.utils import timezone
        self.status = self.StatusChoices.COMPLETED
        self.ended_at = timezone.now()
        self.save(update_fields=['status', 'ended_at'])


class Message(models.Model):
    """Individual messages in a conversation"""
    
    class SenderChoices(models.TextChoices):
        USER = 'user', _('User')
        BOT = 'bot', _('Bot')
        SYSTEM = 'system', _('System')
    
    class MessageTypeChoices(models.TextChoices):
        TEXT = 'text', _('Text')
        QUICK_REPLY = 'quick_reply', _('Quick Reply')
        IMAGE = 'image', _('Image')
        BUTTON = 'button', _('Button')
        CAROUSEL = 'carousel', _('Carousel')
        LOCATION = 'location', _('Location')
    
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    
    # Message content
    message_type = models.CharField(
        max_length=20,
        choices=MessageTypeChoices.choices,
        default=MessageTypeChoices.TEXT
    )
    sender = models.CharField(
        max_length=10,
        choices=SenderChoices.choices
    )
    content = models.TextField()
    
    # Intent detection (what the user wants)
    intent = models.CharField(max_length=100, blank=True)
    confidence = models.FloatField(default=0.0)
    
    # Entities extracted from message
    entities = models.JSONField(default=dict, blank=True)
    
    # Quick reply / button data
    quick_replies = models.JSONField(default=list, blank=True)
    buttons = models.JSONField(default=list, blank=True)
    
    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Read status
    is_read = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = _("Message")
        verbose_name_plural = _("Messages")
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
        ]
    
    def __str__(self):
        sender_label = self.get_sender_display()
        content_preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"{sender_label}: {content_preview}"


class QuickReply(models.Model):
    """Predefined quick reply buttons for the chatbot"""
    
    # Trigger conditions
    intent = models.CharField(max_length=100, unique=True)
    triggers = models.JSONField(
        default=list,
        help_text=_("List of keywords that trigger this quick reply set")
    )
    
    # Response content
    title = models.CharField(max_length=200)
    replies = models.JSONField(
        default=list,
        help_text=_("List of quick reply options: [{'label': 'Text', 'payload': 'intent'}]")
    )
    
    # Order and status
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    # Language
    language = models.CharField(max_length=10, default='fr')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Quick Reply")
        verbose_name_plural = _("Quick Replies")
        ordering = ['order', 'intent']
    
    def __str__(self):
        return f"{self.intent} - {self.title}"


class FAQ(models.Model):
    """Frequently Asked Questions for the chatbot"""
    
    question = models.CharField(max_length=500)
    answer = models.TextField()
    
    # Category
    category = models.CharField(
        max_length=50,
        choices=[
            ('booking', _('Réservation')),
            ('payment', _('Paiement')),
            ('trip', _('Course')),
            ('account', _('Compte')),
            ('support', _('Support')),
            ('general', _('Général')),
        ],
        default='general'
    )
    
    # Keywords for matching
    keywords = models.JSONField(
        default=list,
        help_text=_("Keywords that trigger this FAQ")
    )
    
    # Intent
    intent = models.CharField(max_length=100, unique=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    
    # Usage stats
    view_count = models.IntegerField(default=0)
    helpful_count = models.IntegerField(default=0)
    not_helpful_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("FAQ")
        verbose_name_plural = _("FAQs")
        ordering = ['order', 'category']
    
    def __str__(self):
        return self.question[:50] + "..."
    
    def get_helpfulness_ratio(self):
        """Calculate percentage of helpful votes"""
        total = self.helpful_count + self.not_helpful_count
        if total == 0:
            return 0
        return (self.helpful_count / total) * 100


class ChatbotTraining(models.Model):
    """Training data for improving the chatbot"""
    
    # Training examples
    user_message = models.TextField()
    correct_intent = models.CharField(max_length=100)
    correct_entities = models.JSONField(default=dict, blank=True)
    
    # Status
    is_verified = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    
    # Metadata
    language = models.CharField(max_length=10, default='fr')
    source = models.CharField(
        max_length=50,
        choices=[
            ('manual', _('Manual Entry')),
            ('feedback', _('From Feedback')),
            ('auto', _('Auto-generated')),
        ],
        default='manual'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _("Chatbot Training Data")
        verbose_name_plural = _("Chatbot Training Data")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user_message[:30]}... -> {self.correct_intent}"

