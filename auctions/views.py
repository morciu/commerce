from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.db.models import Max

from .models import User, AuctionListing, Bids, Comments


def index(request):
    return render(request, "auctions/index.html", {
        "active_listings": AuctionListing.objects.all()
        })


def auction(request, auction_id):
    auction = AuctionListing.objects.get(pk=auction_id)
    current_user = request.user
    if request.method == "POST":
        # Add to watch list button
        if "add_to_watchlist" in request.POST:
            #Check if user is using the watchlist button
            # Check if auction is already in watchlist
            if auction in current_user.watchlist.all():
                # Remove actuon from watchlist
                current_user.watchlist.remove(auction)
            else:
                # Add auction to watchlist
                current_user.watchlist.add(auction_id)
            return HttpResponseRedirect(reverse("auction", args=[auction_id]))

        # Submit Bid Button
        if "submit_bid" in request.POST:
            # Check if user is submiting a bid
            bid_ammount = float(request.POST["bid"])
            bids = auction.bid.all()
            price = auction.starting_bid
            if len(bids) == 0:
                if bid_ammount > price:
                    current_bid = Bids(auction=auction, bidder=current_user, ammount=bid_ammount)
                    current_bid.save()
                    auction.bid.add(current_bid)
                else:
                    return HttpResponseRedirect(reverse("error", args=["Your bid needs to be higher than the starting bid!"]))
            else:
                if bid_ammount > bids.aggregate(Max('ammount'))['ammount__max']:
                    current_bid = Bids(auction=auction, bidder=current_user, ammount=bid_ammount)
                    current_bid.save()
                    auction.bid.add(current_bid)
                else:
                    return HttpResponseRedirect(reverse("error", args=["Your need needs to be higher than the current highest bid!"]))
            return HttpResponseRedirect(reverse("auction", args=[auction_id]))

        #Submit Comment Form
        if "submit_comment" in request.POST:
            comment_text = request.POST["comment_field"]
            new_comment = Comments(user=current_user, text=comment_text, auction=auction)
            new_comment.save()
            auction.comment.add(new_comment)

            return HttpResponseRedirect(reverse("auction", args=[auction_id]))

        # Close Auction Button
        if "close_auction" in request.POST:
            auction.available = False
            auction.save()
            return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/auction.html", {
        "auction": auction,
        "current_user": current_user,
        })


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")


@login_required(login_url="login")
def create_listing(request):
    if request.method == "POST":
        # Get current logged in user and form inputs
        current_user = request.user
        title = request.POST["title"]
        description = request.POST["description"]
        starting_bid = float(request.POST["starting_bid"])

        #Check if optional forms have been filled in and create the auction object accordingly
        if request.POST["image_url"] and request.POST["category"]:
            image_url = request.POST["image_url"]
            category = request.POST["category"]
            auction = AuctionListing(title=title, description=description, image_url=image_url, category=category, starting_bid=starting_bid, seller=current_user)
        elif request.POST["image_url"]:
            image_url = request.POST["image_url"]
            auction = AuctionListing(title=title, description=description, image_url=image_url, starting_bid=starting_bid, seller=current_user)
        elif request.POST["category"]:
            category = request.POST["category"]
            auction = AuctionListing(title=title, description=description, category=category, starting_bid=starting_bid, seller=current_user)
        else:
            auction = AuctionListing(title=title, description=description, starting_bid=starting_bid, seller=current_user)
        auction.save()

        # Return to index page
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/create_listing.html")


def watchlist(request):
    current_user = request.user
    watchlist = current_user.watchlist.all()
    for i in watchlist:
        print(i.title)
    return render(request, "auctions/watchlist.html", {
        "watchlist": watchlist
        })


def error(request, message):
    return render(request, "auctions/error.html", {
        "message": message
        })


def categories(request):
    categories = []
    for auction in AuctionListing.objects.all():
        if auction.category:
            categories.append(auction.category)

    return render(request, "auctions/categories.html", {
        "categories": set(categories)
        })


def filtered(request, category):
    return render(request, "auctions/filtered.html", {
        "category": category,
        "auctions": AuctionListing.objects.filter(category=category, available=True)
        })