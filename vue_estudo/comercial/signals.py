"""
Signals para criar CompanyProfile e Subscription automaticamente.

Quando um novo usuário se registra, automaticamente:
1. CompanyProfile é criada
2. Subscription é criada com pago=True
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from decimal import Decimal

from .models import CompanyProfile, Subscription

User = get_user_model()


@receiver(post_save, sender=User)
def create_company_profile(sender, instance, created, **kwargs):
    """Criar CompanyProfile quando um novo usuário é criado."""
    if created:
        # Verificar se já existe
        if not hasattr(instance, 'company_profile'):
            CompanyProfile.objects.get_or_create(
                owner=instance,
                defaults={
                    'nome_empresa': f"Empresa de {instance.get_full_name() or instance.username}",
                }
            )


@receiver(post_save, sender=CompanyProfile)
def create_subscription(sender, instance, created, **kwargs):
    """Criar Subscription quando uma CompanyProfile é criada."""
    if created:
        Subscription.objects.get_or_create(
            company=instance,
            defaults={
                'pago': True,
                'valor_mensalidade': Decimal("0.00"),  # Pode alterar para um valor padrão
            }
        )
