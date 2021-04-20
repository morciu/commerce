from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    watchlist = models.ManyToManyField('AuctionListing', blank=True, related_name="followers")


class AuctionListing(models.Model):
	title = models.CharField(max_length=64)
	description = models.CharField(max_length=200)
	image_url = models.URLField(max_length=200, null=True, blank=True)
	category = models.CharField(max_length=64, null=True, blank=True)
	starting_bid = models.FloatField()
	seller = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name="auction")
	available = models.BooleanField(default=True)

	def __str__(self):
		return f"{self.seller}: Selling {self.title} for {self.starting_bid}"


class Bids(models.Model):
	auction = models.ForeignKey(AuctionListing, on_delete=models.CASCADE, related_name="bid")
	bidder = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bid")
	ammount = models.FloatField()


class Comments(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name="comment")
	text = models.CharField(max_length=200)
	auction = models.ForeignKey(AuctionListing, on_delete=models.CASCADE, related_name="comment")