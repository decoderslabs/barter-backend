from django.contrib import admin
from admin_interface.admin import AdminSiteAdmin
from admin_interface.models import Theme

admin.site.__class__ = AdminSiteAdmin

# Customize admin site
admin.site.site_header = 'Barter Admin'
admin.site.site_title = 'Barter Administration'
admin.site.index_title = 'Welcome to Barter Admin Panel'

# Register all models from apps
from apps.users.admin import UserAdmin, SocialAccountAdmin, BrandProfileAdmin, CreatorProfileAdmin
from apps.offers.admin import OfferAdmin
from apps.proposals.admin import ProposalAdmin, ProposalCounterAdmin
from apps.deals.admin import DealAdmin, DeliveryAdmin, DealMessageAdmin, RevisionRequestAdmin
from apps.drops.admin import DropsCampaignAdmin, DropsApplicationAdmin
from apps.membership.admin import MembershipTaskAdmin, MembershipTaskSubmissionAdmin, CreatorMembershipAdmin
from apps.ratings.admin import RatingAdmin
from apps.notifications.admin import NotificationAdmin
from apps.payments.admin import PaymentAdmin, SubscriptionAdmin, WalletAdmin, WalletTransactionAdmin

admin.site.register(User, UserAdmin)
admin.site.register(SocialAccount, SocialAccountAdmin)
admin.site.register(BrandProfile, BrandProfileAdmin)
admin.site.register(CreatorProfile, CreatorProfileAdmin)
admin.site.register(Offer, OfferAdmin)
admin.site.register(Proposal, ProposalAdmin)
admin.site.register(ProposalCounter, ProposalCounterAdmin)
admin.site.register(Deal, DealAdmin)
admin.site.register(Delivery, DeliveryAdmin)
admin.site.register(DealMessage, DealMessageAdmin)
admin.site.register(RevisionRequest, RevisionRequestAdmin)
admin.site.register(DropsCampaign, DropsCampaignAdmin)
admin.site.register(DropsApplication, DropsApplicationAdmin)
admin.site.register(MembershipTask, MembershipTaskAdmin)
admin.site.register(MembershipTaskSubmission, MembershipTaskSubmissionAdmin)
admin.site.register(CreatorMembership, CreatorMembershipAdmin)
admin.site.register(Rating, RatingAdmin)
admin.site.register(Notification, NotificationAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
admin.site.register(Wallet, WalletAdmin)
admin.site.register(WalletTransaction, WalletTransactionAdmin)
