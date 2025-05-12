from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from campaigns.models import Campaign
from subscribers.models import List
from django.http import JsonResponse

def home(request):
    """Home page view."""
    return render(request, 'core/home.html')

@login_required
def dashboard(request):
    """Dashboard view with user's campaigns and lists."""
    campaigns = Campaign.objects.filter(user=request.user).order_by('-created_at')
    lists = List.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'campaigns': campaigns,
        'lists': lists,
        'campaigns_count': campaigns.count(),
        'lists_count': lists.count(),
        'subscribers_count': sum(list.subscribers.count() for list in lists),
        'sent_emails_count': sum(campaign.sent_count for campaign in campaigns),
    }
    return render(request, 'core/dashboard.html', context)

def pricing(request):
    """Pricing page view."""
    return render(request, 'core/pricing.html')

def about(request):
    """About page view."""
    return render(request, 'core/about.html')

def contact(request):
    """Contact page view."""
    return render(request, 'core/contact.html')

def terms(request):
    """Terms page view."""
    return render(request, 'core/terms.html')

def privacy(request):
    """Privacy page view."""
    return render(request, 'core/privacy.html')

@login_required
def promo_verification(request):
    """Verify promotional tweet or blog post to remove ads."""
    if request.method == 'POST':
        promo_url = request.POST.get('promo_url')
        promo_type = request.POST.get('promo_type')
        
        # In a real app, you'd verify the URL contains proper promotion
        # For this MVP, we'll just accept any URL
        profile = request.user.profile
        profile.has_verified_promo = True
        profile.promo_url = promo_url
        profile.save()
        
        messages.success(request, _("Thank you for promoting DripEmails.org! Ads have been disabled for your account."))
        return redirect('dashboard')
    
    return render(request, 'core/promo_verification.html')